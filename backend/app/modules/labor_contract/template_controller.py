"""API Mẫu hợp đồng lao động — `/api/labor-contract-templates`, khóa quyền `labor_contract_template`.

`/placeholders` PHẢI khai TRƯỚC `/{template_id}` (FastAPI dò theo thứ tự khai trong cùng router).
"""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_current_user, get_perm_profile, require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import error, success

from . import access, template_service, template_web_editor
from .docx_engine import TemplateRejected
from .file_response import DOCX_MIME, download_response
from .placeholder_catalog import PLACEHOLDERS
from .template_model import LaborContractTemplate
from .template_schema import TemplateContentIn, TemplateCreateIn, TemplateUpdate
from .template_serializer import serialize_templates

router = APIRouter(prefix="/api/labor-contract-templates", tags=["labor-contract-template"])
ENTITY = template_service.ENTITY


def _rejected(exc: TemplateRejected):
    """Mẫu bị từ chối → 422 phong bì lỗi, `details.unknown` = biến ngoài danh mục (FE hiện chip)."""
    return error(exc.message, code="validation_error", status_code=422, details={"unknown": exc.unknown})


def _one(db: Session, row: LaborContractTemplate) -> dict:
    return serialize_templates(db, [row])[0]


def _scoped(db, tid, user, profile, action):
    return access.get_or_404_scoped(db, LaborContractTemplate, ENTITY, tid, user, profile, action,
                                    "Không tìm thấy mẫu hợp đồng")


@router.get("/placeholders")
def list_placeholders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    profile = get_perm_profile(db, user)
    if not (access.has_perm(profile, ENTITY, "read") or access.has_perm(profile, "labor_contract", "create")):
        raise HTTPException(403, "Không có quyền xem danh mục biến của mẫu hợp đồng")
    return success([{"key": p.key, "label": p.label, "group": p.group, "example": p.example}
                    for p in PLACEHOLDERS])


@router.get("")
def list_templates(company_id: int | None = None, contract_type: int | None = None,
                   is_active: bool | None = None, q: str = "", pg: dict = Depends(pagination),
                   db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    profile = get_perm_profile(db, user)
    total, rows = template_service.list_templates(
        db, user, profile, company_id=company_id, contract_type=contract_type, is_active=is_active,
        q=q, offset=pg["offset"], limit=pg["limit"])
    return success({"total": total, "items": serialize_templates(db, rows)})


@router.get("/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    row = _scoped(db, template_id, user, get_perm_profile(db, user), "read")
    return success(_one(db, row))


@router.post("")
def create_template(file: UploadFile = File(...), name: str = Form(...), company_id: int = Form(...),
                    contract_type: int = Form(...), note: str = Form(""),
                    db: Session = Depends(get_db), user=Depends(require(ENTITY, "create"))):
    try:
        data = TemplateCreateIn(name=name, company_id=company_id, contract_type=contract_type, note=note)
    except ValidationError as exc:
        raise HTTPException(422, exc.errors()[0]["msg"].removeprefix("Value error, "))
    profile = get_perm_profile(db, user)
    try:
        row = template_service.create_template(db, user, profile, data, file.file, file.filename or "")
    except TemplateRejected as exc:
        return _rejected(exc)
    audit_record(db, user.id, ENTITY, row.id, "create", f"Tải mẫu hợp đồng «{row.name}»")
    return success(_one(db, row), "Đã tạo mẫu hợp đồng", 201)


@router.patch("/{template_id}")
def update_template(template_id: int, data: TemplateUpdate, db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "write"))):
    row = _scoped(db, template_id, user, get_perm_profile(db, user), "write")
    row = template_service.update_meta(db, user, row, data)
    audit_record(db, user.id, ENTITY, row.id, "update", f"Sửa mẫu hợp đồng «{row.name}»")
    return success(_one(db, row), "Đã cập nhật mẫu hợp đồng")


@router.put("/{template_id}/file")
def replace_template_file(template_id: int, file: UploadFile = File(...), db: Session = Depends(get_db),
                          user=Depends(require(ENTITY, "write"))):
    row = _scoped(db, template_id, user, get_perm_profile(db, user), "write")
    try:
        template_service.replace_file(db, user, row, file.file, file.filename or "")
    except TemplateRejected as exc:
        return _rejected(exc)
    db.refresh(row)
    audit_record(db, user.id, ENTITY, row.id, "update", f"Thay tệp mẫu hợp đồng «{row.name}»")
    return success(_one(db, row), "Đã thay tệp mẫu")


@router.get("/{template_id}/file")
def download_template_file(template_id: int, db: Session = Depends(get_db),
                           user=Depends(require(ENTITY, "read"))):
    row = _scoped(db, template_id, user, get_perm_profile(db, user), "read")
    return download_response(template_service.read_template_file(db, row),
                             row.original_filename or f"{row.name}.docx", DOCX_MIME)


@router.get("/{template_id}/content")
def get_template_content(template_id: int, db: Session = Depends(get_db),
                         user=Depends(require(ENTITY, "read"))):
    """duoc-CR-606 — tệp mẫu mở thành HTML + lề trái/phải, cho trang soạn trên web."""
    row = _scoped(db, template_id, user, get_perm_profile(db, user), "read")
    return success(template_web_editor.read_content(db, row))


@router.put("/{template_id}/content")
def save_template_content(template_id: int, data: TemplateContentIn, db: Session = Depends(get_db),
                          user=Depends(require(ENTITY, "write"))):
    """Lưu nội dung soạn trên web thành .docx — kiểm biến y như tải tệp lên."""
    row = _scoped(db, template_id, user, get_perm_profile(db, user), "write")
    try:
        template_web_editor.save_content(db, user, row, data)
    except TemplateRejected as exc:
        return _rejected(exc)
    db.refresh(row)
    audit_record(db, user.id, ENTITY, row.id, "update", f"Soạn lại mẫu hợp đồng «{row.name}» trên web")
    return success(_one(db, row), "Đã lưu nội dung mẫu")


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "delete"))):
    row = _scoped(db, template_id, user, get_perm_profile(db, user), "delete")
    name = row.name
    template_service.delete_template(db, row)
    audit_record(db, user.id, ENTITY, template_id, "delete", f"Xóa mẫu hợp đồng «{name}»")
    return success(None, "Đã xóa mẫu hợp đồng")
