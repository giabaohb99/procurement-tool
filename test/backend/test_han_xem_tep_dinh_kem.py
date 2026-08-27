"""HẠN XEM TỆP ĐÍNH KÈM của văn bản (24/08/2026).

Văn bản đặt được ngày *"xem tệp tới ngày…"*; quá ngày đó thì mọi tệp đính kèm
**không mở và không tải được nữa**. Kiểm ở BACKEND chứ không ở giao diện: giấu
nút xem chỉ ngăn người dùng bình thường, ai cầm đường dẫn `/view` thì vẫn lấy
được nguyên tệp.

Hai chỗ dễ sai mà bài kiểm này canh:
  * ranh giới ngày — "xem tới 24/08" nghĩa là **hết ngày 24/08 vẫn xem được**;
  * tệp của entity khác (YCMH, ĐMH, bình luận) đi qua cùng đường không được dính
    hạn nào cả.
"""
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.modules.document import attachment_window as due
from app.modules.document.model import Document

TODAY = date(2026, 8, 24)


def _doc(view_until: date | None) -> Document:
    return Document(id=1, title="Tài liệu họp", attachment_view_until=view_until)


def test_khong_dat_han_thi_khong_bao_gio_het():
    assert due.view_window_expired(_doc(None), TODAY) is False


def test_dung_ngay_han_van_con_xem_duoc():
    """"Xem tới ngày 24/08" = hết ngày 24/08 vẫn xem được — đúng cách người Việt đọc."""
    assert due.view_window_expired(_doc(TODAY), TODAY) is False


def test_qua_mot_ngay_la_het():
    assert due.view_window_expired(_doc(TODAY - timedelta(days=1)), TODAY) is True


def test_han_o_tuong_lai_thi_con_xem_duoc():
    assert due.view_window_expired(_doc(TODAY + timedelta(days=30)), TODAY) is False


def test_khong_co_van_ban_thi_khong_chan():
    """Tệp của YCMH/ĐMH/bình luận đi qua cùng hàm — không được dính hạn nào."""
    assert due.view_window_expired(None, TODAY) is False


def test_entity_khac_thi_khong_tra_ra_van_ban(db):
    assert due.document_of_attachment(db, "purchase_request", 1) is None
    assert due.document_of_attachment(db, "comment", 1) is None


def test_chan_neu_het_han_nem_403_kem_ngay(db, seed, monkeypatch):
    """403 chứ không 404: tệp có thật, người này có quyền — chỉ là HẾT GIỜ.

    404 là nói dối, và người dùng sẽ đi báo mất tệp.
    """
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
    doc = Document(id=99, title="Còn hạn",
                   attachment_view_until=date.today() + timedelta(days=1))
    monkeypatch.setattr(due, "document_of_attachment", lambda *a, **kw: doc)

    due.block_if_expired(db, due.ENTITY_DOCUMENT_VERSION, 1)  # không ném gì
