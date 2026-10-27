"""Đếm hồ sơ THIẾU ngày cho ghi chú báo cáo Biến động nhân sự (tách khỏi
`report_headcount_events.py` để giữ tệp đó < 200 dòng)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.employee.model import Employee
from app.modules.employee.report_headcount_events import scoped_employee_query
from app.modules.employee.service import STATUS_RESIGNED


def missing_resign_count(db: Session, user, prof: dict, company_id: int | None = None,
                         department_id: int | None = None) -> int:
    """Hồ sơ đánh dấu Nghỉ việc nhưng THIẾU `resign_date`."""
    return scoped_employee_query(db, user, prof, company_id, department_id).filter(
        Employee.status == STATUS_RESIGNED, Employee.resign_date.is_(None)).count()


def missing_hire_count(db: Session, user, prof: dict, company_id: int | None = None,
                       department_id: int | None = None) -> int:
    """Hồ sơ ĐANG LÀM (chưa nghỉ việc) THIẾU `hire_date` — báo cáo đang lấy ngày TẠO hồ sơ thay."""
    return scoped_employee_query(db, user, prof, company_id, department_id).filter(
        Employee.status != STATUS_RESIGNED, Employee.hire_date.is_(None)).count()
