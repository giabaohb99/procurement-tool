from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import Supplier
from .schema import SupplierCreate, SupplierUpdate

FILTERABLE = ["code", "name", "tax_code", "supplier_type"]
ENTITY = "supplier"


def list_suppliers(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(Supplier.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def get_supplier(db: Session, sid: int) -> Supplier:
    obj = db.get(Supplier, sid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy nhà cung cấp")
    return obj


def create_supplier(db: Session, data: SupplierCreate, user_id: int) -> Supplier:
    if db.query(Supplier).filter(Supplier.code == data.code).first():
        raise HTTPException(400, "Mã NCC đã tồn tại")
    obj = Supplier(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "create")
    return obj


def update_supplier(db: Session, sid: int, data: SupplierUpdate, user_id: int) -> Supplier:
    obj = get_supplier(db, sid)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "update")
    return obj


def delete_supplier(db: Session, sid: int, user_id: int) -> None:
    obj = get_supplier(db, sid)
    db.delete(obj)
    db.commit()
    record(db, user_id, ENTITY, sid, "delete")
