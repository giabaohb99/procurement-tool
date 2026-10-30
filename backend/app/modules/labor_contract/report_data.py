"""Dữ liệu hàng cho báo cáo Hợp đồng lao động (duoc-CR-686, khóa 17) — tách khỏi
`report_service.py` để mỗi tệp dưới 200 dòng.

Hàng = mỗi HĐ (mang các CỜ trạng thái đã tính sẵn tại `as_of`) + mỗi nhân sự đang làm CHƯA TỪNG
có HĐ đã ký. Chỉ số của báo cáo là ĐẾM CỜ nên cộng được ở cả Tổng lẫn từng nhóm.

Số truy vấn CỐ ĐỊNH mỗi lần `load_rows` (không tăng theo số HĐ): HĐ trong phạm vi · HĐ cùng
người (nối tiếp + đếm HĐ có thời hạn) · hồ sơ nhân sự · nhân sự chưa có HĐ.

Luật "HĐ nối tiếp" và "người còn làm" dùng lại của `expiry_service` (cùng một nguồn với chuông
cảnh báo) — không chép lại. HĐ nối tiếp / số HĐ có thời hạn đọc KHÔNG qua phạm vi: chỉ dùng để
LOẠI hoặc ĐẾM, không lộ gì ra ngoài.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LABOR_CONTRACT_TYPE_LABELS
from app.core.labor_contract_codes import LaborContractStatus as S
from app.core.labor_contract_codes import LaborContractType as T
from app.core.scoping import not_deleted_cond
from app.modules.employee.model import Employee
from app.modules.employee.service import STATUS_RESIGNED

from .expiry_service import _has_successor
from .model import LaborContract

#  Cờ -> chỉ số của báo cáo (một nguồn cho cả `report_service` lẫn danh sách `/rows`).
FLAGS = ("active", "expiring_30", "expiring_60", "expiring_90", "probation_expiring_30",
         "overdue", "no_contract", "missing_scan", "second_fixed_term", "new_contracts", "terminated",
         "resigned_not_terminated")

_CONTRACT_COLS = (LaborContract.id, LaborContract.code, LaborContract.contract_no, LaborContract.employee_id,
                  LaborContract.company_id, LaborContract.department_id, LaborContract.contract_type,
                  LaborContract.status, LaborContract.start_date, LaborContract.end_date,
                  LaborContract.signed_file_id, LaborContract.base_salary, LaborContract.insurance_salary,
                  LaborContract.allowance, LaborContract.terminated_date)
_EMP_COLS = (Employee.id, Employee.code, Employee.full_name, Employee.is_active, Employee.status)


@dataclass(frozen=True)
class ContractRow:
    contract_id: int
    contract_code: str
    contract_type: int          # 0 = hàng "chưa có HĐ"
    employee_id: int
    employee_code: str
    employee_name: str
    company_id: int
    department_id: int
    start_date: date | None
    end_date: date | None
    days_left: int | None       # âm = đã quá hạn; None = không có ngày kết thúc
    base_salary: int
    insurance_salary: int
    allowance: int
    flags: frozenset[str]


def type_label(code: int) -> str:
    """Nhãn loại HĐ; mã lạ trong DB rơi về "Khác" thay vì ném lỗi 500."""
    try:
        return LABOR_CONTRACT_TYPE_LABELS[T(int(code))]
    except (ValueError, KeyError):
        return LABOR_CONTRACT_TYPE_LABELS[T.OTHER]


def is_working(emp) -> bool:
    """Cùng luật "người còn làm" của `expiry_service`: còn hoạt động và chưa nghỉ việc."""
    return bool(emp.is_active) and (emp.status or "") != STATUS_RESIGNED


def _contract_flags(c, emp, as_of: date, d_from: date, d_to: date, later: list,
                    fixed_signed: int) -> set[str]:
    flags: set[str] = set()
    working = emp is not None and is_working(emp)
    #  "Đã ký tại as_of": đang SIGNED, hoặc đã ký rồi bị chấm dứt SAU as_of (xem kỳ quá khứ).
    signed = c.status == int(S.SIGNED) or (
        c.status == int(S.TERMINATED) and c.terminated_date is not None and c.terminated_date > as_of)
    in_force = signed and c.start_date <= as_of and (c.end_date is None or c.end_date >= as_of)
    #  HĐ còn hiệu lực của người đã nghỉ không cần gia hạn: tách riêng cho Nhân sự dọn sổ.
    if in_force and emp is not None and not working:
        flags.add("resigned_not_terminated")
    active = in_force and working
    if active:
        flags.add("active")
        if not c.signed_file_id:
            flags.add("missing_scan")
        if c.contract_type == int(T.FIXED_TERM) and fixed_signed >= 2:
            flags.add("second_fixed_term")
        if (working and c.end_date is not None
                and not _has_successor(later, c.start_date, overdue=False)):
            left = (c.end_date - as_of).days
            for n in (30, 60, 90):
                if left <= n:
                    flags.add(f"expiring_{n}")
            if left <= 30 and c.contract_type == int(T.PROBATION):
                flags.add("probation_expiring_30")
    if (signed and working and c.end_date is not None and c.end_date < as_of
            and not _has_successor(later, c.start_date, overdue=True)):
        flags.add("overdue")
    if d_from <= c.start_date <= d_to:
        flags.add("new_contracts")           # chỉ nạp HĐ đã ký / chấm dứt, nên không có nháp / hủy
    if c.status == int(S.TERMINATED) and c.terminated_date and d_from <= c.terminated_date <= d_to:
        flags.add("terminated")
    return flags


def load_rows(db: Session, contracts_q, employees_q, d_from: date, d_to: date, today: date,
              company_id: int | None = None, department_id: int | None = None) -> list[ContractRow]:
    """`contracts_q` / `employees_q` PHẢI đã qua `apply_scope` (controller làm); các bộ lọc
    `company_id` / `department_id` chỉ THU HẸP thêm, đặt SAU phạm vi."""
    as_of = min(d_to, today)
    cq = contracts_q.filter(or_(
        LaborContract.status == int(S.SIGNED),
        and_(LaborContract.status == int(S.TERMINATED),
             or_(LaborContract.terminated_date.between(d_from, d_to),
                 LaborContract.terminated_date > as_of,
                 LaborContract.start_date.between(d_from, d_to)))))
    if company_id is not None:
        cq = cq.filter(LaborContract.company_id == company_id)
    if department_id is not None:
        cq = cq.filter(LaborContract.department_id == department_id)
    contracts = cq.with_entities(*_CONTRACT_COLS).all()   # chỉ cột cần, bỏ JSON `custom_values`

    emp_ids = {c.employee_id for c in contracts}
    employees = ({e.id: e for e in db.query(*_EMP_COLS).filter(Employee.id.in_(emp_ids)).all()}
                 if emp_ids else {})
    later: dict[int, list[tuple[date, int]]] = {}
    fixed_signed: dict[int, int] = {}
    if emp_ids:
        sib = db.query(LaborContract.employee_id, LaborContract.start_date, LaborContract.status,
                       LaborContract.contract_type).filter(
            LaborContract.employee_id.in_(emp_ids),
            LaborContract.status.in_((int(S.DRAFT), int(S.SIGNED), int(S.TERMINATED))))
        cond = not_deleted_cond(LaborContract)
        if cond is not None:
            sib = sib.filter(cond)
        for eid, start, status, ctype in sib.all():
            #  HĐ nối tiếp: chỉ nháp / đã ký (luật của `expiry_service`); HĐ đã chấm dứt KHÔNG vào đây.
            if int(status) != int(S.TERMINATED):
                later.setdefault(eid, []).append((start, int(status)))
            #  Bộ đếm riêng: HĐ có thời hạn đã ký (kể cả đã bị chấm dứt sau đó).
            if int(status) in (int(S.SIGNED), int(S.TERMINATED)) and int(ctype) == int(T.FIXED_TERM):
                fixed_signed[eid] = fixed_signed.get(eid, 0) + 1

    out: list[ContractRow] = []
    for c in contracts:
        emp = employees.get(c.employee_id)
        flags = _contract_flags(c, emp, as_of, d_from, d_to, later.get(c.employee_id, []),
                                fixed_signed.get(c.employee_id, 0))
        if not flags:
            continue
        out.append(ContractRow(
            contract_id=c.id, contract_code=c.contract_no or c.code, contract_type=int(c.contract_type),
            employee_id=c.employee_id, employee_code=(emp.code if emp else ""),
            employee_name=(emp.full_name if emp else ""), company_id=c.company_id or 0,
            department_id=c.department_id or 0, start_date=c.start_date, end_date=c.end_date,
            days_left=(c.end_date - as_of).days if c.end_date else None,
            base_salary=c.base_salary or 0, insurance_salary=c.insurance_salary or 0,
            allowance=c.allowance or 0, flags=frozenset(flags)))
    out.extend(_no_contract_rows(db, employees_q, as_of, company_id, department_id))
    return out


def _no_contract_rows(db: Session, employees_q, as_of: date, company_id, department_id) -> list[ContractRow]:
    """Nhân sự đang làm, vào làm không sau `as_of`, chưa từng có HĐ đã ký / chấm dứt bắt đầu ≤ `as_of`."""
    has_contract = db.query(LaborContract.employee_id).filter(
        LaborContract.status.in_((int(S.SIGNED), int(S.TERMINATED))),
        LaborContract.start_date <= as_of)
    cond = not_deleted_cond(LaborContract)
    if cond is not None:
        has_contract = has_contract.filter(cond)
    q = employees_q.filter(Employee.is_active == True,  # noqa: E712
                           Employee.status != STATUS_RESIGNED,
                           or_(Employee.hire_date.is_(None), Employee.hire_date <= as_of),
                           ~Employee.id.in_(has_contract.scalar_subquery()))
    if company_id is not None:
        q = q.filter(Employee.company_id == company_id)
    if department_id is not None:
        q = q.filter(Employee.department_id == department_id)
    return [ContractRow(
        contract_id=0, contract_code="", contract_type=0, employee_id=e.id, employee_code=e.code or "",
        employee_name=e.full_name or "", company_id=e.company_id or 0, department_id=e.department_id or 0,
        start_date=None, end_date=None, days_left=None, base_salary=0, insurance_salary=0, allowance=0,
        flags=frozenset({"no_contract"})) for e in q.with_entities(Employee.id, Employee.code, Employee.full_name, Employee.company_id,
                                 Employee.department_id).all()]

