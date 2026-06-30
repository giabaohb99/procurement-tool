from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import Product
from .schema import ProductCreate, ProductUpdate

FILTERABLE = ["code", "name", "item_group", "unit"]
ENTITY = "product"


def list_products(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(Product.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def get_product(db: Session, pid: int) -> Product:
    obj = db.get(Product, pid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy sản phẩm")
    return obj


def create_product(db: Session, data: ProductCreate, user_id: int) -> Product:
    if db.query(Product).filter(Product.code == data.code).first():
        raise HTTPException(400, "Mã sản phẩm đã tồn tại")
    obj = Product(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "create")
    return obj


def update_product(db: Session, pid: int, data: ProductUpdate, user_id: int) -> Product:
    obj = get_product(db, pid)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "update")
    return obj


def delete_product(db: Session, pid: int, user_id: int) -> None:
    obj = get_product(db, pid)
    db.delete(obj)
    db.commit()
    record(db, user_id, ENTITY, pid, "delete")
