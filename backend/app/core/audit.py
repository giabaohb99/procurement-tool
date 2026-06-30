"""Ghi & đọc nhật ký thao tác (audit log) dùng chung."""
from sqlalchemy.orm import Session


def record(db: Session, user_id: int, entity: str, entity_id: int, action: str, message: str = ""):
    from app.modules.audit.model import AuditLog

    db.add(AuditLog(entity=entity, entity_id=entity_id, action=action, message=message,
                    created_by=user_id, updated_by=user_id))
    db.commit()


def resolve_actor(db: Session, user_id: int) -> str:
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    if not user_id:
        return "Hệ thống"
    user = db.get(User, user_id)
    if not user:
        return f"User #{user_id}"
    emp = db.get(Employee, user.employee_id) if user.employee_id else None
    return emp.full_name if emp else (user.email or f"User #{user_id}")
