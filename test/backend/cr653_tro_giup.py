"""Dụng cụ dùng chung cho bài kiểm duoc-CR-653."""
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole


def mk_admin(db, code="NGUOI_THAO_TAC") -> int:
    """Một tài khoản QUẢN TRỊ HỆ THỐNG riêng làm người thao tác (không trùng tài khoản của `seed`)."""
    role = db.query(Role).filter(Role.code == "admin").first()
    if not role:
        role = Role(code="admin", name="Quản trị hệ thống")
        db.add(role)
        db.flush()
    u = User(email=code, password_hash="x", is_active=True)
    db.add(u)
    db.flush()
    db.add(UserRole(user_id=u.id, role_id=role.id))
    db.commit()
    return u.id
