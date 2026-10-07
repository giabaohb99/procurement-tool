"""Đọc số tiền thành chữ (Python) — PHẢI khớp bản TS `number-to-vietnamese-words.ts`.

Bộ ca dùng CHUNG số liệu với `frontend-v2/src/shared/utils/number-to-vietnamese-words.test.ts`.
Lệch ở bên nào thì bản in HĐ ra khác màn hình — sửa cả hai bên.
"""
import pytest

from app.core.vn_number_words import MAX_AMOUNT, read_amount_vi

CASES = [
    (1_000, "Một nghìn đồng chẵn"),
    (4_760_000, "Bốn triệu bảy trăm sáu mươi nghìn đồng chẵn"),
    (1_000_000_000, "Một tỷ đồng chẵn"),
    (1_050_000, "Một triệu không trăm năm mươi nghìn đồng chẵn"),
    (1_001, "Một nghìn không trăm lẻ một đồng chẵn"),
    (21, "Hai mươi mốt đồng chẵn"),
    (25, "Hai mươi lăm đồng chẵn"),
    (15, "Mười lăm đồng chẵn"),
    (105, "Một trăm lẻ năm đồng chẵn"),
    (4_760_000.08, "Bốn triệu bảy trăm sáu mươi nghìn đồng chẵn"),
    (1_000.6, "Một nghìn không trăm lẻ một đồng chẵn"),
    (1_234_567_890,
     "Một tỷ hai trăm ba mươi bốn triệu năm trăm sáu mươi bảy nghìn tám trăm chín mươi đồng chẵn"),
    (21_000_000, "Hai mươi mốt triệu đồng chẵn"),
    (15_000, "Mười lăm nghìn đồng chẵn"),
    (105_000, "Một trăm lẻ năm nghìn đồng chẵn"),
    (15_000_000, "Mười lăm triệu đồng chẵn"),
    (1, "Một đồng chẵn"),
    (5, "Năm đồng chẵn"),
    (10, "Mười đồng chẵn"),
    (101, "Một trăm lẻ một đồng chẵn"),
    (1_000_001, "Một triệu không trăm lẻ một đồng chẵn"),
]


@pytest.mark.parametrize("amount,expected", CASES)
def test_khop_ban_ts(amount, expected):
    assert read_amount_vi(amount) == expected


@pytest.mark.parametrize("bad", [0, -5_000, float("nan"), None, "", "abc", 0.4, [], float("-inf")])
def test_khong_am_hong_ra_khong_dong(bad):
    """0, âm, NaN, None, chuỗi rác, dưới nửa đồng → «Không đồng», không ném lỗi."""
    assert read_amount_vi(bad) == "Không đồng"


def test_so_nguyen_chuoi_va_decimal_nhu_nhau():
    from decimal import Decimal
    assert read_amount_vi("15000000") == read_amount_vi(Decimal("15000000")) == read_amount_vi(15_000_000)


def test_muoi_mu_12_doc_dung_bac():
    """10^12 = «một nghìn tỷ» — không được rơi mất bậc."""
    assert read_amount_vi(10**12) == "Một nghìn tỷ đồng chẵn"


def test_tran_so_chan_thay_vi_doc_bay():
    assert read_amount_vi(MAX_AMOUNT).startswith("Chín trăm chín mươi chín nghìn tỷ")
    with pytest.raises(ValueError):
        read_amount_vi(MAX_AMOUNT + 1)
    with pytest.raises(ValueError):
        read_amount_vi(10**30)
