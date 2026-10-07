"""Gộp `TemplateOut` cho một DANH SÁCH — tên pháp nhân, người tạo, dung lượng tệp, số HĐ dùng mẫu:
mỗi loại MỘT truy vấn cho cả trang (`GROUP BY template_id`), không N+1."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.attachment.model import StoredFile
from app.modules.company.model import Company

from .lookup import user_names
from .model import LaborContract
from .template_model import LaborContractTemplate
from .template_schema import TemplateOut


def serialize_templates(db: Session, rows: list[LaborContractTemplate]) -> list[dict]:
    if not rows:
        return []
    ids = [r.id for r in rows]
    #  Lấy cả mã: có pháp nhân trùng tên, chỉ tên thì bảng mẫu không phân biệt được.
    company_ids = {r.company_id for r in rows if r.company_id}
    companies = {cid: (name, issue_code or code or "") for cid, name, issue_code, code in
                 db.query(Company.id, Company.name, Company.issue_code, Company.code)
                 .filter(Company.id.in_(company_ids)).all()} if company_ids else {}
    creators = user_names(db, {r.created_by for r in rows})
    file_ids = {r.file_id for r in rows if r.file_id}
    sizes = dict(db.query(StoredFile.id, StoredFile.size).filter(StoredFile.id.in_(file_ids)).all()) if file_ids else {}
    counts = dict(db.query(LaborContract.template_id, func.count(LaborContract.id))
                  .filter(LaborContract.template_id.in_(ids))
                  .group_by(LaborContract.template_id).all())
    return [TemplateOut(
        id=r.id, company_id=r.company_id, company_name=companies.get(r.company_id, ("", ""))[0],
        company_code=companies.get(r.company_id, ("", ""))[1],
        contract_type=r.contract_type, name=r.name, note=r.note or "",
        original_filename=r.original_filename or "", file_size=int(sizes.get(r.file_id, 0) or 0),
        placeholders=list(r.placeholders or []), is_active=bool(r.is_active),
        created_at=r.created_at, created_by_name=creators.get(r.created_by, ""),
        contract_count=int(counts.get(r.id, 0)),
    ).model_dump() for r in rows]
