"""bao-CR-728 — trần dung lượng tệp nạp Tra cứu thị trường (`POST /api/customs/imports`).

Trước CR này cửa nạp đọc trọn tệp vào bộ nhớ, không có trần. Canh: tệp quá trần bị 413 câu tiếng Việt và chỉ đọc
tối đa trần + 1 byte; tệp đúng bằng trần vẫn qua bước kiểm cỡ; một tệp quá trần trong lượt nhiều tệp thì cả lượt bị từ
chối, không lưu tệp nào; trần đủ rộng cho tệp xuất 50.000 dòng của lô xuất (bao-CR-718) nạp lại được.

Hai chỗ sửa thêm từ lượt thử trọn vòng xuất, sửa, nạp lại 50.000 dòng: kiểm tiêu đề .xlsx chỉ đọc dòng đầu; bộ gắn
hoạt chất theo tên thương mại cho cùng kết quả ở mọi tiến trình.
"""
import io
from types import SimpleNamespace

import openpyxl
import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from app.modules.customs import controller, pesticide_reader, reader, service
from app.modules.import_tool import service as import_service

USER = SimpleNamespace(id=1)


class _SpyFile(io.BytesIO):
    """Tệp giả ghi lại số byte bị đòi đọc — kiểm cửa nạp không đọc trọn tệp quá trần."""

    def __init__(self, data: bytes):
        super().__init__(data)
        self.read_sizes: list[int] = []

    def read(self, size=-1):
        self.read_sizes.append(size)
        return super().read(size)


def _upload(name: str, data: bytes) -> UploadFile:
    return UploadFile(file=_SpyFile(data), filename=name)


def _export_like_xlsx(rows: int = 2) -> bytes:
    """Tệp cùng cột với tệp xuất (có cột ID + Thao tác) — đúng thứ người dùng nạp lại."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(service.export_header())
    for i in range(rows):
        ws.append([i + 1] + [""] * (len(service.export_header()) - 1))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def no_store(monkeypatch):
    """Chặn lưu kho / tạo lô / gọi Celery — bài này chỉ canh bước kiểm trước khi lưu."""
    saved = []
    monkeypatch.setattr(import_service, "save_upload", lambda db, f, uid: saved.append(f.filename) or None)
    return saved


def test_tran_mac_dinh_30_mb_bang_tran_thuoc_bvtv_va_du_cho_tep_xuat_50000_dong():
    assert reader.MAX_UPLOAD_BYTES == 30 * 1024 * 1024 == pesticide_reader.MAX_UPLOAD_BYTES
    #  Tệp xuất 50.000 dòng đo được ~12,8 MB (kế hoạch bao-CR-718 §6) — trần phải dư ít nhất gấp đôi.
    assert reader.MAX_UPLOAD_BYTES > 2 * 13 * 1024 * 1024
    assert reader.MAX_UPLOAD_LABEL == "30 MB"


def test_tep_qua_tran_bi_413_cau_tieng_viet_va_chi_doc_tran_cong_mot_byte(db, monkeypatch, no_store):
    monkeypatch.setattr(reader, "MAX_UPLOAD_BYTES", 100)
    up = _upload("qua-lon.xlsx", b"PK" + b"x" * 500)
    with pytest.raises(HTTPException) as exc:
        controller.upload_files(files=[up], db=db, user=USER)
    assert exc.value.status_code == 413
    assert exc.value.detail.startswith("\"qua-lon.xlsx\": tệp quá lớn (tối đa 30 MB mỗi tệp)")
    assert up.file.read_sizes == [101]
    assert no_store == []


def test_tep_dung_bang_tran_qua_buoc_kiem_co_roi_moi_kiem_tieu_de(db, monkeypatch, no_store):
    monkeypatch.setattr(reader, "MAX_UPLOAD_BYTES", 100)
    up = _upload("vua-tran.xlsx", b"PK" + b"x" * 98)          # đúng 100 byte, không phải xlsx thật
    with pytest.raises(HTTPException) as exc:
        controller.upload_files(files=[up], db=db, user=USER)
    assert exc.value.status_code == 400                        # rơi xuống bước đọc tiêu đề, không phải 413
    assert "Không đọc được tệp .xlsx" in exc.value.detail


def test_mot_tep_qua_tran_trong_luot_nhieu_tep_thi_khong_luu_tep_nao(db, monkeypatch, no_store):
    good = _export_like_xlsx()
    monkeypatch.setattr(reader, "MAX_UPLOAD_BYTES", len(good) + 10)
    files = [_upload("tep-1.xlsx", good), _upload("tep-2.xlsx", good + b"\0" * 50)]
    with pytest.raises(HTTPException) as exc:
        controller.upload_files(files=files, db=db, user=USER)
    assert exc.value.status_code == 413 and "\"tep-2.xlsx\"" in exc.value.detail
    assert no_store == []


def test_kiem_tieu_de_xlsx_chi_doc_dong_dau(monkeypatch):
    """Thử trọn vòng 50.000 dòng: đọc trọn lưới chỉ để xem tiêu đề tốn ~19 giây + ~500 MB trong tiến trình api."""
    raw = _export_like_xlsx(rows=5)
    assert len(reader.load_cells(raw, "x.xlsx")) == 6
    assert len(reader.load_cells(raw, "x.xlsx", max_rows=1)) == 1
    calls = []
    original = reader.load_cells
    monkeypatch.setattr(reader, "load_cells", lambda r, n="", max_rows=None: calls.append(max_rows) or original(r, n,
                                                                                                             max_rows))
    reader.check_headers(raw, "x.xlsx")
    assert calls == [1]


def test_go_hoat_chat_theo_ten_thuong_mai_on_dinh_theo_thu_tu_tu_trong_ten_hang():
    """Trước CR này duyệt từ bằng `set` — thứ tự đổi theo từng tiến trình nên cùng tên hàng ra hoạt chất khác nhau,
    xuất rồi nạp lại tệp không sửa vẫn báo "Ghi đè". Nay: tên thương mại xuất hiện TRƯỚC trong tên hàng thắng."""
    from app.modules.customs.ingredient import IngredientTagger
    letters = [chr(65 + i) for i in range(20)]
    trades = [(f"MARK{c}{c} PLUS", f"HOAT CHAT {c}") for c in letters]
    tagger = IngredientTagger([], trades)
    for order in (letters, letters[::-1], letters[7:] + letters[:7]):
        name = " ".join(f"MARK{c}{c} PLUS" for c in order) + " 25KG/DRUM"
        assert tagger.tag(name)[0] == f"HOAT CHAT {order[0]}"


def test_tep_xuat_duoi_tran_qua_kiem_va_con_tro_ve_dau_tep_de_luu(db, monkeypatch):
    """Tệp hợp lệ dưới trần: qua kiểm tiêu đề, con trỏ tệp quay về đầu để bước lưu kho đọc đủ."""
    raw = _export_like_xlsx(rows=3)
    seen = {}

    def fake_save(db_, f, uid):
        seen["bytes"] = f.file.read()
        raise HTTPException(418, "dừng ở bước lưu")              # đủ để biết đã qua mọi bước kiểm
    monkeypatch.setattr(import_service, "save_upload", fake_save)
    with pytest.raises(HTTPException) as exc:
        controller.upload_files(files=[_upload("xuat-lai.xlsx", raw)], db=db, user=USER)
    assert exc.value.status_code == 418
    assert seen["bytes"] == raw
