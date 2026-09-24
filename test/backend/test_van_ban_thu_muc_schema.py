"""Schema CÂY THƯ MỤC VĂN BẢN — `folder_schema.py` + `document/schema.py`
(rà soát code-reviewer 23/09/2026, M4 + M5).

Test THUẦN Pydantic — không cần `db`/`world`, chỉ dựng model rồi kiểm
`ValidationError` (422 ở tầng FastAPI), không đi qua HTTP.
"""
import pytest
from pydantic import ValidationError

from app.modules.doc_catalog.folder_schema import (MAX_BULK_IDS, DocumentFolderSetIn,
                                                    FolderLinkIn, FolderReorderIn, FolderUnlinkIn)
from app.modules.document.schema import DocumentCreate, DocumentUpdate


# ── M4 — `mode` sai kiểu phải ra ValidationError (422), không phải 500 ──────
def test_folder_link_in_mode_hop_le_add_replace():
    assert FolderLinkIn(document_ids=[1], folder_id=1, mode="add").mode == "add"
    assert FolderLinkIn(document_ids=[1], folder_id=1, mode="replace").mode == "replace"


def test_folder_link_in_mode_khong_hop_le_ra_validation_error():
    """Trước M4: `model_post_init` tự `raise ValueError` — Pydantic v2 KHÔNG
    bọc lỗi từ hook này thành `ValidationError`, nên nó lọt thành 500 chưa bắt
    ở tầng FastAPI thay vì 422. `Literal` khiến Pydantic tự bắt NGAY khi dựng
    model, trước khi code nghiệp vụ nào chạy tới."""
    with pytest.raises(ValidationError):
        FolderLinkIn(document_ids=[1], folder_id=1, mode="xoa-het")


def test_folder_link_in_mode_mac_dinh_la_add():
    assert FolderLinkIn(document_ids=[1], folder_id=1).mode == "add"


# ── M5 — trần số id một lượt gửi ─────────────────────────────────────────────
def test_folder_link_in_qua_tran_id_ra_validation_error():
    with pytest.raises(ValidationError):
        FolderLinkIn(document_ids=list(range(1, MAX_BULK_IDS + 2)), folder_id=1)


def test_folder_link_in_dung_tran_id_van_hop_le():
    data = FolderLinkIn(document_ids=list(range(1, MAX_BULK_IDS + 1)), folder_id=1)
    assert len(data.document_ids) == MAX_BULK_IDS


def test_folder_unlink_in_qua_tran_id_ra_validation_error():
    with pytest.raises(ValidationError):
        FolderUnlinkIn(document_ids=list(range(1, MAX_BULK_IDS + 2)), folder_id=1)


def test_document_folder_set_in_qua_tran_id_ra_validation_error():
    with pytest.raises(ValidationError):
        DocumentFolderSetIn(folder_ids=list(range(1, MAX_BULK_IDS + 2)))


def test_folder_reorder_in_qua_tran_id_ra_validation_error():
    items = [{"id": i, "sort_order": i} for i in range(1, MAX_BULK_IDS + 2)]
    with pytest.raises(ValidationError):
        FolderReorderIn(items=items)


def test_document_create_qua_tran_id_ra_validation_error():
    with pytest.raises(ValidationError):
        DocumentCreate(
            doc_type_id=1, company_id=1, department_id=1, owner_employee_id=1,
            title="X", folder_ids=list(range(1, MAX_BULK_IDS + 2)),
        )


def test_document_update_qua_tran_id_ra_validation_error():
    with pytest.raises(ValidationError):
        DocumentUpdate(folder_ids=list(range(1, MAX_BULK_IDS + 2)))
