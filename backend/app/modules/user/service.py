from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import hash_password
from app.modules.employee.model import Employee

from .model import User, UserRole
from .schema import RoleAssign, UserProvision


def _role_ids(db: Session, user_id: int) -> list[int]:
    return [ur.role_id for ur in db.query(UserRole).filter(UserRole.user_id == user_id).all()]


def list_users(db: Session, pg: dict):
    query = db.query(User)
    total = query.count()
    items = query.order_by(User.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def provision_user(db: Session, data: UserProvision, actor_id: int) -> User:
    emp = db.get(Employee, data.employee_id)
    if not emp:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    if db.query(User).filter(User.employee_id == data.employee_id).first():
        raise HTTPException(400, "Nhân viên này đã có tài khoản")
    user = User(
        email=data.email or emp.email,
        employee_id=data.employee_id,
        password_hash=hash_password(data.password),
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    assign_roles(db, user.id, RoleAssign(role_ids=data.role_ids), actor_id)
    return user


def reset_password(db: Session, user_id: int, new_password: str, actor_id: int) -> None:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    user.password_hash = hash_password(new_password)
    user.updated_by = actor_id
    db.commit()


def assign_roles(db: Session, user_id: int, data: RoleAssign, actor_id: int) -> None:
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    for rid in data.role_ids:
        db.add(UserRole(user_id=user_id, role_id=rid, created_by=actor_id, updated_by=actor_id))
    db.commit()


def set_active(db: Session, user_id: int, active: bool, actor_id: int) -> None:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    user.is_active = active
    user.updated_by = actor_id
    db.commit()
