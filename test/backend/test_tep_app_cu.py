"""Đường đọc byte của tệp đính kèm còn nằm ở kho app cũ (`core/legacy_files.py`).

Bộ này KHÔNG gọi mạng. Nó chỉ canh đúng một thứ: mỗi dòng `tab_file` được đưa
tới ĐÚNG cái kho của nó. Đọc nhầm kho là lỗi im lặng tệ nhất của cụm này — dòng
`datxe` mà hỏi kho ERP thì trả 404 cho một tệp vẫn còn sống, còn dòng của ERP mà
hỏi kho app cũ thì trúng một tệp KHÁC HOÀN TOÀN (hai kho trùng tiền tố
`uploads/`, không trùng nội dung).

Phép kiểm đọc được byte thật của cả 1488 tệp nằm ở
`backend/scripts/legacy_sync/verify_legacy_bucket.py` — nó cần khóa R2 nên
không sống trong bộ test được.
"""
import pytest
from fastapi import HTTPException

from app.core import legacy_files
from app.core.legacy_files import SOURCE_DATXE, is_remote, read_file_bytes


class FakeFile:
    """Một dòng `tab_file` vừa đủ cho `read_file_bytes`."""

    def __init__(self, source="", file_key="uploads/abc-hop dong.pdf",
                 external_id="kX2Sv3WXOiNW", id=7):
        self.source = source
        self.file_key = file_key
        self.external_id = external_id
        self.id = id


@pytest.fixture
def bucket_on(monkeypatch):
    """Bật cấu hình kho app cũ và ghi lại khóa nào được hỏi."""
    asked = []

    def fake_download(key):
        asked.append(key)
        return b"noi dung that"

    monkeypatch.setattr(legacy_files, "legacy_bucket_ready", lambda: True)
    monkeypatch.setattr(legacy_files, "download_legacy_bytes", fake_download)
    return asked


def test_tep_cua_erp_van_di_kho_erp(monkeypatch):
    """Dòng thường (`source` rỗng) KHÔNG được đổi hành vi dù thêm kho thứ hai."""
    goi = []
    monkeypatch.setattr(legacy_files, "download_bytes",
                        lambda key: goi.append(key) or b"erp")
    #  Kho app cũ bật sẵn, mà vẫn phải đi đường cũ.
    monkeypatch.setattr(legacy_files, "legacy_bucket_ready", lambda: True)

    f = FakeFile(source="", file_key="prod/attachment/2026/07/1-a.pdf")
    assert read_file_bytes(f) == b"erp"
    assert goi == ["prod/attachment/2026/07/1-a.pdf"]


def test_tep_app_cu_doc_thang_kho_cu(bucket_on):
    """Dòng `datxe` hỏi kho app cũ, và hỏi bằng `file_key` chứ không phải id."""
    f = FakeFile(source=SOURCE_DATXE, file_key="uploads/uid/xyz-Hợp đồng.pdf")
    assert read_file_bytes(f) == b"noi dung that"
    assert bucket_on == ["uploads/uid/xyz-Hợp đồng.pdf"]


def test_khoa_co_dau_tieng_viet_khong_bi_sua(bucket_on):
    """Khóa đi xuống kho phải NGUYÊN VẸN từng ký tự.

    Khóa thật có dấu tiếng Việt, khoảng trắng và dấu ngoặc — ví dụ
    `...-Biên bảng điều chỉnh hoá đơn ĐL Trung Liễu (4803-4804).pdf`. Ai đó
    "dọn dẹp" bằng `safe_name` hay `quote` ở tầng này là 1488 tệp mất đường về
    cùng lúc; việc mã hóa cho chữ ký S3 là của boto3, không phải của chỗ này.
    """
    key = "uploads/uid/abc-Biên bảng điều chỉnh hoá đơn ĐL Trung Liễu (4803-4804).pdf"
    read_file_bytes(FakeFile(source=SOURCE_DATXE, file_key=key))
    assert bucket_on == [key]


def test_chua_cau_hinh_thi_noi_ro_chu_khong_404(monkeypatch):
    """Chưa có khóa kho cũ thì trả 503 kèm câu người thường đọc được.

    Cố ý KHÔNG phải 404: tệp vẫn còn nguyên bên app cũ, câu 404 làm người dùng
    tưởng tệp đã mất rồi đi tìm bản sao.
    """
    monkeypatch.setattr(legacy_files, "legacy_bucket_ready", lambda: False)
    monkeypatch.setattr(legacy_files, "legacy_ready", lambda: False)

    with pytest.raises(HTTPException) as err:
        read_file_bytes(FakeFile(source=SOURCE_DATXE))
    assert err.value.status_code == 503
    assert "app đặt xe cũ" in err.value.detail


def test_nguon_la_thi_dung_lai_chu_khong_doan(monkeypatch):
    """`source` lạ thì dừng, đừng đoán bừa là kho nào."""
    monkeypatch.setattr(legacy_files, "legacy_bucket_ready", lambda: True)
    with pytest.raises(HTTPException) as err:
        read_file_bytes(FakeFile(source="pos365"))
    assert err.value.status_code == 503


def test_thieu_file_key_la_loi_cua_dot_nap(monkeypatch):
    """Mang cờ `datxe` mà không có khóa thì không tra được nữa — dừng gọn."""
    monkeypatch.setattr(legacy_files, "legacy_bucket_ready", lambda: True)
    monkeypatch.setattr(legacy_files, "download_legacy_bytes",
                        lambda key: pytest.fail("không được hỏi kho với khóa rỗng"))
    with pytest.raises(HTTPException) as err:
        read_file_bytes(FakeFile(source=SOURCE_DATXE, file_key=""))
    assert err.value.status_code == 503


def test_kho_cu_hong_thi_khong_lo_ten_bucket(monkeypatch):
    """Câu trả cho người dùng KHÔNG được mang theo lời của boto3.

    Lỗi gốc có tên bucket và nguyên khóa tệp; đưa thẳng ra là vẽ sơ đồ kho cho
    người lạ. Chi tiết nằm ở nhật ký máy chủ, chỗ này chỉ nói "thử lại sau".
    """
    def no(key):
        raise RuntimeError("NoSuchBucket: degoholding-app-cdn / uploads/uid/x.pdf")

    monkeypatch.setattr(legacy_files, "legacy_bucket_ready", lambda: True)
    monkeypatch.setattr(legacy_files, "download_legacy_bytes", no)

    with pytest.raises(HTTPException) as err:
        read_file_bytes(FakeFile(source=SOURCE_DATXE))
    assert err.value.status_code == 503
    assert "degoholding-app-cdn" not in err.value.detail
    assert "uploads/" not in err.value.detail


def test_is_remote_doc_theo_cot_source():
    assert is_remote(FakeFile(source=SOURCE_DATXE)) is True
    assert is_remote(FakeFile(source="")) is False
    assert is_remote(FakeFile(source="   ")) is False
