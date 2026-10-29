"""«Chưa được cấp quỹ» (duoc-CR-686): nhân sự ĐANG LÀM, trong phạm vi + lọc, không có dòng quỹ
phép năm đó cho BẤT KỲ loại nghỉ nào tính quỹ (`LeaveType.counts_balance = True`).

Phạm vi lấy theo `apply_scope(Employee, "employee")` — người xem báo cáo quỹ phép mà không có
quyền đọc nhân sự sẽ thấy 0 (đóng, không mở). Người vào làm SAU hết năm đang xem không tính.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.balance_report_spec import employee_conds
from app.modules.leave.catalog_model import LeaveType


def missing_balance_query(db: Session, user, prof: dict, year: int, status: str,
                          company_id: int | None, department_id: int | None):
    """Query `Employee` thiếu quỹ năm `year`. `status == "resigned"` → luôn rỗng (chỉ số nói về
    người ĐANG LÀM, người đã nghỉ không cần quỹ)."""
    q = apply_scope(db.query(Employee), Employee, "employee", user, prof)
    if status == "resigned":
        return q.filter(Employee.id == -1)
    for cond in employee_conds("working", department_id):
        q = q.filter(cond)
    if company_id is not None:
        q = q.filter(Employee.company_id == company_id)
    year_end = date(year, 12, 31)
    has_balance = (db.query(LeaveBalance.employee_id)
                   .filter(LeaveBalance.year == year,
                           LeaveBalance.leave_type_id.in_(
                               db.query(LeaveType.id).filter(LeaveType.counts_balance.is_(True)))))
    return q.filter(~Employee.id.in_(has_balance),
                    (Employee.hire_date.is_(None)) | (Employee.hire_date <= year_end))


def count_missing_balance(db: Session, user, prof: dict, year: int, status: str,
                          company_id: int | None, department_id: int | None) -> int:
    return missing_balance_query(db, user, prof, year, status, company_id, department_id).count()
