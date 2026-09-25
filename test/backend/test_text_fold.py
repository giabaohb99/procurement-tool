"""`app/core/text_fold.py` — gập dấu tiếng Việt + hạ chữ thường.

Tách khỏi `help_center/service.py._fold` (phase 07 tìm kiếm toàn văn văn bản,
duoc-CR-477). Hai điều BẮT BUỘC đúng, cả hai đều bị `document/search_service.py`
trông cậy vào:

1. Kết quả không phân biệt hoa/thường/dấu.
2. Độ dài chuỗi gập LUÔN bằng độ dài chuỗi gốc (offset ánh xạ 1:1) — vỡ điều
   này thì đoạn trích tìm kiếm cắt sai chỗ.
"""
import unicodedata

from app.core.text_fold import fold, fold_char


def test_d_va_D_gap_ve_d():
    assert fold("Đ") == "d"
    assert fold("đ") == "d"
    assert fold("Đà Nẵng") == "da nang"


def test_khong_phan_biet_hoa_thuong():
    assert fold("Quyết Định") == fold("quyết định") == fold("QUYẾT ĐỊNH")


def test_nfc_va_nfd_gap_ra_cung_mot_ket_qua():
    """`"à"` (NFC, 1 mã) và `"a" + "̀"` (NFD, dấu huyền RỜI, 2 mã) phải
    gập ra CÙNG một chữ — người gõ từ bàn phím/hệ điều hành khác nhau có thể
    gửi lên một trong hai dạng, chỉ mục tìm kiếm không được phân biệt."""
    nfc = "à"
    nfd = unicodedata.normalize("NFD", "à")
    assert nfc != nfd, "tiền đề: hai chuỗi phải THẬT SỰ khác nhau ở đầu vào"
    assert fold(nfc) == fold(nfd) == "a"


def test_to_hop_dau_nfd_phuc_tap():
    #  "ệ" NFD = "e" + dấu mũ (U+0302) + dấu nặng (U+0323) — hai dấu combining
    #  chồng lên nhau, trường hợp dễ vỡ nhất của một bộ gập dấu viết tay.
    e_mu_nang_nfd = unicodedata.normalize("NFD", "ệ")
    assert fold(e_mu_nang_nfd) == "e"
    assert fold("Việt Nam") == "viet nam"


def test_do_dai_chuoi_gap_luon_bang_do_dai_chuoi_goc():
    """Điều kiện offset — `search_service._snippet` dựa vào đúng bất biến này."""
    mau = "Đây là Đà Nẵng — thành phố biển miền Trung, 2026!"
    assert len(fold(mau)) == len(mau)


def test_moi_ky_tu_gap_ra_dung_mot_ky_tu():
    for ch in "đĐàÀâẤậệôỐộưỨựĂắẰ123 -_.,!?":
        assert len(fold_char(ch)) == 1, f"{ch!r} gập ra khác đúng 1 ký tự"


def test_chuoi_rong_va_none_khong_loi():
    assert fold("") == ""
    assert fold(None) == ""


def test_chu_khong_dau_giu_nguyen():
    assert fold("ABC 123 xyz") == "abc 123 xyz"
