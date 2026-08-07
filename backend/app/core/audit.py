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


def resolve_signature_by_employee(db: Session, employee_id: int) -> str:
    """URL ảnh chữ ký của một NHÂN SỰ (qua tài khoản đăng nhập gắn với nhân sự đó).
    Trả "" nếu nhân sự chưa có tài khoản hoặc tài khoản chưa tải chữ ký lên.
    Dùng cho phiếu in: chữ ký phải khớp đúng TÊN đang in, nên tra theo nhân sự chứ không theo
    người bấm nút."""
    from app.modules.user.model import User

    if not employee_id:
        return ""
    user = (db.query(User)
            .filter(User.employee_id == employee_id, User.is_active == True)  # noqa: E712
            .order_by(User.id).first())
    return (user.signature or "") if user else ""


def resolve_signature(db: Session, user_id: int) -> str:
    """URL ảnh chữ ký của một TÀI KHOẢN. Trả "" nếu chưa tải chữ ký lên."""
    from app.modules.user.model import User

    user = db.get(User, user_id) if user_id else None
    return (user.signature or "") if user else ""


def resolve_actor_profile(db: Session, user_id: int) -> dict:
    """Thông tin nhân sự của người dùng để in phiếu: họ tên, chức vụ, bộ phận, trưởng BP."""
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    out = {"name": resolve_actor(db, user_id), "position": "", "department": "", "manager": ""}
    user = db.get(User, user_id) if user_id else None
    emp = db.get(Employee, user.employee_id) if (user and user.employee_id) else None
    if not emp:
        return out
    out["position"] = emp.position or ""
    dept = db.get(Department, emp.department_id) if emp.department_id else None
    if dept:
        out["department"] = dept.name or ""
        out["manager"] = dept.manager_name or ""
    return out
