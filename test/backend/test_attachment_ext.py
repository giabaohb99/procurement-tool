"""Test file attachment extension policy for Purchase Order & other entities."""

import pytest
from app.core.file_registry import FILE_POLICY, policy, ext_of
from app.modules.attachment.controller import _valid_doc_type


def test_ext_of_helper():
    assert ext_of("note_hop.txt") == "txt"
    assert ext_of("hoadon.xml") == "xml"
    assert ext_of("baogia.ZIP") == "zip"
    assert ext_of("file_no_ext") == ""


def test_file_policy_extensions():
    parent, exts, max_mb = policy("purchase_order")
    assert parent == "purchase_order"
    assert "txt" in exts
    assert "xml" in exts
    assert "pdf" in exts
    assert "docx" in exts
    assert "xlsx" in exts

    # Archive and Executable files must be rejected
    assert "zip" not in exts
    assert "rar" not in exts
    assert "7z" not in exts
    assert "exe" not in exts
    assert "bat" not in exts
    assert "sh" not in exts
    assert "dll" not in exts


def test_cdr_allowed_for_documents():
    """File thiết kế CorelDRAW (.cdr) — NCC hay gửi kèm mẫu bao bì/nhãn."""
    for entity in ("purchase_request", "purchase_order", "survey", "contract", "ticket_message"):
        _, exts, _ = policy(entity)
        assert "cdr" in exts, entity
    # Ô chỉ nhận ảnh thì vẫn chỉ ảnh
    for entity in ("product", "avatar", "purchase_request_line_image"):
        _, exts, _ = policy(entity)
        assert "cdr" not in exts, entity


def test_document_size_floor_20mb():
    """Mọi ô đính kèm chứng từ tối thiểu 20MB — file .cdr thường nặng."""
    for entity, (_, exts, max_mb) in FILE_POLICY.items():
        if "pdf" in exts:                       # ô chứng từ (khác ô chỉ nhận ảnh)
            assert max_mb >= 20, f"{entity} = {max_mb}MB"


def test_doc_type_validation():
    assert _valid_doc_type("") == ""
    assert _valid_doc_type("quotation") == "quotation"
    assert _valid_doc_type("other") == "other"
    with pytest.raises(Exception):
        _valid_doc_type("invalid_type_xyz")
