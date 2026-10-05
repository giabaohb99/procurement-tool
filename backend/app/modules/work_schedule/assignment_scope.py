"""Phạm vi `employee` cho dòng gán cấp NHÂN SỰ (bug M3): dòng cấp khác công khai, dòng cấp Nhân sự
chỉ thấy khi nhân sự đó nằm trong phạm vi `employee.read` của người gọi."""
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.scoping import get_scoped, scope_condition
from app.core.work_schedule_codes import WorkScheduleLevel
from app.modules.employee.model import Employee

from .model import WorkScheduleAssignment


def employee_scope_condition(db: Session, user, profile: dict):
    """Điều kiện lọc dòng gán cấp NHÂN SỰ theo phạm vi `employee.read` của người gọi.

    Dòng cấp Hệ thống/Pháp nhân/Phòng ban vẫn công khai (danh mục cấu hình); dòng cấp Nhân sự
    kèm họ tên + lịch của một người nên chỉ trả khi người đó nằm trong tầm (bug M3). Một truy
    vấn con duy nhất, không N+1. Trả `None` = không cần lọc (phạm vi `all`).
    """
    cond = scope_condition(Employee, "employee", user, profile, "read")
    if cond is None:
        return None
    visible = db.query(Employee.id).filter(cond).scalar_subquery()
    return or_(WorkScheduleAssignment.target_level != int(WorkScheduleLevel.EMPLOYEE),
               WorkScheduleAssignment.target_id.in_(visible))


def employee_row_visible(db: Session, user, profile: dict, obj: WorkScheduleAssignment) -> bool:
    """Một dòng có được phép thấy không (dòng cấp Nhân sự đòi nhân sự đó trong phạm vi)."""
    if obj.target_level != int(WorkScheduleLevel.EMPLOYEE):
        return True
    return get_scoped(db, Employee, "employee", obj.target_id, user, profile, "read") is not None
