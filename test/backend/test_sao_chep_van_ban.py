"""SAO CHÉP VĂN BẢN để dựng nhanh một bản ghi thử độc lập."""

from datetime import datetime

import pytest

from app.modules.attachment.model import FileLink, StoredFile
from app.modules.company.model import Company
from app.modules.doc_catalog.link_rule_model import (RELATION_BASED_ON,
                                                     RELATION_REFERENCE)
from app.modules.doc_catalog.model import DocType
from app.modules.document import duplicate_service, service
from app.modules.document.access_model import (EFFECT_ALLOW, SUBJECT_EMPLOYEE,
                                               DocumentAccess)
from app.modules.document.link_model import DocumentLink
from app.modules.document.model import STATUS_DRAFT
from app.modules.document.schema import DocumentCreate
from app.modules.document.scope_model import (DIM_COMPANY, MODE_INCLUDE,
                                              DocumentScope)
from app.modules.document.version_model import VERSION_DRAFT, DocumentVersion

ACTOR = 1


@pytest.fixture()
def source(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    target = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id,
        company_id=seed.company_id,
        department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id,
        title="Văn bản làm căn cứ",
        content_html="<p>Căn cứ</p>",
    ), ACTOR)
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id,
        company_id=seed.company_id,
        department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id,
        drafter_employee_id=seed.emp_nstm_id,
        title="Quy chế dùng làm dữ liệu thử",
        summary="Tóm tắt giữ nguyên",
        keywords="test, sao chép",
        secrecy_level=2,
        urgency=2,
        content_html="<h1>Nội dung cần sao chép</h1>",
    ), ACTOR)

    version = db.get(DocumentVersion, doc.current_version_id)
    version.margin_left_mm = 35
    version.margin_right_mm = 18
    version.auto_heading_number = True
    version.header_left = "DEGO"
    version.footer_right = "{{trang}}/{{tong_trang}}"

    stored = StoredFile(
        filename="phu-luc.pdf",
        file_key="tests/phu-luc.pdf",
        content_type="application/pdf",
        size=120,
        created_by=ACTOR,
        updated_by=ACTOR,
    )
    db.add(stored)
    db.flush()
    db.add(FileLink(
        file_id=stored.id,
        entity=service.ATTACH_ENTITY,
        entity_id=version.id,
        doc_type="attachment",
        created_by=ACTOR,
        updated_by=ACTOR,
    ))
    db.add(DocumentScope(
        document_id=doc.id,
        dim=DIM_COMPANY,
        company_id=seed.company_id,
        mode=MODE_INCLUDE,
        created_by=ACTOR,
        updated_by=ACTOR,
    ))
    db.add(DocumentAccess(
        document_id=doc.id,
        subject_kind=SUBJECT_EMPLOYEE,
        subject_id=seed.emp_nstm_id,
        effect=EFFECT_ALLOW,
        can_read=True,
        can_write=True,
        reason="Dùng thử",
        created_by=ACTOR,
        updated_by=ACTOR,
    ))
    db.add(DocumentAccess(
        document_id=doc.id,
        subject_kind=SUBJECT_EMPLOYEE,
        subject_id=seed.emp_backup_id,
        effect=EFFECT_ALLOW,
        can_read=True,
        reason="Quyền cũ đã thu hồi",
        revoked_at=datetime.now(),
        revoked_by=ACTOR,
        created_by=ACTOR,
        updated_by=ACTOR,
    ))
    db.add(DocumentLink(
        source_document_id=doc.id,
        target_document_id=target.id,
        relation=RELATION_REFERENCE,
        note="Quan hệ khai tay",
        is_system=False,
        created_by=ACTOR,
        updated_by=ACTOR,
    ))
    db.add(DocumentLink(
        source_document_id=doc.id,
        target_document_id=target.id,
        relation=RELATION_BASED_ON,
        note="Quan hệ hệ thống không được chép",
        is_system=True,
        created_by=ACTOR,
        updated_by=ACTOR,
    ))
    db.commit()

    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    db.refresh(doc)
    return {
        "doc": doc,
        "target": target,
        "version": version,
        "stored_file_id": stored.id,
        "seed": seed,
    }


def test_tao_record_nhap_doc_lap_cung_phap_nhan_va_khong_chep_so(db, source):
    original = source["doc"]
    copied = duplicate_service.duplicate(db, original, ACTOR)

    assert copied.id != original.id
    assert copied.company_id == original.company_id
    assert copied.title == f"{original.title} (Copy)"
    assert copied.summary == original.summary
    assert copied.keywords == original.keywords
    assert copied.status == STATUS_DRAFT
    assert copied.doc_code is None
    assert copied.issue_number == ""
    assert copied.seq_no is None
    assert copied.book_seq_no is None
    assert copied.source_document_id is None
    assert copied.clone_source_version_id is None


def test_chep_noi_dung_the_thuc_va_tep_nhung_mo_lai_thanh_ban_nhap(db, source):
    copied = duplicate_service.duplicate(db, source["doc"], ACTOR)
    version = db.get(DocumentVersion, copied.current_version_id)

    assert version.status == VERSION_DRAFT
    assert version.is_locked is False
    assert version.content_html == "<h1>Nội dung cần sao chép</h1>"
    assert version.margin_left_mm == 35
    assert version.margin_right_mm == 18
    assert version.auto_heading_number is True
    assert version.header_left == "DEGO"
    assert version.footer_right == "{{trang}}/{{tong_trang}}"
    links = db.query(FileLink).filter(
        FileLink.entity == service.ATTACH_ENTITY,
        FileLink.entity_id == version.id,
    ).all()
    assert len(links) == 1
    assert links[0].file_id == source["stored_file_id"]


def test_chep_pham_vi_quyen_dang_song_va_quan_he_khai_tay(db, source):
    copied = duplicate_service.duplicate(db, source["doc"], ACTOR)

    scopes = db.query(DocumentScope).filter(DocumentScope.document_id == copied.id).all()
    assert len(scopes) == 1
    assert scopes[0].company_id == source["seed"].company_id

    access = db.query(DocumentAccess).filter(DocumentAccess.document_id == copied.id).all()
    assert len(access) == 1
    assert access[0].subject_id == source["seed"].emp_nstm_id
    assert access[0].can_write is True

    links = db.query(DocumentLink).filter(
        DocumentLink.source_document_id == copied.id,
    ).all()
    assert len(links) == 1
    assert links[0].target_document_id == source["target"].id
    assert links[0].relation == RELATION_REFERENCE
    assert links[0].is_system is False
