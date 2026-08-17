"""Bộ đếm cấp số của sổ văn bản.

Số hiệu trùng nghĩa là hai văn bản cùng một số; số nhảy cóc nghĩa là sổ thủng lỗ
không giải thích được khi thanh tra. Cả hai đều không sửa được sau khi văn bản đã
ban hành, nên phần này phải có kiểm thử.

⚠️ **Bài kiểm quan trọng nhất KHÔNG nằm ở đây.** Chuyện "100 người bấm cùng lúc
vẫn ra 100 số liên tiếp" phụ thuộc `SELECT ... FOR UPDATE`, mà SQLite (bộ kiểm
thử này chạy trên SQLite in-memory) khóa cả tệp nên không mô phỏng được cạnh
tranh thật. Bài đó chạy trên MySQL thật bằng
`test/backend/check_number_sequence_concurrency.py`.
"""
from datetime import date

import pytest

from app.modules.doc_catalog.book_model import DocumentBook, NumberSequence
from app.modules.doc_catalog.number_service import (book_scope_key, format_book_number,
                                                    next_number, peek_book_number)


@pytest.fixture()
def book(db):
    obj = DocumentBook(code="SD001", name="Sổ công văn đến", kind=1, company_id=1,
                       number_prefix="CVĐ", reset_yearly=True, start_no=1)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def test_cap_so_tang_dan_lien_tuc(db, book):
    key = book_scope_key(book.code, 2026)
    assert [next_number(db, key, 2026) for _ in range(5)] == [1, 2, 3, 4, 5]


def test_sang_nam_moi_dem_lai_tu_dau(db, book):
    key_2026 = book_scope_key(book.code, 2026)
    for _ in range(3):
        next_number(db, key_2026, 2026)

    # Sổ có reset theo năm → khóa đổi theo năm, bộ đếm 2027 là dòng mới.
    key_2027 = book_scope_key(book.code, 2027)
    assert key_2027 != key_2026
    assert next_number(db, key_2027, 2027) == 1


def test_so_khong_reset_thi_dem_tiep_qua_nam(db):
    """Sổ tắt `reset_yearly` dùng chung một dòng cho mọi năm."""
    key = book_scope_key("SD002", 2026, reset_yearly=False)
    assert key == "book:SD002"
    assert next_number(db, key, 2026, reset_yearly=False) == 1
    #  Khóa đã bỏ năm ra, nhưng chừng đó chưa đủ: phải nói thẳng cho bộ đếm biết
    #  là không đếm lại, nếu không nó thấy `row.year` lệch và tự đặt về đầu.
    assert next_number(db, key, 2027, reset_yearly=False) == 2


def test_start_no_ap_dung_khi_chuyen_tu_so_giay(db):
    """Sổ giấy đã tới số 47 thì sổ điện tử bắt đầu từ 48."""
    key = book_scope_key("SD003", 2026)
    assert next_number(db, key, 2026, start_no=48) == 48
    assert next_number(db, key, 2026, start_no=48) == 49


def test_xem_truoc_khong_chiem_so(db, book):
    year = date.today().year
    assert peek_book_number(db, book, year) == 1
    # Gọi bao nhiêu lần cũng không đẩy bộ đếm lên.
    assert peek_book_number(db, book, year) == 1
    assert db.query(NumberSequence).count() == 0

    next_number(db, book_scope_key(book.code, year), year)
    assert peek_book_number(db, book, year) == 2


def test_khoa_scope_key_la_duy_nhat(db):
    """Lớp chặn cuối cùng nằm ở tầng dữ liệu, độc lập với mã nguồn."""
    db.add(NumberSequence(scope_key="book:SD009:2026", year=2026, current_no=1))
    db.commit()

    db.add(NumberSequence(scope_key="book:SD009:2026", year=2026, current_no=1))
    with pytest.raises(Exception):
        db.commit()
    db.rollback()


def test_chuoi_so_hien_thi(db, book):
    assert format_book_number(book, 8, 2026) == "CVĐ 08/2026"
    book.number_prefix = ""
    assert format_book_number(book, 12, 2026) == "12/2026"
