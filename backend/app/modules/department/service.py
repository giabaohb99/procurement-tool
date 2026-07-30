from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .model import Department
from .schema import DepartmentCreate, DepartmentUpdate


def list_departments(db: Session, q: str | None, pg: dict, is_active: bool | None = None,
                     sort_by: str = "", sort_dir: str = "asc"):
    from app.core.base_controller import apply_sort
    query = db.query(Department)
    if q:
        # Tìm chung 1 ô: theo tên phòng ban HOẶC tên trưởng bộ phận (manager)
        from app.modules.employee.model import Employee
        query = query.outerjoin(Employee, Employee.id == Department.manager_id).filter(
            or_(Department.name.like(f"%{q}%"), Employee.full_name.like(f"%{q}%"))
        )
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)
    total = query.count()
    query = apply_sort(query, Department, sort_by, sort_dir, default=Department.id.desc())
    items = query.offset(pg["offset"]).limit(pg["limit"]).all()
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
