"""P6-2 (bao-CR-280) — khối phương án của phiếu gộp gợi ý / khóa theo mã hàng (doc/erp/12 §P6-2).

Hai luật cần khóa bằng test:

1. `choose_option` — dòng CHƯA có mã: chọn phương án mang mã thì mã điền lên dòng;
   BỎ CHỌN thì gỡ lại đúng mã do phương án đó điền (không gỡ thì bộ lọc theo mã
   khóa chặt các phương án khác, dòng kẹt vĩnh viễn với lựa chọn cũ). Dòng ĐÃ có
   mã khác thì chặn 400 — giao diện đã lọc sẵn, chốt này chống gọi API thẳng.
2. `code_visible_options` + `_out_result` — dòng đã có mã chỉ trả phương án khớp mã,
   nhưng GIỮ phương án chưa gắn mã và phương án đang chọn (dữ liệu cũ lệch mã mà
   giấu đi thì dòng hiện 'chưa chọn' trong khi DB đã chọn).
"""
import pytest
from fastapi import HTTPException

from app.modules.survey_request import service
from app.modules.survey_request.controller import _out_result
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption)


def _sr_line(db, product_code: str = "", **kw):
    s = SurveyRequest(code=kw.pop("code", "YCBG-P62"), status="survey_done")
    db.add(s)
    db.commit()
    ln = SurveyRequestLine(survey_request_id=s.id, item_group="Thùng",
                           product_code=product_code, **kw)
    db.add(ln)
    db.commit()
    return s, ln


def _opt(db, line_id: int, public_id: int, code: str = "", chosen: bool = False):
    o = SurveyRequestOption(survey_request_line_id=line_id, public_id=public_id,
                            system_product_code=code, is_chosen=chosen)
    db.add(o)
    db.commit()
    return o


# ───────────────────────── choose_option: điền / gỡ / chặn mã ─────────────────────────

def test_chon_phuong_an_co_ma_dien_ma_len_dong_chua_co_ma(db, seed):
    _s, ln = _sr_line(db)
    o = _opt(db, ln.id, 1, code="VT-P62-01")

    service.choose_option(db, ln.id, o.id, user_id=1)

    db.refresh(ln)
    assert ln.product_code == "VT-P62-01"


def test_bo_chon_go_lai_ma_do_chinh_phuong_an_do_dien(db, seed):
    _s, ln = _sr_line(db)
    o = _opt(db, ln.id, 1, code="VT-P62-01")
    service.choose_option(db, ln.id, o.id, user_id=1)   # chọn -> điền mã

    service.choose_option(db, ln.id, o.id, user_id=1)   # bấm lại -> bỏ chọn

    db.refresh(ln)
    db.refresh(o)
    assert not o.is_chosen
    assert ln.product_code == "", "mã do phương án điền phải gỡ theo, kẻo bộ lọc khóa dòng"


def test_bo_chon_khong_go_ma_khac_ma_cua_phuong_an(db, seed):
    """Dòng mang mã A, phương án đang chọn KHÔNG gắn mã — bỏ chọn không được đụng mã dòng."""
    _s, ln = _sr_line(db, product_code="VT-GIU-NGUYEN")
    o = _opt(db, ln.id, 1, code="", chosen=True)

    service.choose_option(db, ln.id, o.id, user_id=1)   # bỏ chọn

    db.refresh(ln)
    assert ln.product_code == "VT-GIU-NGUYEN"


def test_dong_da_co_ma_chan_phuong_an_mang_ma_khac(db, seed):
    _s, ln = _sr_line(db, product_code="VT-A")
    o = _opt(db, ln.id, 1, code="VT-B")

    with pytest.raises(HTTPException) as e:
        service.choose_option(db, ln.id, o.id, user_id=1)
    assert e.value.status_code == 400

    db.refresh(o)
    assert not o.is_chosen


def test_dong_da_co_ma_van_chon_duoc_phuong_an_chua_gan_ma(db, seed):
    """Phương án chưa gắn mã không phải là sai mã — mã dòng vẫn là mã chốt."""
    _s, ln = _sr_line(db, product_code="VT-A")
    o = _opt(db, ln.id, 1, code="")

    service.choose_option(db, ln.id, o.id, user_id=1)

    db.refresh(ln)
    db.refresh(o)
    assert o.is_chosen and ln.product_code == "VT-A"


def test_chon_phuong_an_khop_dung_ma_dong(db, seed):
    _s, ln = _sr_line(db, product_code="VT-A")
    o = _opt(db, ln.id, 1, code="VT-A")

    service.choose_option(db, ln.id, o.id, user_id=1)

    db.refresh(o)
    assert o.is_chosen


# ───────────────────── code_visible_options + _out_result: lọc theo mã ─────────────────────

def test_loc_phuong_an_theo_ma_dong(db, seed):
    _s, ln = _sr_line(db, product_code="VT-A")
    khop = _opt(db, ln.id, 1, code="VT-A")
    _opt(db, ln.id, 2, code="VT-B")                      # lệch mã -> ẩn
    chua_ma = _opt(db, ln.id, 3, code="")                # chưa gắn mã -> giữ
    lech_dang_chon = _opt(db, ln.id, 4, code="VT-C", chosen=True)  # lệch nhưng ĐANG CHỌN -> giữ

    ids = {o.id for o in service.code_visible_options(ln, service.valid_options_of(db, ln.id))}
    assert ids == {khop.id, chua_ma.id, lech_dang_chon.id}


def test_dong_chua_co_ma_khong_loc_gi(db, seed):
    _s, ln = _sr_line(db)
    a = _opt(db, ln.id, 1, code="VT-A")
    b = _opt(db, ln.id, 2, code="VT-B")

    ids = {o.id for o in service.code_visible_options(ln, service.valid_options_of(db, ln.id))}
    assert ids == {a.id, b.id}


def test_out_result_an_phuong_an_lech_ma_va_dem_theo_ban_da_loc(db, seed):
    s, ln = _sr_line(db, product_code="VT-A")
    _opt(db, ln.id, 1, code="VT-A")
    _opt(db, ln.id, 2, code="VT-B")

    dong = _out_result(db, s)["lines"][0]
    assert [o["public_id"] for o in dong["options"]] == [1]
    assert dong["option_count"] == 1, "đếm phải theo danh sách ĐÃ LỌC — lệch nhau là FE hiện số ma"
