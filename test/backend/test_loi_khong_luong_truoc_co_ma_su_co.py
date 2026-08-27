"""MỌI LỖI 500 PHẢI RA ĐÚNG PHONG BÌ, KÈM MÃ TRA ĐƯỢC.

Trước 25/08/2026 `main.py` không có cửa cho lỗi ngoài dự tính, nên chúng rơi ra
ngoài thành `500 Internal Server Error` **thân rỗng, không phải JSON**. Giao diện
không bóc được phong bì `{success, error}` nên chỉ hiện đúng một dòng «Request
failed with status code 500» — người dùng không biết chuyện gì, người sửa cũng
không có gì để lần (đúng ảnh khách gửi khi bấm *Thêm bước duyệt*).

Gọi thẳng hàm xử lý thay vì dựng `TestClient`: bộ kiểm chạy trong container
không có `httpx`, mà thêm một phụ thuộc chỉ để kiểm một hàm thuần là quá tay.
"""
import asyncio
import json

from fastapi import Request

from app.main import unhandled_exception_handler


def _goi(duong_dan: str = "/api/approval-flows/56/nodes") -> dict:
    request = Request({"type": "http", "method": "POST", "path": duong_dan,
                       "headers": [], "query_string": b""})
    res = asyncio.run(unhandled_exception_handler(
        request, RuntimeError("Duplicate entry 'document--2' for key 'uq_...'")))
    return {"status": res.status_code, "than": json.loads(res.body)}


def test_loi_ngoai_du_tinh_van_ra_dung_phong_bi():
    ket = _goi()

    assert ket["status"] == 500
    assert ket["than"]["success"] is False
    assert ket["than"]["error"]["code"] == "internal_error"


def test_co_MA_SU_CO_de_doi_chieu_voi_log():
    error = _goi()["than"]["error"]

    code = error["details"]["ma_su_co"]
    assert len(code) == 8 and code.isalnum() and code.upper() == code
    #  Mã phải nằm luôn trong câu người dùng ĐỌC ĐƯỢC, không chỉ ở `details`:
    #  không ai mở tab Network để lấy mã đi báo lỗi.
    assert code in error["message"]


def test_moi_lan_no_la_mot_ma_khac():
    """Hai người gặp lỗi cùng lúc phải phân biệt được vết của ai."""
    assert (_goi()["than"]["error"]["details"]["ma_su_co"]
            != _goi()["than"]["error"]["details"]["ma_su_co"])


def test_KHONG_bay_ruot_gan_ra_man_hinh():
    """Tên bảng, câu SQL, dấu vết Python chỉ được nằm trong log."""
    message = _goi()["than"]["error"]["message"]

    assert "RuntimeError" not in message
    assert "Duplicate entry" not in message
    assert "uq_" not in message
