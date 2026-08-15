from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.book_model import DocumentBook
from app.modules.doc_catalog.model import DocType
from app.modules.doc_catalog.numbering_rule_schema import (
    DocumentNumberingRuleCreate,
    DocumentNumberingRuleUpdate,
)
from app.modules.doc_catalog.numbering_rule_service import (
    create_rule,
    resolve_rule,
    serialize,
    update_rule,
)
from app.modules.document import numbering
from app.modules.document.model import Document
from app.modules.document.service import update_issue_number


def _catalog(db):
    company = Company(code="CT", name="Công ty", issue_code="DEGO", is_active=True)
    db.add(company)
    db.flush()
    department = Department(
        code="PB", name="Phòng HCNS", company_id=company.id,
        issue_code="HCNS", kind=1, is_active=True,
    )
    doc_type = DocType(
        code="TB", name="Thông báo", id_scheme=2, number_when=2, is_active=True,
    )
    book = DocumentBook(
        code="SODI", name="Sổ văn bản đi", kind=2, company_id=company.id,
        number_prefix="CV", is_active=True,
    )
    db.add_all([department, doc_type, book])
    db.commit()
    return company, department, doc_type, book


def test_rule_scope_serialize_and_resolve(db):
    _, _, doc_type, book = _catalog(db)
    rule = create_rule(
        db,
        DocumentNumberingRuleCreate(
            direction=2,
            pattern="{STT}/{Nam}/{LoaiVB}-{PhapNhan}",
            doc_type_mode=2,
            doc_type_ids=[doc_type.id],
            book_mode=2,
            book_ids=[book.id],
        ),
        actor=7,
    )

    output = serialize(db, rule)
    assert output["doc_type_names"] == ["Thông báo"]
    assert output["book_names"] == ["Sổ văn bản đi"]
    assert resolve_rule(db, 2, doc_type.id, book.id).id == rule.id
    assert resolve_rule(db, 2, doc_type.id, None) is None


def test_rule_drives_preview_and_real_number(db):
    company, department, doc_type, book = _catalog(db)
    rule = create_rule(
        db,
        DocumentNumberingRuleCreate(
            direction=2,
            pattern="{SoVB}-{STT}/{Ngay}/{Thang}/{Nam}/{LoaiVB}-{PhongBan}-{PhapNhan}",
            start_no=33,
            reset_yearly=False,
            doc_type_mode=1,
            book_mode=1,
        ),
        actor=7,
    )

    preview = numbering.peek(
        db, doc_type, company.id, department.id, date(2026, 8, 15), book.id,
    )
    assert preview == "CV-33/15/08/2026/TB-HCNS-DEGO"

    doc = SimpleNamespace(
        doc_code=None,
        issue_number="",
        company_id=company.id,
        department_id=department.id,
        book_id=book.id,
        effective_date=date(2026, 8, 15),
        seq_no=None,
        issue_year=None,
        numbering_rule_id=0,
    )
    numbering.assign(db, doc, doc_type, 2026)
    assert doc.issue_number == preview
    assert doc.seq_no == 33
    assert doc.numbering_rule_id == rule.id

    # Đếm liên tục qua năm: không quay về số bắt đầu.
    assert numbering.peek(
        db, doc_type, company.id, department.id, date(2027, 1, 2), book.id,
    ).startswith("CV-34/")

    with pytest.raises(HTTPException, match="đã cấp số"):
        update_rule(
            db,
            rule.id,
            DocumentNumberingRuleUpdate(pattern="{STT}/{Nam}"),
            actor=7,
        )


def test_rule_rejects_book_from_other_direction(db):
    _, _, _, book = _catalog(db)
    with pytest.raises(HTTPException, match="không cùng chiều"):
        create_rule(
            db,
            DocumentNumberingRuleCreate(
                direction=1,
                pattern="{STT}/{Nam}",
                book_mode=2,
                book_ids=[book.id],
            ),
            actor=7,
        )


def test_manual_number_requires_rule_permission_and_keeps_audit_sequence(db):
    company, department, doc_type, book = _catalog(db)
    rule = create_rule(
        db,
        DocumentNumberingRuleCreate(
            direction=2,
            pattern="{STT}/{Nam}/{LoaiVB}",
            allow_manual=True,
            book_mode=1,
        ),
        actor=7,
    )
    doc = Document(
        origin=1,
        doc_type_id=doc_type.id,
        company_id=company.id,
        department_id=department.id,
        book_id=book.id,
        owner_employee_id=1,
        title="Văn bản thử",
        issue_number="01/2026/TB",
        seq_no=1,
        issue_year=2026,
        numbering_rule_id=rule.id,
    )
    db.add(doc)
    db.commit()

    updated, previous = update_issue_number(db, doc, "01A/2026/TB", actor=8)
    assert previous == "01/2026/TB"
    assert updated.issue_number == "01A/2026/TB"
    assert updated.seq_no == 1

    rule.allow_manual = False
    db.commit()
    with pytest.raises(HTTPException, match="không cho phép"):
        update_issue_number(db, doc, "01B/2026/TB", actor=8)
