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

from app.modules.document import attachment_window as han
from app.modules.document.model import Document

HOM_NAY = date(2026, 8, 24)


def _doc(view_until: date | None) -> Document:
    return Document(id=1, title="Tài liệu họp", attachment_view_until=view_until)


def test_khong_dat_han_thi_khong_bao_gio_het():
    assert han.het_han_xem(_doc(None), HOM_NAY) is False


def test_dung_ngay_han_van_con_xem_duoc():
    """"Xem tới ngày 24/08" = hết ngày 24/08 vẫn xem được — đúng cách người Việt đọc."""
    assert han.het_han_xem(_doc(HOM_NAY), HOM_NAY) is False


def test_qua_mot_ngay_la_het():
    assert han.het_han_xem(_doc(HOM_NAY - timedelta(days=1)), HOM_NAY) is True


def test_han_o_tuong_lai_thi_con_xem_duoc():
    assert han.het_han_xem(_doc(HOM_NAY + timedelta(days=30)), HOM_NAY) is False


def test_khong_co_van_ban_thi_khong_chan():
    """Tệp của YCMH/ĐMH/bình luận đi qua cùng hàm — không được dính hạn nào."""
    assert han.het_han_xem(None, HOM_NAY) is False


def test_entity_khac_thi_khong_tra_ra_van_ban(db):
    assert han.van_ban_cua_dinh_kem(db, "purchase_request", 1) is None
    assert han.van_ban_cua_dinh_kem(db, "comment", 1) is None


def test_chan_neu_het_han_nem_403_kem_ngay(db, seed, monkeypatch):
    """403 chứ không 404: tệp có thật, người này có quyền — chỉ là HẾT GIỜ.

    404 là nói dối, và người dùng sẽ đi báo mất tệp.
    """
    doc = Document(id=99, title="Bảng lương kỳ 8",
                   attachment_view_until=date.today() - timedelta(days=1))
    monkeypatch.setattr(han, "van_ban_cua_dinh_kem", lambda *a, **kw: doc)

    with pytest.raises(HTTPException) as loi:
        han.chan_neu_het_han(db, han.ENTITY_DINH_KEM_VAN_BAN, 1)

    assert loi.value.status_code == 403
    #  Câu báo phải nói RÕ NGÀY — "không xem được" trơ trọi thì người dùng đi hỏi
    #  vòng quanh xem ai khóa mất tệp.
    assert doc.attachment_view_until.strftime("%d/%m/%Y") in loi.value.detail


def test_con_han_thi_khong_chan(db, monkeypatch):
    doc = Document(id=99, title="Còn hạn",
                   attachment_view_until=date.today() + timedelta(days=1))
    monkeypatch.setattr(han, "van_ban_cua_dinh_kem", lambda *a, **kw: doc)

    han.chan_neu_het_han(db, han.ENTITY_DINH_KEM_VAN_BAN, 1)  # không ném gì
