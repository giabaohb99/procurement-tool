from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.utils import generate_code

from .model import Company
from .schema import CompanyCreate, CompanyUpdate

FILTERABLE = ["code", "name", "tax_code", "is_active"]
ENTITY = "company"


def list_companies(db: Session, base_query, pg: dict):
    total = base_query.count()
    items = base_query.order_by(Company.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return total, items


def get_company(db: Session, cid: int) -> Company:
    obj = db.get(Company, cid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy công ty")
    return obj


def create_company(db: Session, data: CompanyCreate, user_id: int) -> Company:
    if not data.code:
        data.code = generate_code(db, Company, "CTY")
    elif db.query(Company).filter(Company.code == data.code).first():
        raise HTTPException(400, "Mã công ty đã tồn tại")
    obj = Company(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "create")
    return obj


def update_company(db: Session, cid: int, data: CompanyUpdate, user_id: int) -> Company:
    obj = get_company(db, cid)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "update")
    return obj


def delete_company(db: Session, cid: int, user_id: int) -> None:
    obj = get_company(db, cid)
    db.delete(obj)
    db.commit()
    record(db, user_id, ENTITY, cid, "delete")
