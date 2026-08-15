"""Nghiệp vụ thư viện văn bản mẫu."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.doc_catalog.model import DocType

from .template_model import DocumentTemplate
from .template_schema import DocumentTemplateCreate, DocumentTemplateUpdate


def get_or_404(db: Session, template_id: int) -> DocumentTemplate:
    template = db.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(404, "Không tìm thấy văn bản mẫu")
    return template


def _doc_type_or_400(db: Session, doc_type_id: int) -> DocType:
    doc_type = db.get(DocType, doc_type_id)
    if not doc_type:
        raise HTTPException(400, "Loại văn bản không tồn tại")
    if not doc_type.is_active:
        raise HTTPException(400, f"Loại văn bản {doc_type.name} đã ngừng dùng")
    return doc_type


def _ensure_unique_name(
    db: Session,
    doc_type_id: int,
    name: str,
    exclude_id: int | None = None,
) -> None:
    query = db.query(DocumentTemplate.id).filter(
        DocumentTemplate.doc_type_id == doc_type_id,
        DocumentTemplate.name == name,
    )
    if exclude_id:
        query = query.filter(DocumentTemplate.id != exclude_id)
    if query.first():
        raise HTTPException(400, "Tên văn bản mẫu đã tồn tại trong loại văn bản này")


def create_template(
    db: Session,
    data: DocumentTemplateCreate,
    actor: int,
) -> DocumentTemplate:
    _doc_type_or_400(db, data.doc_type_id)
    _ensure_unique_name(db, data.doc_type_id, data.name)
    template = DocumentTemplate(
        **data.model_dump(),
        created_by=actor,
        updated_by=actor,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def update_template(
    db: Session,
    template: DocumentTemplate,
    data: DocumentTemplateUpdate,
    actor: int,
) -> DocumentTemplate:
    values = data.model_dump(exclude_unset=True)
    doc_type_id = values.get("doc_type_id", template.doc_type_id)
    name = values.get("name", template.name)
    if doc_type_id != template.doc_type_id:
        _doc_type_or_400(db, doc_type_id)
    if "doc_type_id" in values or "name" in values:
        _ensure_unique_name(db, doc_type_id, name, template.id)

    for key, value in values.items():
        setattr(template, key, value)
    template.updated_by = actor
    db.commit()
    db.refresh(template)
    return template


def delete_template(db: Session, template: DocumentTemplate) -> None:
    # Văn bản đã tạo chỉ giữ bản sao nội dung, không tham chiếu ngược về mẫu,
    # nên xóa mẫu không làm mất hoặc đổi nội dung văn bản nào.
    db.delete(template)
    db.commit()
