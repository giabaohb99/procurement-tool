from fastapi import HTTPException
from sqlalchemy.orm import Session

from .model import Permission, Role
from .schema import PermissionUpdate, RoleCreate, RoleUpdate


def list_roles(db: Session):
    return db.query(Role).order_by(Role.id).all()


def get_role(db: Session, rid: int) -> Role:
    obj = db.get(Role, rid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy vai trò")
    return obj


def create_role(db: Session, data: RoleCreate, user_id: int) -> Role:
    if db.query(Role).filter(Role.code == data.code).first():
        raise HTTPException(400, "Mã vai trò đã tồn tại")
    obj = Role(code=data.code, name=data.name, description=data.description, created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_role(db: Session, rid: int, data: RoleUpdate, user_id: int) -> Role:
    obj = get_role(db, rid)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    return obj


def delete_role(db: Session, rid: int, user_id: int) -> None:
    obj = get_role(db, rid)
    if obj.code in ["ADMIN", "ADMINISTRATOR"]:
        raise HTTPException(400, "Không được xóa vai trò mặc định của hệ thống")
    db.query(Permission).filter(Permission.role_id == rid).delete()
    db.delete(obj)
    db.commit()


def get_permissions(db: Session, rid: int):
    get_role(db, rid)
    return db.query(Permission).filter(Permission.role_id == rid).all()


def set_permissions(db: Session, rid: int, data: PermissionUpdate, user_id: int):
    get_role(db, rid)
    db.query(Permission).filter(Permission.role_id == rid).delete()
    for item in data.permissions:
        db.add(Permission(role_id=rid, created_by=user_id, updated_by=user_id, **item.model_dump()))
    db.commit()
    return get_permissions(db, rid)
