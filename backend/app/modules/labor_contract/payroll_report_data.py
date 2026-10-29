"""Dữ liệu hàng cho báo cáo A5 «Quỹ lương theo pháp nhân» (duoc-CR-693, khóa 21).

Nguồn số = ô lương trên HỒ SƠ nhân sự (`Employee.salary_monthly` / `allowance_monthly`), KHÔNG đọc hợp đồng
lao động nữa (ký HĐ chỉ tự điền ô hồ sơ — xem `salary_sync.py`). Một truy vấn nhân sự duy nhất, số truy vấn
cố định. Số liệu là ẢNH CHỤP hiện tại (ô hồ sơ không có lịch sử): chỉ người đang làm (`is_active`, chưa «Đã nghỉ»).

⚠️ Hàng mang lương từng người chỉ sống trong bộ nhớ để cộng; không hàng nào được trả ra ngoài kèm số tiền.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.employee.constants import job_category_of
from app.modules.employee.model import Employee
from app.modules.employee.service import STATUS_RESIGNED

_COLS = (Employee.id, Employee.code, Employee.full_name, Employee.company_id, Employee.department_id,
         Employee.position, Employee.job_level, Employee.education_level,
         Employee.salary_monthly, Employee.allowance_monthly)


@dataclass(frozen=True)
class FundRow:
    """Một nhân sự đang làm + lương hồ sơ. `has_salary` = đã nhập lương hoặc phụ cấp (> 0)."""
    employee_id: int
    employee_code: str
    employee_name: str
    company_id: int
    department_id: int
    position: str
    job_category: int
    base_salary: int
    allowance: int
    has_salary: bool


def load_rows(db: Session, employees_q, company_id: int | None = None,
              department_id: int | None = None) -> list[FundRow]:
    """`employees_q` PHẢI đã qua `apply_scope(Employee, "employee")`; `company_id` / `department_id` chỉ thu hẹp thêm."""
    q = employees_q.filter(Employee.is_active.is_(True), Employee.status != STATUS_RESIGNED)
    if company_id is not None:
        q = q.filter(Employee.company_id == company_id)
    if department_id is not None:
        q = q.filter(Employee.department_id == department_id)
    out = []
    for e in q.with_entities(*_COLS).all():
        base, allow = int(e.salary_monthly or 0), int(e.allowance_monthly or 0)
        out.append(FundRow(
            employee_id=e.id, employee_code=e.code or "", employee_name=e.full_name or "",
            company_id=e.company_id or 0, department_id=e.department_id or 0, position=(e.position or "").strip(),
            job_category=job_category_of(e.job_level, e.education_level),
            base_salary=base, allowance=allow, has_salary=base > 0 or allow > 0))
    return out
