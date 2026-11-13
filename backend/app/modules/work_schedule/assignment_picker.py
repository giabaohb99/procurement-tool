"""Nguồn của ô chọn đối tượng khi gán lịch RIÊNG (duoc-CR-757 lượt 2): nhân sự mà người gọi gán được.

Hai chế độ, cùng khuôn với cửa quyền ở `assignment_access`:
* khóa Nhân sự `work_schedule.create` → nhân sự trong phạm vi `employee.read` (như `_ensure_employee_in_scope`);
* chỉ khóa Trưởng phòng `work_schedule_personal.create` → nhân sự trong phạm vi khóa đó (đã gồm ô "Phòng ban được xem"
  ràng công ty), trừ chính mình.
Chỉ người ĐANG LÀM. Từ khóa tìm không dấu trong bộ nhớ (cùng lý do `leave/balance_controller`: collation MySQL không gập
dấu tiếng Việt) — bảng nhân sự cỡ vài trăm dòng; số truy vấn cố định: một cho nhân sự, một cho tên phòng.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import user_has_permission
from app.core.scoping import apply_scope, get_perm_profile, scope_condition
from app.core.text_fold import fold
from app.modules.department.model import Department
from app.modules.employee.model import Employee

from .assignment_access import HR_ENTITY, PERSONAL_ENTITY, holds_hr_key


def list_assignable(db: Session, user, keyword: str | None, offset: int, limit: int) -> tuple[int, list[dict]]:
    """`(tổng, một trang)` nhân sự gán được; mỗi phần tử `{id, code, full_name, department_name}`."""
    profile = get_perm_profile(db, user)
    query = db.query(Employee.id, Employee.code, Employee.full_name, Employee.department_id).filter(
        Employee.is_active.is_(True))
    if holds_hr_key(db, user, "create"):
        query = apply_scope(query, Employee, "employee", user, profile)
    elif user_has_permission(db, user, PERSONAL_ENTITY, "create"):
        cond = scope_condition(Employee, PERSONAL_ENTITY, user, profile, "create")
        query = query if cond is None else query.filter(cond)
        own = profile.get("employee_id") or 0
        if own:
            query = query.filter(Employee.id != own)
    else:
        raise HTTPException(403, f"Không có quyền: create {HR_ENTITY}")
    rows = query.order_by(Employee.full_name, Employee.id).all()
    needle = fold((keyword or "").strip()[:100])
    if needle:
        rows = [r for r in rows if needle in fold(r.full_name or "") or needle in fold(r.code or "")]
    page = rows[offset:offset + limit]
    names = {d.id: d.name for d in db.query(Department.id, Department.name)
             .filter(Department.id.in_({r.department_id for r in page} or {0})).all()}
    return len(rows), [{"id": r.id, "code": r.code, "full_name": r.full_name,
                        "department_name": names.get(r.department_id, "")} for r in page]
