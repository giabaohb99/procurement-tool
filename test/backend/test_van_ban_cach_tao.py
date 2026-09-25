"""CÁCH TẠO văn bản — cột `content_mode` (24/09/2026).

Màn chi tiết bỏ tab «Tệp»: tab «Văn bản» là trình SOẠN THẢO (1) hay trình XEM
TỆP (2) tùy cột này. Trước đó giao diện đoán bằng "nội dung rỗng + có tệp" và
đoán nhầm văn bản soạn thảo vừa tạo, chưa gõ chữ nào mà đã đính tệp.
"""
import pytest
from pydantic import ValidationError

from app.modules.doc_catalog.model import DocType
from app.modules.document import duplicate_service, serializer, service
from app.modules.document.model import CONTENT_MODE_COMPOSE, CONTENT_MODE_FILES
from app.modules.document.schema import DocumentCreate

ACTOR = 1


def _create(db, seed, code, **kw):
    doc_type = DocType(code=code, name=f"Loại {code}", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()
    return service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title=f"Văn bản {code}", **kw,
    ), ACTOR)


def test_defaults_to_compose_when_client_sends_nothing(db, seed):
    """Nơi gọi CŨ (chưa gửi trường này) phải ra đúng hành vi cũ: soạn thảo."""
    doc = _create(db, seed, "CT1")
    assert doc.content_mode == CONTENT_MODE_COMPOSE


def test_files_only_mode_is_persisted_and_serialized(db, seed):
    doc = _create(db, seed, "CT2", content_mode=CONTENT_MODE_FILES)
    assert doc.content_mode == CONTENT_MODE_FILES
    assert serializer.serialize(db, doc)["content_mode"] == CONTENT_MODE_FILES


def test_compose_mode_with_empty_content_stays_compose(db, seed):
    """Đúng ca đoán nhầm cũ: soạn thảo, nội dung RỖNG — vẫn phải là soạn thảo."""
    doc = _create(db, seed, "CT3", content_mode=CONTENT_MODE_COMPOSE, content_html="")
    data = serializer.serialize(db, doc)
    assert data["content_mode"] == CONTENT_MODE_COMPOSE
    assert data["has_content"] is False


@pytest.mark.parametrize("bad", [0, 3, -1, 99])
def test_schema_rejects_unknown_modes(bad):
    with pytest.raises(ValidationError):
        DocumentCreate(doc_type_id=1, company_id=1, department_id=1, owner_employee_id=1,
                       title="x", content_mode=bad)


def test_duplicate_keeps_the_source_mode(db, seed):
    """«Sao chép» văn bản chỉ gồm tệp mà ra bản soạn thảo là mở ra trang giấy trắng."""
    source = _create(db, seed, "CT4", content_mode=CONTENT_MODE_FILES)
    copied = duplicate_service.duplicate(db, source, ACTOR)
    assert copied.content_mode == CONTENT_MODE_FILES


def test_mode_can_be_set_on_update_because_create_page_saves_a_draft_first(db, seed):
    """Màn tạo sinh bản nháp ở bước 1 (mặc định soạn thảo); nút «Tạo, không soạn
    thảo» ở cuối là lượt SỬA. Thiếu trường này ở lượt sửa là văn bản chỉ gồm
    tệp vẫn mở ra trình soạn thảo trắng."""
    from app.modules.document.schema import DocumentUpdate

    draft = _create(db, seed, "CT5")
    assert draft.content_mode == CONTENT_MODE_COMPOSE
    service.update_document(db, draft, DocumentUpdate(content_mode=CONTENT_MODE_FILES), ACTOR)
    db.refresh(draft)
    assert draft.content_mode == CONTENT_MODE_FILES


def test_update_without_the_field_leaves_mode_untouched(db, seed):
    from app.modules.document.schema import DocumentUpdate

    doc = _create(db, seed, "CT6", content_mode=CONTENT_MODE_FILES)
    service.update_document(db, doc, DocumentUpdate(title="Đổi tiêu đề"), ACTOR)
    db.refresh(doc)
    assert doc.content_mode == CONTENT_MODE_FILES


# ── Gửi duyệt văn bản CHỈ GỒM TỆP (lỗi bắt khi test UI 25/09/2026) ─────────────
#  `submit` từng chỉ hỏi `content_html`, nên mọi văn bản «Tạo, không soạn thảo»
#  kẹt ở «Nội dung văn bản còn trống» — không gửi duyệt được bằng đường nào.

def _attach(db, entity, entity_id):
    from app.modules.attachment.model import FileLink

    db.add(FileLink(file_id=1, entity=entity, entity_id=entity_id))
    db.commit()


def test_files_only_document_with_a_file_can_be_submitted(db, seed):
    doc = _create(db, seed, "SF1", content_mode=CONTENT_MODE_FILES, content_html="")
    _attach(db, service.ATTACH_ENTITY, doc.current_version_id)
    service.submit(db, doc, ACTOR)
    db.refresh(doc)
    assert doc.status != service.STATUS_DRAFT


def test_files_only_document_without_any_file_is_still_blocked(db, seed):
    from fastapi import HTTPException

    doc = _create(db, seed, "SF2", content_mode=CONTENT_MODE_FILES, content_html="")
    with pytest.raises(HTTPException) as caught:
        service.submit(db, doc, ACTOR)
    assert caught.value.status_code == 400
    assert "chưa đính kèm tệp" in caught.value.detail


def test_a_file_hung_on_another_record_does_not_count(db, seed):
    """Tệp phải treo đúng PHIÊN BẢN đang trình — trùng số id ở entity khác
    (hay ở phiên bản khác) mà lọt qua là trình duyệt một cái vỏ rỗng."""
    from fastapi import HTTPException

    doc = _create(db, seed, "SF3", content_mode=CONTENT_MODE_FILES, content_html="")
    _attach(db, "purchase_request", doc.current_version_id)
    _attach(db, service.ATTACH_ENTITY, doc.current_version_id + 999)
    with pytest.raises(HTTPException):
        service.submit(db, doc, ACTOR)


def test_compose_document_with_a_file_but_no_text_is_still_blocked(db, seed):
    """Văn bản SOẠN THẢO: tệp chỉ là phụ lục, nội dung chính vẫn phải có."""
    from fastapi import HTTPException

    doc = _create(db, seed, "SF4", content_mode=CONTENT_MODE_COMPOSE, content_html="")
    _attach(db, service.ATTACH_ENTITY, doc.current_version_id)
    with pytest.raises(HTTPException) as caught:
        service.submit(db, doc, ACTOR)
    assert "Nội dung văn bản còn trống" in caught.value.detail
