"""C03/C06 — đính kèm văn bản không phát link công khai, và có mã băm toàn vẹn.

`url` trong `tab_file` là đường đọc thẳng kho lưu trữ, không qua lớp kiểm nào:
chạy local thì đó là `/api/uploads/...` gắn bằng `StaticFiles` (không hỏi đăng
nhập), chạy thật thì là URL công khai của bucket. Đưa chuỗi đó ra ngoài nghĩa là
ai cầm được nó đều mở được tệp — kể cả người đã bị thu hồi quyền.

Bài kiểm này canh đúng chỗ đó, và canh cả chiều ngược lại: các phân hệ Thu mua
VẪN phải nhận được `url` như cũ, vì `frontend/` đang đóng băng đọc nó.
"""
import hashlib
import io

from app.core.file_registry import is_private
from app.modules.attachment.controller import _link_out, _sha256_of
from app.modules.attachment.model import FileLink, StoredFile


def _cap(entity: str, url: str = "https://kho.example/prod/a.pdf", sha: str = "abc"):
    link = FileLink(id=1, file_id=2, entity=entity, entity_id=3, doc_type="", sort_order=0)
    stored = StoredFile(id=2, filename="a.pdf", file_key="prod/a.pdf", url=url,
                        content_type="application/pdf", size=10, sha256=sha)
    return _link_out(link, stored)


def test_dinh_kem_van_ban_khong_tra_link_cong_khai():
    assert is_private("document_version") is True
    assert _cap("document_version")["url"] == ""


def test_dinh_kem_thu_mua_van_giu_link_nhu_cu():
    """`frontend/` đóng băng đang đọc `url` — đổi là vỡ màn đang chạy thật."""
    assert is_private("purchase_request") is False
    assert _cap("purchase_request")["url"] == "https://kho.example/prod/a.pdf"


def test_ma_bam_van_tra_ve_ca_khi_giau_link():
    """Giấu đường tải nhưng KHÔNG giấu mã băm — đó là thứ để đối chiếu tệp."""
    assert _cap("document_version", sha="deadbeef")["sha256"] == "deadbeef"


def test_ma_bam_dung_voi_noi_dung_tep():
    noi_dung = b"quy che luong 2026"
    assert _sha256_of(io.BytesIO(noi_dung)) == hashlib.sha256(noi_dung).hexdigest()


def test_bam_xong_phai_tra_con_tro_ve_dau():
    """Bẫy: ngay sau khi băm là `upload_fileobj` đọc lại chính luồng này.

    Quên `seek(0)` thì nó đọc được 0 byte và đẩy lên kho một tệp RỖNG — mà không
    có lỗi nào bật lên, chỉ tới lúc ai đó bấm tải về mới lộ.
    """
    luong = io.BytesIO(b"noi dung that")
    _sha256_of(luong)
    assert luong.read() == b"noi dung that"


def test_tep_rong_van_co_ma_bam():
    """Tệp 0 byte là hợp lệ; mã băm rỗng chỉ được dành cho tệp tải lên trước C06."""
    assert _sha256_of(io.BytesIO(b"")) == hashlib.sha256(b"").hexdigest()
