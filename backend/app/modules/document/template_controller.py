"""API thư viện văn bản mẫu.

Mẫu nằm trong trang Thiết lập văn bản nên dùng chung quyền của `doc_type`.
Người được tạo văn bản vốn đã cần quyền đọc danh mục loại để đổ ô chọn, vì vậy
họ cũng đọc được các mẫu đang dùng mà không cần thêm một entity quyền mới.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.base_controller import apply_filters, apply_sort, pagination
from app.core.database import get_db
from app.core.response import success
from app.modules.doc_catalog.model import DocType

from . import template_service
from .template_model import DocumentTemplate
from .template_schema import (DocumentTemplateCreate,
                              DocumentTemplateDetailOut,
                              DocumentTemplateListOut,
                              DocumentTemplateUpdate)

router = APIRouter(prefix="/api/document-templates", tags=["document_template"])


def _serialize(db: Session, template: DocumentTemplate, *, detail: bool) -> dict:
    schema = DocumentTemplateDetailOut if detail else DocumentTemplateListOut
    payload = schema.model_validate(template).model_dump()
    doc_type = db.get(DocType, template.doc_type_id)
    payload["doc_type_name"] = doc_type.name if doc_type else ""
    payload["doc_type_code"] = doc_type.code if doc_type else ""
    return payload


@router.get("")
def list_templates(
    request: Request,
    pg: dict = Depends(pagination),
    sort_by: str | None = None,
    sort_dir: str = "asc",
    db: Session = Depends(get_db),
    user=Depends(require("doc_template", "read")),
):
    # Danh sách cố ý KHÔNG trả `content_html`: một mẫu có thể dài vài trăm KB,
    # tải hết thân bài chỉ để vẽ bảng tên mẫu là lãng phí.
    query = apply_filters(
        db.query(DocumentTemplate),
        DocumentTemplate,
        request,
        ["name", "doc_type_id", "is_active"],
    )
    total = query.count()
    query = apply_sort(query, DocumentTemplate, sort_by, sort_dir)
    templates = query.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({
        "total": total,
        "items": [_serialize(db, item, detail=False) for item in templates],
    })


@router.get("/{template_id}")
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("doc_template", "read")),
):
    template = template_service.get_or_404(db, template_id)
    return success(_serialize(db, template, detail=True))


@router.post("")
def create_template(
    data: DocumentTemplateCreate,
    db: Session = Depends(get_db),
    user=Depends(require("doc_template", "create")),
):
    template = template_service.create_template(db, data, user.id)
    record(db, user.id, "document_template", template.id, "create")
    return success(_serialize(db, template, detail=True), "Đã tạo văn bản mẫu", 201)


@router.patch("/{template_id}")
def update_template(
    template_id: int,
    data: DocumentTemplateUpdate,
    db: Session = Depends(get_db),
    user=Depends(require("doc_template", "write")),
):
    template = template_service.get_or_404(db, template_id)
    template = template_service.update_template(db, template, data, user.id)
    record(db, user.id, "document_template", template.id, "update")
    return success(_serialize(db, template, detail=True), "Đã cập nhật văn bản mẫu")


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("doc_template", "delete")),
):
    template = template_service.get_or_404(db, template_id)
    template_service.delete_template(db, template)
    record(db, user.id, "document_template", template_id, "delete")
    return success(None, "Đã xóa văn bản mẫu")
