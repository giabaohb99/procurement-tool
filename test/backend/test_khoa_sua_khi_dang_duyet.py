"""ĐANG TRÌNH DUYỆT THÌ ĐÓNG BĂNG (19/08/2026).

Lỗ hổng dựng lại được trên dữ liệu thật: gửi duyệt xong, mọi đường ghi vẫn trả
200 — sửa thân văn bản, đổi tiêu đề, **nâng mức mật lên Mật**, đổi lề. Người
duyệt đọc bản A, người soạn sửa thành bản B, người duyệt bấm Duyệt là ban hành
bản B mà không ai đọc. Luồng nhiều bước còn tệ hơn: bước 1 ký bản A, bước 2 ký
bản B, dấu vết ghi "đã duyệt" cho cả hai, mà `content_sha256` chỉ tính lúc khóa
nên sau đó không còn gì đối chiếu ngược.

Ghi chú cũ trong `version_model` nói cố ý cho sửa ("trả lại thì gõ tiếp"). Lý do
đó chết từ D-029: phải TRẢ VỀ / RÚT PHIẾU rồi mới gõ tiếp.

Cập nhật 24/08/2026 — ba nhịp kết thúc phiên duyệt nay đi ba đường khác nhau:
trả về → «Trả về (9)» *sửa được*, từ chối → «Đã từ chối (10)» *khóa*, rút phiếu
→ Nháp. Bài kiểm dưới đây canh đúng ranh giới đó.

Bài kiểm gọi thẳng tầng dịch vụ, đúng như một người gọi thẳng API sẽ làm — ẩn
nút trên giao diện không phải là chốt chặn.
"""
import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import service, version_service
from app.modules.document.model import (STATUS_DRAFT, STATUS_REJECTED,
                                        STATUS_RETURNED, STATUS_SUBMITTED)
from app.modules.document.schema import (DocumentCreate, DocumentUpdate,
                                         VersionContentUpdate)
from app.modules.document.version_model import DocumentVersion

ACTOR = 1


@pytest.fixture()
def doc(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    return service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế thử",
        content_html="<p>NỘI DUNG GỐC.</p>",
    ), ACTOR)


def _ban(db, doc) -> DocumentVersion:
    return db.get(DocumentVersion, doc.current_version_id)


def test_con_nhap_thi_van_sua_binh_thuong(db, doc):
    """Chốt chặn mới không được đụng tới đường đi thường ngày."""
    version_service.save_content(
        db, _ban(db, doc), VersionContentUpdate(content_html="<p>Sửa lúc nháp.</p>"), ACTOR)
    service.update_document(db, doc, DocumentUpdate(title="Tiêu đề mới"), ACTOR)

    assert doc.status == STATUS_DRAFT
    assert _ban(db, doc).content_html == "<p>Sửa lúc nháp.</p>"
    assert doc.title == "Tiêu đề mới"


def test_gui_duyet_roi_thi_khong_sua_duoc_noi_dung(db, doc):
    service.submit(db, doc, ACTOR)

    with pytest.raises(HTTPException) as error:
        version_service.save_content(
            db, _ban(db, doc), VersionContentUpdate(content_html="<p>SỬA TRỘM.</p>"), ACTOR)

    assert error.value.status_code == 409
    assert "rút phiếu" in error.value.detail.lower()
    assert _ban(db, doc).content_html == "<p>NỘI DUNG GỐC.</p>"


def test_gui_duyet_roi_thi_khong_doi_duoc_le_trang(db, doc):
    service.submit(db, doc, ACTOR)

    with pytest.raises(HTTPException) as error:
        version_service.save_content(db, _ban(db, doc),
                                     VersionContentUpdate(margin_left_mm=35), ACTOR)

    assert error.value.status_code == 409


def test_gui_duyet_roi_thi_khong_doi_duoc_tieu_de_va_muc_mat(db, doc):
    """Nâng mức mật dưới tay người duyệt cũng là đưa họ ký thứ khác thứ họ đọc."""
    service.submit(db, doc, ACTOR)

    with pytest.raises(HTTPException) as error:
        service.update_document(
            db, doc, DocumentUpdate(title="Tiêu đề đổi trộm", secrecy_level=3), ACTOR)

    assert error.value.status_code == 409
    assert doc.status == STATUS_SUBMITTED
    assert doc.title == "Quy chế thử"
    assert doc.secrecy_level != 3


def test_bi_tra_lai_thi_sua_tiep_duoc(db, doc):
    """Đường ra phải còn: trả về → gõ tiếp được. Không ai bị kẹt.

    Từ 24/08/2026 nó về «Trả về (9)» chứ không về Nháp — nhưng CÁI PHẢI GIỮ là
    ghi được nội dung và sửa được trường chung, đúng như hồi còn về Nháp.
    """
    service.submit(db, doc, ACTOR)
    service.send_back(db, doc, "thiếu căn cứ ở mục 2", ACTOR)

    version_service.save_content(
        db, _ban(db, doc), VersionContentUpdate(content_html="<p>Sửa sau khi bị trả.</p>"), ACTOR)
    service.update_document(db, doc, DocumentUpdate(title="Tiêu đề sửa sau khi bị trả"), ACTOR)

    assert doc.status == STATUS_RETURNED
    assert _ban(db, doc).content_html == "<p>Sửa sau khi bị trả.</p>"


def test_bi_tu_choi_thi_khoa_han(db, doc):
    """Từ chối KHÁC trả về: khóa cả nội dung lẫn trường chung, không gửi lại được.

    Trước 24/08/2026 hai nhịp này đi chung `service.reject()` nên từ chối cũng mở
    ra cho gõ tiếp — người soạn sửa cả buổi rồi mới thấy không có nút nào gửi lại.
    """
    service.submit(db, doc, ACTOR)
    service.reject(db, doc, "không duyệt nhu cầu này", ACTOR)

    assert doc.status == STATUS_REJECTED
    #  Bản bị từ chối NHẢ chỗ `open_slot` nên không còn bản nào "đang mở".
    assert service.open_version(db, doc) is None

    with pytest.raises(HTTPException) as error:
        service.update_document(db, doc, DocumentUpdate(title="Cố sửa bản đã từ chối"), ACTOR)
    assert error.value.status_code == 409

    with pytest.raises(HTTPException) as loi_gui:
        service.submit(db, doc, ACTOR)
    assert loi_gui.value.status_code == 400


def test_da_duyet_van_bao_dung_cau_cu(db, doc):
    """Bản đã duyệt vẫn phải nhận câu «mở phiên bản mới», không phải câu rút phiếu."""
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)

    with pytest.raises(HTTPException) as error:
        version_service.save_content(
            db, _ban(db, doc), VersionContentUpdate(content_html="<p>x</p>"), ACTOR)

    assert error.value.status_code == 409
    assert "mở phiên bản mới" in error.value.detail.lower()
