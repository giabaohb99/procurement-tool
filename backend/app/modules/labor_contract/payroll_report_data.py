"""Dữ liệu hàng cho báo cáo A5 «Quỹ lương theo pháp nhân» (duoc-CR-688, khóa 21).

MỘT lần nạp cho mọi thứ (kỳ này, kỳ so sánh, xu hướng theo tháng): `load_records` lấy các HĐ đã ký /
đã chấm dứt có thể còn hiệu lực ở BẤT KỲ mốc nào trong khoảng cần xem, rồi `rows_at(records, mốc)` lọc
trong bộ nhớ — nên số truy vấn CỐ ĐỊNH (HĐ + nhân sự = 2), không tăng theo số HĐ hay số mốc.

Hàng tại mốc `t` = mỗi cặp (người, pháp nhân) MỘT HĐ: HĐ đã ký còn hiệu lực ở `t` (kể cả HĐ bị chấm dứt SAU
`t`), của người còn làm. Hai HĐ chồng nhau của cùng người ở CÙNG pháp nhân (dữ liệu sai) chỉ lấy HĐ bắt đầu
muộn hơn — không cộng đôi lương; người có HĐ còn hiệu lực ở HAI pháp nhân thì có hai hàng (lương hai nơi đều
là tiền thật, quỹ lương từng pháp nhân phải đủ). Vì vậy «số người hưởng lương» thực ra đếm HĐ.
Lương là lương THỎA THUẬN trên HĐ, không phải lương thực trả.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractStatus as S
from app.modules.employee.constants import job_category_of
from app.modules.employee.model import Employee
from app.modules.employee.service import STATUS_RESIGNED

from .model import LaborContract

_COLS = (LaborContract.id, LaborContract.employee_id, LaborContract.company_id, LaborContract.department_id,
         LaborContract.contract_type, LaborContract.status, LaborContract.start_date, LaborContract.end_date,
         LaborContract.terminated_date, LaborContract.base_salary, LaborContract.allowance,
         LaborContract.insurance_salary)
_EMP_COLS = (Employee.id, Employee.code, Employee.full_name, Employee.is_active, Employee.status,
             Employee.resign_date, Employee.position, Employee.job_level, Employee.education_level)


@dataclass(frozen=True)
class PayRecord:
    """Một HĐ + thông tin người, CHƯA lọc theo mốc."""
    contract_id: int
    employee_id: int
    employee_code: str
    employee_name: str
    company_id: int
    department_id: int
    position: str
    job_category: int
    contract_type: int
    start_date: date
    end_date: date | None
    signed: bool                  # False = đã chấm dứt
    terminated_date: date | None
    working_now: bool
    resign_date: date | None
    base_salary: int
    allowance: int
    insurance_salary: int


def load_records(db: Session, contracts_q, lo: date, hi: date, today: date,
                 company_id: int | None = None, department_id: int | None = None) -> list[PayRecord]:
    """`contracts_q` PHẢI đã qua `apply_scope`; `company_id` / `department_id` chỉ thu hẹp thêm.
    Lấy HĐ có thể còn hiệu lực ở một mốc nào đó trong [min(lo, hôm nay), hi]."""
    lo = min(lo, today)
    q = contracts_q.filter(
        LaborContract.status.in_((int(S.SIGNED), int(S.TERMINATED))),
        LaborContract.start_date <= hi,
        or_(LaborContract.end_date.is_(None), LaborContract.end_date >= lo),
        or_(LaborContract.status == int(S.SIGNED), LaborContract.terminated_date > lo))
    if company_id is not None:
        q = q.filter(LaborContract.company_id == company_id)
    if department_id is not None:
        q = q.filter(LaborContract.department_id == department_id)
    contracts = q.with_entities(*_COLS).all()
    ids = {c.employee_id for c in contracts}
    emps = ({e.id: e for e in db.query(*_EMP_COLS).filter(Employee.id.in_(ids)).all()} if ids else {})
    out = []
    for c in contracts:
        e = emps.get(c.employee_id)
        if e is None:
            continue        # HĐ mồ côi: không biết người còn làm hay không -> không tính vào quỹ lương
        out.append(PayRecord(
            contract_id=c.id, employee_id=c.employee_id, employee_code=e.code or "",
            employee_name=e.full_name or "", company_id=c.company_id or 0, department_id=c.department_id or 0,
            position=(e.position or "").strip(), job_category=job_category_of(e.job_level, e.education_level),
            contract_type=int(c.contract_type), start_date=c.start_date, end_date=c.end_date,
            signed=int(c.status) == int(S.SIGNED), terminated_date=c.terminated_date,
            working_now=bool(e.is_active) and (e.status or "") != STATUS_RESIGNED, resign_date=e.resign_date,
            base_salary=c.base_salary or 0, allowance=c.allowance or 0, insurance_salary=c.insurance_salary or 0))
    return out


def _in_force(r: PayRecord, t: date) -> bool:
    if r.start_date > t or (r.end_date is not None and r.end_date < t):
        return False
    return r.signed or (r.terminated_date is not None and r.terminated_date > t)


def _working_at(r: PayRecord, t: date) -> bool:
    """Còn làm ở mốc `t`: đang làm, hoặc đã nghỉ nhưng ngày nghỉ SAU `t` (xem tháng quá khứ)."""
    return r.working_now or (r.resign_date is not None and r.resign_date > t)


def rows_at(records: list[PayRecord], t: date) -> list[PayRecord]:
    """Mỗi cặp (người, pháp nhân) một HĐ còn hiệu lực tại `t` (HĐ bắt đầu muộn nhất, hòa thì id lớn nhất)."""
    best: dict[tuple[int, int], PayRecord] = {}
    for r in records:
        if not (_in_force(r, t) and _working_at(r, t)):
            continue
        cur = best.get((r.employee_id, r.company_id))
        if cur is None or (r.start_date, r.contract_id) > (cur.start_date, cur.contract_id):
            best[(r.employee_id, r.company_id)] = r
    return list(best.values())
