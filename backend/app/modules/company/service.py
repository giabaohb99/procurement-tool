from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.utils import generate_code

from .model import Company
from .schema import CompanyCreate, CompanyUpdate

FILTERABLE = ["code", "name", "issue_code", "tax_code", "level", "is_active"]
ENTITY = "company"


def get_company_logo_map(db: Session, company_ids: list[int]) -> dict[int, str]:
    if not company_ids:
        return {}
    from app.modules.attachment.model import FileLink, StoredFile

    rows = (
        db.query(FileLink.entity_id, StoredFile.url)
        .join(StoredFile, StoredFile.id == FileLink.file_id)
        .filter(
            FileLink.entity == "company",
            FileLink.entity_id.in_(company_ids),
            FileLink.doc_type == "logo",
        )
        .order_by(FileLink.id.desc())
        .all()
    )
    res: dict[int, str] = {}
    for cid, url in rows:
        if cid not in res:
            res[cid] = url or ""
    return res


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
    if data.issue_code and db.query(Company).filter(Company.issue_code == data.issue_code).first():
        raise HTTPException(400, "Mã số hiệu pháp nhân đã tồn tại")
    obj = Company(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "create")
    return obj


def update_company(db: Session, cid: int, data: CompanyUpdate, user_id: int) -> Company:
    obj = get_company(db, cid)
    values = data.model_dump(exclude_unset=True)

    if "issue_code" in values:
        from app.modules.doc_catalog.issue_code_guard import ensure_company_issue_code_free
        ensure_company_issue_code_free(db, obj.issue_code, values["issue_code"])
        duplicate = (
            db.query(Company.id)
            .filter(Company.issue_code == values["issue_code"], Company.id != obj.id)
            .first()
        ) if values["issue_code"] else None
        if duplicate:
            raise HTTPException(400, "Mã số hiệu pháp nhân đã tồn tại")

    for key, value in values.items():
        setattr(obj, key, value)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    record(db, user_id, ENTITY, obj.id, "update")
    return obj


def delete_company(db: Session, cid: int, user_id: int):
    obj = get_company(db, cid)
    db.delete(obj)
    db.commit()
    record(db, user_id, ENTITY, cid, "delete")
