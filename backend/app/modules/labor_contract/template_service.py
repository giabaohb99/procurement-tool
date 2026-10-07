"""Nghiệp vụ Mẫu hợp đồng lao động: tải lên (kiểm 2 lớp), thay tệp, sửa, xóa, danh sách.

Thứ tự kiểm khi nhận tệp (đầu vào KHÔNG tin cậy): `guard_upload` (đuôi, dung lượng, tên) →
`inspect_template` (guard_upload KHÔNG nhìn nội dung .docx: zip bom, macro, biến lạ, cú pháp Jinja
ngoài `{{ biến }}`). Sai → `TemplateRejected` (controller đổi thành 422 kèm `unknown`).
"""
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.file_registry import direct_policy
from app.core.scoping import apply_scope
from app.core.upload_guard import guard_upload
from app.modules.company.model import Company

from . import access
from .docx_engine import inspect_template
from .file_response import (delete_files_after_commit, discard_new_file, load_bytes,
                            store_bytes)
from .model import LaborContract
from .template_model import LaborContractTemplate
from .template_schema import MAX_PLACEHOLDERS, TemplateCreateIn, TemplateUpdate

ENTITY = "labor_contract_template"
KIND = "labor_contract_template"
CATEGORY = "labor-contract-template"
OUT_OF_SCOPE = "Pháp nhân ngoài phạm vi của bạn"


def read_and_inspect(fileobj, filename: str) -> tuple[bytes, list[str]]:
    """guard_upload RỒI inspect_template. Ném HTTPException (400/422) hoặc TemplateRejected."""
    exts, max_mb = direct_policy(KIND)
    guard_upload(filename=filename, fileobj=fileobj, exts=exts, max_mb=max_mb)
    data = fileobj.read()
    placeholders = inspect_template(data)
    if len(placeholders) > MAX_PLACEHOLDERS:  # không xảy ra với danh mục hiện tại; lưới cho cột JSON
        raise HTTPException(422, "Mẫu dùng quá nhiều biến")
    return data, placeholders


def _active_company_or_400(db: Session, company_id: int) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(400, "Pháp nhân không tồn tại")
    if not company.is_active:
        raise HTTPException(400, f"Pháp nhân {company.name} đã ngừng hoạt động")
    return company


def _ensure_unique_name(db: Session, company_id: int, name: str, exclude_id: int | None = None) -> None:
    q = db.query(LaborContractTemplate.id).filter(
        LaborContractTemplate.company_id == company_id, LaborContractTemplate.name == name)
    if exclude_id:
        q = q.filter(LaborContractTemplate.id != exclude_id)
    if q.first():
        raise HTTPException(400, "Tên mẫu đã tồn tại trong pháp nhân này")


def list_templates(db: Session, user, profile: dict, *, company_id: int | None, contract_type: int | None,
                   is_active: bool | None, q: str, offset: int, limit: int):
    query = apply_scope(db.query(LaborContractTemplate), LaborContractTemplate, ENTITY, user, profile, "read")
    if company_id:
        query = query.filter(LaborContractTemplate.company_id == company_id)
    if contract_type:
        query = query.filter(LaborContractTemplate.contract_type == contract_type)
    if is_active is not None:
        query = query.filter(LaborContractTemplate.is_active == is_active)
    keyword = (q or "").strip()
    if keyword:
        like = f"%{keyword[:100].replace('%', '').replace('_', '')}%"
        query = query.filter(or_(LaborContractTemplate.name.like(like),
                                 LaborContractTemplate.original_filename.like(like)))
    total = query.count()
    rows = (query.order_by(LaborContractTemplate.company_id, LaborContractTemplate.contract_type,
                           LaborContractTemplate.name)
            .offset(offset).limit(limit).all())
    return total, rows


def create_template(db: Session, user, profile: dict, data: TemplateCreateIn, fileobj,
                    filename: str) -> LaborContractTemplate:
    #  Phạm vi TRƯỚC mọi kiểm tra tồn tại / trùng tên: ngoài phạm vi phải ra 403 như nhau, không để
    #  400 «pháp nhân không tồn tại» / «tên đã có» thành đường dò pháp nhân và tên mẫu của nơi khác.
    probe = LaborContractTemplate(company_id=data.company_id, contract_type=data.contract_type,
                                  name=f"_probe_{user.id}", created_by=user.id, updated_by=user.id)
    if not access.can_create_for(db, LaborContractTemplate, ENTITY, probe, user, profile):
        raise HTTPException(403, OUT_OF_SCOPE)
    _active_company_or_400(db, data.company_id)
    _ensure_unique_name(db, data.company_id, data.name)
    file_bytes, placeholders = read_and_inspect(fileobj, filename)

    row = LaborContractTemplate(
        company_id=data.company_id, contract_type=data.contract_type, name=data.name, note=data.note,
        original_filename=filename.strip(), placeholders=placeholders, is_active=True,
        created_by=user.id, updated_by=user.id)
    db.add(row)
    access.ensure_created_in_scope(db, LaborContractTemplate, ENTITY, row, user, profile, OUT_OF_SCOPE)
    sf = None
    try:
        sf = store_bytes(db, file_bytes, filename, KIND, CATEGORY, user.id)
        row.file_id = sf.id
        db.commit()
    except Exception:
        db.rollback()
        discard_new_file(sf)
        raise
    db.refresh(row)
    return row


def replace_file(db: Session, user, row: LaborContractTemplate, fileobj, filename: str) -> None:
    """Thay tệp: kiểm lại như lúc tải mới; commit tệp mới rồi MỚI xóa tệp cũ."""
    file_bytes, placeholders = read_and_inspect(fileobj, filename)
    swap_file(db, user, row, file_bytes, placeholders, filename)


def swap_file(db: Session, user, row: LaborContractTemplate, file_bytes: bytes, placeholders: list[str],
              filename: str) -> None:
    """Gắn tệp ĐÃ KIỂM vào mẫu — dùng chung cho «Thay tệp» và «Soạn trên web» (duoc-CR-606)."""
    old_id = row.file_id
    sf = None
    try:
        sf = store_bytes(db, file_bytes, filename, KIND, CATEGORY, user.id)
        row.file_id = sf.id
        row.original_filename = filename.strip()
        row.placeholders = placeholders
        row.updated_by = user.id
        db.commit()
    except Exception:
        db.rollback()
        discard_new_file(sf)
        raise
    delete_files_after_commit(db, old_id)


def update_meta(db: Session, user, row: LaborContractTemplate, data: TemplateUpdate) -> LaborContractTemplate:
    values = data.model_dump(exclude_unset=True)
    if values.get("name") is None:
        values.pop("name", None)
    for key in ("contract_type", "is_active", "note"):  # cột NOT NULL: bỏ null, không ghi đè bằng None
        if key in values and values[key] is None:
            values.pop(key)
    if "name" in values and values["name"] != row.name:
        _ensure_unique_name(db, row.company_id, values["name"], row.id)
    for key, value in values.items():
        setattr(row, key, value)
    row.updated_by = user.id
    db.commit()
    db.refresh(row)
    return row


def delete_template(db: Session, row: LaborContractTemplate) -> None:
    used = db.query(LaborContract.id).filter(LaborContract.template_id == row.id).count()
    if used:
        raise HTTPException(
            409, f"Mẫu đang được {used} hợp đồng tham chiếu — không xóa được, hãy chọn «Ngừng dùng».")
    file_id = row.file_id
    db.delete(row)
    db.commit()
    delete_files_after_commit(db, file_id)


def read_template_file(db: Session, row: LaborContractTemplate) -> bytes:
    return load_bytes(db, row.file_id)[1]
