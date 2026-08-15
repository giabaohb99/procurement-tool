"""Thư viện văn bản mẫu và nguyên tắc chép nội dung khi tạo văn bản."""
import pytest
from fastapi import HTTPException

from app.modules.doc_catalog.model import DocType
from app.modules.document import service as document_service
from app.modules.document import template_service
from app.modules.document.schema import DocumentCreate
from app.modules.document.template_schema import (DocumentTemplateCreate,
                                                  DocumentTemplateUpdate)
from app.modules.document.version_model import DocumentVersion

ACTOR = 1


def _doc_type(db, code="QD", name="Quyết định", active=True):
    row = DocType(code=code, name=name, id_scheme=2, number_when=2,
                  is_active=active)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_tao_va_cap_nhat_van_ban_mau(db):
    doc_type = _doc_type(db)
    template = template_service.create_template(
        db,
        DocumentTemplateCreate(
            doc_type_id=doc_type.id,
            name="  Quyết định bổ nhiệm  ",
            description="  Dùng cho nhân sự quản lý  ",
            content_html="<h1>QUYẾT ĐỊNH</h1>",
        ),
        ACTOR,
    )

    assert template.name == "Quyết định bổ nhiệm"
    assert template.description == "Dùng cho nhân sự quản lý"
    assert template.is_active is True

    updated = template_service.update_template(
        db,
        template,
        DocumentTemplateUpdate(content_html="<h1>QUYẾT ĐỊNH MỚI</h1>"),
        ACTOR,
    )
    assert updated.content_html == "<h1>QUYẾT ĐỊNH MỚI</h1>"


def test_khong_trung_ten_mau_trong_cung_loai(db):
    doc_type = _doc_type(db)
    payload = DocumentTemplateCreate(
        doc_type_id=doc_type.id,
        name="Thông báo nội bộ",
        content_html="<p>Nội dung</p>",
    )
    template_service.create_template(db, payload, ACTOR)
    # Một loại có nhiều mẫu, miễn là tên trong cùng loại không trùng nhau.
    second = template_service.create_template(
        db,
        DocumentTemplateCreate(
            doc_type_id=doc_type.id,
            name="Thông báo khách hàng",
            content_html="<p>Nội dung khác</p>",
        ),
        ACTOR,
    )
    assert second.doc_type_id == doc_type.id

    with pytest.raises(HTTPException, match="đã tồn tại"):
        template_service.create_template(db, payload, ACTOR)

    # Hai loại khác nhau được phép dùng cùng một tên mẫu.
    other_type = _doc_type(db, code="CV", name="Công văn")
    same_name = template_service.create_template(
        db,
        DocumentTemplateCreate(
            doc_type_id=other_type.id,
            name="Thông báo nội bộ",
            content_html="<p>Mẫu của loại khác</p>",
        ),
        ACTOR,
    )
    assert same_name.doc_type_id == other_type.id


def test_khong_tao_mau_cho_loai_da_ngung(db):
    doc_type = _doc_type(db, active=False)

    with pytest.raises(HTTPException, match="đã ngừng dùng"):
        template_service.create_template(
            db,
            DocumentTemplateCreate(doc_type_id=doc_type.id, name="Mẫu cũ"),
            ACTOR,
        )


def test_noi_dung_mau_duoc_chep_vao_phien_ban_dau_tien(db, seed):
    doc_type = _doc_type(db)
    template = template_service.create_template(
        db,
        DocumentTemplateCreate(
            doc_type_id=doc_type.id,
            name="Quyết định chuẩn",
            content_html="<h1>QUYẾT ĐỊNH</h1><p>Nội dung mẫu</p>",
        ),
        ACTOR,
    )

    document = document_service.create_document(
        db,
        DocumentCreate(
            doc_type_id=doc_type.id,
            company_id=seed.company_id,
            department_id=seed.dept_id,
            owner_employee_id=seed.emp_req_id,
            title="Quyết định thử nghiệm",
            content_html=template.content_html,
        ),
        ACTOR,
    )
    version = db.get(DocumentVersion, document.current_version_id)
    assert version.content_html == template.content_html

    template_service.update_template(
        db,
        template,
        DocumentTemplateUpdate(content_html="<p>Nội dung mẫu đã đổi</p>"),
        ACTOR,
    )
    db.refresh(version)
    assert version.content_html == "<h1>QUYẾT ĐỊNH</h1><p>Nội dung mẫu</p>"
