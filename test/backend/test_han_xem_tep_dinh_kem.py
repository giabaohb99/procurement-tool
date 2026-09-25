"""HẠN XEM TỆP ĐÍNH KÈM của văn bản (24/08/2026).

Văn bản đặt được ngày *"xem tệp tới ngày…"*; quá ngày đó thì mọi tệp đính kèm
**không mở và không tải được nữa**. Kiểm ở BACKEND chứ không ở giao diện: giấu
nút xem chỉ ngăn người dùng bình thường, ai cầm đường dẫn `/view` thì vẫn lấy
được nguyên tệp.

Hai chỗ dễ sai mà bài kiểm này canh:
  * ranh giới ngày — "xem tới 24/08" nghĩa là **hết ngày 24/08 vẫn xem được**;
  * tệp của entity khác (YCMH, ĐMH, bình luận) đi qua cùng đường không được dính
    hạn nào cả.

⚠️ **duoc-CR-478 (23/09/2026) — công tắc TẠM TẮT cả cụm.** Mặc định
`doc_attachment_view_window_enabled` là TẮT (`DOC_ATTACHMENT_VIEW_WINDOW_ENABLED`
= `False`), nên MỌI bài kiểm luật ngày ở dưới phải tự BẬT công tắc trước —
không thì `view_window_expired` trả `False` ngay từ câu đầu, chưa kịp chạm tới
logic ngày mà bài đang muốn đo. `_isolate_app_settings` (conftest) đã dọn cache
rỗng mỗi bài, nên bật/tắt ở đây không rò sang bài khác.
"""
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.core import app_settings
from app.modules.document import attachment_window as due
from app.modules.document.model import Document

TODAY = date(2026, 8, 24)


def _doc(view_until: date | None) -> Document:
    return Document(id=1, title="Tài liệu họp", attachment_view_until=view_until)


def _bat_cong_tac_han_xem() -> None:
    """BẬT công tắc — xem docstring đầu tệp."""
    app_settings._cache["doc_attachment_view_window_enabled"] = "1"


def test_cong_tac_tat_mac_dinh_thi_qua_han_lau_roi_van_xem_duoc():
    """Mặc định TẮT: tệp quá hạn khai cả năm vẫn xem/tải bình thường."""
    assert due.view_window_expired(_doc(TODAY - timedelta(days=365)), TODAY) is False


def test_khong_dat_han_thi_khong_bao_gio_het():
    _bat_cong_tac_han_xem()
    assert due.view_window_expired(_doc(None), TODAY) is False


def test_dung_ngay_han_van_con_xem_duoc():
    """"Xem tới ngày 24/08" = hết ngày 24/08 vẫn xem được — đúng cách người Việt đọc."""
    _bat_cong_tac_han_xem()
    assert due.view_window_expired(_doc(TODAY), TODAY) is False


def test_qua_mot_ngay_la_het():
    _bat_cong_tac_han_xem()
    assert due.view_window_expired(_doc(TODAY - timedelta(days=1)), TODAY) is True


def test_han_o_tuong_lai_thi_con_xem_duoc():
    _bat_cong_tac_han_xem()
    assert due.view_window_expired(_doc(TODAY + timedelta(days=30)), TODAY) is False


def test_khong_co_van_ban_thi_khong_chan():
    """Tệp của YCMH/ĐMH/bình luận đi qua cùng hàm — không được dính hạn nào."""
    _bat_cong_tac_han_xem()
    assert due.view_window_expired(None, TODAY) is False


def test_entity_khac_thi_khong_tra_ra_van_ban(db):
    assert due.document_of_attachment(db, "purchase_request", 1) is None
    assert due.document_of_attachment(db, "comment", 1) is None


def test_chan_neu_het_han_nem_403_kem_ngay(db, seed, monkeypatch):
    """403 chứ không 404: tệp có thật, người này có quyền — chỉ là HẾT GIỜ.

    404 là nói dối, và người dùng sẽ đi báo mất tệp.
    """
    _bat_cong_tac_han_xem()
    doc = Document(id=99, title="Bảng lương kỳ 8",
                   attachment_view_until=date.today() - timedelta(days=1))
    monkeypatch.setattr(due, "document_of_attachment", lambda *a, **kw: doc)

    with pytest.raises(HTTPException) as error:
        due.block_if_expired(db, due.ENTITY_DOCUMENT_VERSION, 1)

    assert error.value.status_code == 403
    #  Câu báo phải nói RÕ NGÀY — "không xem được" trơ trọi thì người dùng đi hỏi
    #  vòng quanh xem ai khóa mất tệp.
    assert doc.attachment_view_until.strftime("%d/%m/%Y") in error.value.detail


def test_con_han_thi_khong_chan(db, monkeypatch):
    _bat_cong_tac_han_xem()
    doc = Document(id=99, title="Còn hạn",
                   attachment_view_until=date.today() + timedelta(days=1))
    monkeypatch.setattr(due, "document_of_attachment", lambda *a, **kw: doc)

    due.block_if_expired(db, due.ENTITY_DOCUMENT_VERSION, 1)  # không ném gì


def test_cong_tac_tat_thi_khong_chan_du_qua_han_tu_lau(db, monkeypatch):
    """Kịch bản 6 của phase 09: công tắc TẮT (mặc định) → `block_if_expired`
    không ném gì cho dù ngày đã khai qua từ cả năm trước."""
    doc = Document(id=99, title="Bảng lương kỳ 8",
                   attachment_view_until=date.today() - timedelta(days=365))
    monkeypatch.setattr(due, "document_of_attachment", lambda *a, **kw: doc)

    due.block_if_expired(db, due.ENTITY_DOCUMENT_VERSION, 1)  # không ném gì


def test_cong_tac_doi_qua_lai_khong_can_khoi_dong_lai(db, monkeypatch):
    """Đổi công tắc GIỮA HAI LƯỢT GỌI có hiệu lực ngay — không có cache riêng
    nào của `attachment_window` cần dọn."""
    doc = Document(id=99, title="Bảng lương kỳ 8",
                   attachment_view_until=date.today() - timedelta(days=1))
    monkeypatch.setattr(due, "document_of_attachment", lambda *a, **kw: doc)

    due.block_if_expired(db, due.ENTITY_DOCUMENT_VERSION, 1)  # tắt: không ném

    _bat_cong_tac_han_xem()
    with pytest.raises(HTTPException):
        due.block_if_expired(db, due.ENTITY_DOCUMENT_VERSION, 1)  # bật: ném ngay
