from fastapi import HTTPException
from sqlalchemy.orm import Session

from .model import Department
from .schema import DepartmentCreate, DepartmentUpdate


def list_departments(db: Session, q: str | None, pg: dict):
    query = db.query(Department)
    if q:
        query = query.filter(Department.name.like(f"%{q}%"))
    total = query.count()
    items = query.order_by(Department.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def get_department(db: Session, did: int) -> Department:
    obj = db.get(Department, did)
    if not obj:
        raise HTTPException(404, "Không tìm thấy phòng ban")
    return obj


def create_department(db: Session, data: DepartmentCreate, user_id: int) -> Department:
    if not data.code:
        from app.core.utils import generate_code
        data.code = generate_code(db, Department, "PBA")
    elif db.query(Department).filter(Department.code == data.code).first():
        raise HTTPException(400, "Mã phòng ban đã tồn tại")

    obj = Department(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_department(db: Session, did: int, data: DepartmentUpdate, user_id: int) -> Department:
    obj = get_department(db, did)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    return obj


def delete_department(db: Session, did: int, user_id: int) -> None:
    obj = get_department(db, did)
    db.delete(obj)
    db.commit()
