"""Nạp hàng cho báo cáo H1 "Phúc lợi & sự kiện" (duoc-CR-688).

Người được tính = đang làm vào NGÀY DỊP: đã vào làm (`hire_date <= ngày`; thiếu `hire_date` thì lấy ngày TẠO
hồ sơ theo giờ VN như A2/A3, `BenefitRow.hire_estimated`) và (chưa nghỉ hoặc `resign_date > ngày`).
Người đã chuyển "Đã nghỉ" mà không ghi ngày nghỉ không xác định được -> không tính.
Số truy vấn CỐ ĐỊNH: nhân sự (2: có/không `hire_date`) · (con, khi lọc theo con) · (hợp đồng, khi có loại
trừ) · (đơn nghỉ + khoảng, khi bỏ người đang nghỉ) — mỗi truy vấn con thêm 1 lần cho mỗi 900 mã.
Ngày sinh chỉ được nạp khi bộ lọc cần và chỉ dùng để lọc — KHÔNG đi vào hàng trả ra.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractStatus as S
from app.core.report_period import to_local_date
from app.modules.leave.constants import LR_APPROVED
from app.modules.leave.period_spans import periods_by_request
from app.modules.leave.request_model import LeaveRequest
from app.modules.labor_contract.model import LaborContract

from .benefit_report_inputs import Filters, age_on
from .constants import JOB_LEVEL_DEPUTY_MANAGER, RELATION_DAUGHTER, RELATION_SON
from .contact_model import EmployeeFamily
from .model import Employee
from .report_headcount_events import as_of_filtered

_CHUNK = 900   # trần số mã trong một mệnh đề IN


def _chunks(ids: list[int]):
    for i in range(0, len(ids), _CHUNK):
        yield ids[i:i + _CHUNK]


@dataclass(frozen=True)
class BenefitRow:
    employee_id: int
    employee_code: str
    employee_name: str
    company_id: int
    department_id: int
    position_id: int
    position: str
    job_level: int
    is_manager: bool
    units: int          # 1 người, hoặc số con khi lọc theo con
    amount: int         # units × mức theo cấp (nhân viên / quản lý)
    hire_estimated: bool = False   # thiếu ngày vào làm -> lấy ngày tạo hồ sơ


def _on_leave_ids(db: Session, ids: list[int], day: date) -> set[int]:
    out: set[int] = set()
    for part in _chunks(ids):
        reqs = db.query(LeaveRequest.id, LeaveRequest.employee_id).filter(
            LeaveRequest.employee_id.in_(part), LeaveRequest.is_deleted.is_(False),
            LeaveRequest.status == LR_APPROVED, LeaveRequest.from_date <= day, LeaveRequest.to_date >= day).all()
        if not reqs:
            continue
        owner = {r.id: r.employee_id for r in reqs}
        out |= {owner[rid] for rid, ps in periods_by_request(db, owner).items()
                if any(p.from_date <= day <= p.to_date for p in ps)}
    return out


def _excluded_by_contract(db: Session, ids: list[int], day: date, types: tuple[int, ...]) -> set[int]:
    """Người có HĐ đã ký còn hiệu lực vào `day` (HĐ bắt đầu gần nhất) thuộc loại bị loại trừ."""
    latest: dict[int, int] = {}
    for part in _chunks(ids):
        for c in (db.query(LaborContract.employee_id, LaborContract.contract_type, LaborContract.status,
                           LaborContract.start_date, LaborContract.end_date, LaborContract.terminated_date)
                  .filter(LaborContract.employee_id.in_(part),
                          LaborContract.status.in_((int(S.SIGNED), int(S.TERMINATED))),
                          LaborContract.start_date <= day)
                  .order_by(LaborContract.start_date, LaborContract.id).all()):
            ended = c.status == int(S.TERMINATED) and (c.terminated_date is None or c.terminated_date <= day)
            if not ended and (c.end_date is None or c.end_date >= day):
                latest[c.employee_id] = c.contract_type
    return {eid for eid, t in latest.items() if int(t) in types}


def _children_count(db: Session, ids: list[int], day: date, max_age: int) -> dict[int, int]:
    out: dict[int, int] = {}
    for part in _chunks(ids):
        for f in db.query(EmployeeFamily.employee_id, EmployeeFamily.date_of_birth).filter(
                EmployeeFamily.employee_id.in_(part),
                EmployeeFamily.relation.in_((RELATION_SON, RELATION_DAUGHTER)),
                EmployeeFamily.date_of_birth.isnot(None), EmployeeFamily.date_of_birth <= day):
            if age_on(f.date_of_birth, day) <= max_age:
                out[f.employee_id] = out.get(f.employee_id, 0) + 1
    return out


def load_rows(db: Session, employees_q, day: date, flt: Filters) -> list[BenefitRow]:
    """`employees_q` PHẢI đã qua `apply_scope(Employee, 'employee')`; mọi bộ lọc chỉ thu hẹp thêm."""
    #  Đã vào làm ≤ `day` và còn làm tại `day`: hai nhánh có/không `hire_date` (nhánh sau lùi về `created_at`).
    with_date, fallback = as_of_filtered(employees_q, day)
    flt_cols = []
    for col, val in ((Employee.gender, flt.gender), (Employee.position_id, flt.position_id),
                     (Employee.company_id, flt.company_id), (Employee.department_id, flt.department_id)):
        if val is not None:
            flt_cols.append(col == val)
    if flt.job_level_min:
        flt_cols.append(Employee.job_level >= flt.job_level_min)
    cols = [Employee.id, Employee.code, Employee.full_name, Employee.company_id, Employee.department_id,
            Employee.position_id, Employee.position, Employee.job_level, Employee.hire_date,
            Employee.created_at]
    if flt.needs_dob:
        cols.append(Employee.date_of_birth)
    found = [(e, e.hire_date is None) for q in (with_date, fallback)
             for e in q.filter(*flt_cols).with_entities(*cols).all()]
    found.sort(key=lambda x: x[0].code or "")
    #  Ngày vào làm hiệu lực: thiếu `hire_date` -> ngày tạo hồ sơ theo giờ VN (khớp A2/A3).
    hired = {e.id: e.hire_date or to_local_date(e.created_at) for e, _ in found}
    estimated = {e.id for e, est in found if est}
    emps = [e for e, _ in found]

    def keep(e) -> bool:
        hd = hired[e.id]
        if flt.seniority_years and not (hd.month == day.month and day.year - hd.year in flt.seniority_years):
            return False
        if flt.needs_dob:
            dob = e.date_of_birth
            if dob is None:
                return False
            if flt.birth_month is not None and dob.month != flt.birth_month:
                return False
            age = age_on(dob, day)
            if (flt.age_min is not None and age < flt.age_min) or (flt.age_max is not None and age > flt.age_max):
                return False
        return True

    emps = [e for e in emps if keep(e)]
    ids = [e.id for e in emps]
    if not ids:
        return []
    drop: set[int] = set()
    if flt.exclude_contract_types:
        drop |= _excluded_by_contract(db, ids, day, flt.exclude_contract_types)
    if not flt.include_on_leave:
        drop |= _on_leave_ids(db, ids, day)
    children = _children_count(db, ids, day, flt.child_max_age) if flt.child_max_age is not None else None
    out = []
    for e in emps:
        if e.id in drop:
            continue
        units = 1 if children is None else children.get(e.id, 0)
        if not units:
            continue
        mgr = (e.job_level or 0) >= JOB_LEVEL_DEPUTY_MANAGER
        out.append(BenefitRow(e.id, e.code or "", e.full_name or "", e.company_id or 0, e.department_id or 0,
                              e.position_id or 0, e.position or "", e.job_level or 0, mgr, units,
                              units * (flt.amount_manager if mgr else flt.amount_staff),
                              e.id in estimated))
    return out
