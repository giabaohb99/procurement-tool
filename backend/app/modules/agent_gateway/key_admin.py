"""PHÍA ERP của việc phát / thu hồi khóa kết nối AI HỘ người khác (ai-CR-212, K4 doc/erp/21 §5.3).

Bảng khóa nằm ở DB dịch vụ AI (`tab_agent_mcp_key`), còn ai được phát hộ cho ai thì tính ở ERP: entity
`ai_mcp_key_admin` (read · create · delete), phạm vi đặt trên HỒ SƠ NHÂN SỰ của CHỦ KHÓA (`SCOPE_FIELDS` = pháp nhân +
phòng ban + chính mình, như entity `employee`). Dịch vụ AI hỏi qua cổng B: «trong những người này / phòng này, người phát
được đụng tới ai» — rồi mới phát / liệt kê / thu hồi.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

ENTITY = "ai_mcp_key_admin"
MAX_PEOPLE = 2000


def people_in_scope(db: Session, admin, action: str, *, user_ids: list[int] | None = None, department_id: int = 0,
                    limit: int = MAX_PEOPLE) -> list[dict] | None:
    """Tài khoản ĐANG HOẠT ĐỘNG có hồ sơ nhân sự nằm trong phạm vi `action` của `admin`. None = không có quyền.

    Tài khoản chưa gắn nhân sự không có phòng ban để tính phạm vi → không bao giờ lọt vào (kể cả phạm vi «toàn hệ»)."""
    from app.core.auth import get_perm_profile, user_has_permission
    from app.core.scoping import apply_scope
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    if not user_has_permission(db, admin, ENTITY, action):
        return None
    q = (db.query(User.id, Employee.id, Employee.code, Employee.full_name, Employee.department_id, Employee.company_id)
         .join(Employee, Employee.id == User.employee_id).filter(User.is_active.is_(True), User.employee_id != 0))
    q = apply_scope(q, Employee, ENTITY, admin, get_perm_profile(db, admin), action=action)
    if user_ids is not None:
        ids = {int(i) for i in user_ids if i}
        if not ids:
            return []
        q = q.filter(User.id.in_(ids))
    if department_id:
        q = q.filter(Employee.department_id == int(department_id))
    rows = q.order_by(Employee.full_name, User.id).limit(max(1, min(int(limit), MAX_PEOPLE))).all()
    dept_ids = {r[4] for r in rows if r[4]}
    names = {d.id: d.name for d in db.query(Department.id, Department.name).filter(Department.id.in_(dept_ids))} \
        if dept_ids else {}
    return [{"user_id": int(uid), "employee_id": int(eid), "label": f"{name} ({code})" if code else (name or f"#{uid}"),
             "department_id": int(dept or 0), "department": names.get(dept, ""), "company_id": int(comp or 0)}
            for uid, eid, code, name, dept, comp in rows]


def notify(db: Session, user_ids: list[int], *, title: str, body: str, link: str, by_user_id: int = 0) -> int:
    """Chuông ERP cho từng người (không email, không Telegram — doc 21 §7.1)."""
    from app.modules.notification.model import Notification

    n = 0
    for uid in {int(i) for i in user_ids if i}:
        db.add(Notification(user_id=uid, title=title[:255], body=body, link=link[:500], created_by=int(by_user_id or 0)))
        n += 1
    if n:
        db.commit()
    return n
