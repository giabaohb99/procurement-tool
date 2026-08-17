"""Bài nghiệm thu Phase 1 số 3 (`02` mục 5), nửa vế hay bị bỏ quên:

> Đổi sang năm mới → sổ theo năm đếm lại từ 1, **sổ mã tài liệu bất biến thì
> không**.

Vế đầu đã có ở `test_number_sequence.py`. Vế sau chưa từng được kiểm, và đúng chỗ
đó có lỗi: `next_number()` đặt lại bộ đếm mỗi khi `row.year` lệch năm truyền vào,
trong khi bộ đếm mã tài liệu bất biến (`doc:DEGO:QC`) và sổ tắt `reset_yearly`
(`book:SD002`) đều **không có năm trong khóa** — một dòng dùng cho mọi năm.

Hậu quả nếu không vá: 1/1 hàng năm, văn bản đầu tiên nhận lại `DEGO-QC-001` —
số đã cấp cho một văn bản khác từ năm trước. `UNIQUE(doc_code)` chặn được việc
ghi, nên biểu hiện thực tế là **không ai cấp số được nữa** cho tới khi có người
sửa tay bộ đếm.
"""
from datetime import date

import pytest

from app.modules.company.model import Company
from app.modules.doc_catalog.book_model import DocumentBook
from app.modules.doc_catalog.model import DocType
from app.modules.doc_catalog.number_service import next_book_number
from app.modules.document import numbering
from app.modules.document.model import Document


@pytest.fixture()
def catalog(db):
    company = Company(code="CT", name="Công ty", issue_code="DEGO", is_active=True)
    db.add(company)
    db.flush()
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2,
                       is_active=True)
    db.add(doc_type)
    db.commit()
    return company, doc_type


def _cap_ma(db, company, doc_type, title: str, year: int) -> Document:
    doc = Document(title=title, doc_type_id=doc_type.id, company_id=company.id,
                   owner_employee_id=1)
    db.add(doc)
    db.flush()
    numbering.assign(db, doc, doc_type, year)
    db.commit()
    db.refresh(doc)
    return doc


def test_ma_tai_lieu_bat_bien_dem_tiep_qua_nam_moi(db, catalog):
    company, doc_type = catalog

    a = _cap_ma(db, company, doc_type, "Quy chế lương", 2026)
    b = _cap_ma(db, company, doc_type, "Quy chế công tác phí", 2026)
    assert (a.doc_code, b.doc_code) == ("DEGO-QC-001", "DEGO-QC-002")

    #  Sang năm mới. Mã tài liệu theo văn bản suốt đời, KHÔNG đếm lại.
    c = _cap_ma(db, company, doc_type, "Quy chế đào tạo", 2027)
    assert c.doc_code == "DEGO-QC-003"


def test_xem_truoc_va_cap_that_khong_lech_nhau_qua_nam(db, catalog):
    """`peek` không đếm lại theo năm — `assign` cũng phải vậy, nếu không hai màn
    hình cùng nói hai số khác nhau ngay đầu tháng Giêng."""
    company, doc_type = catalog
    _cap_ma(db, company, doc_type, "Quy chế lương", 2026)

    xem_truoc = numbering.peek(db, doc_type, company.id, None, date(2027, 1, 2))
    that = _cap_ma(db, company, doc_type, "Quy chế công tác phí", 2027).doc_code
    assert xem_truoc == that == "DEGO-QC-002"


def test_so_tat_reset_yearly_cung_dem_tiep_qua_nam(db):
    """Cùng một lỗi ở sổ văn bản: khóa đã bỏ năm ra, nhưng bộ đếm vẫn tự reset."""
    book = DocumentBook(code="SD002", name="Sổ nội bộ", kind=3, company_id=1,
                        reset_yearly=False, start_no=1, is_active=True)
    db.add(book)
    db.commit()

    assert next_book_number(db, book, 2026) == 1
    assert next_book_number(db, book, 2026) == 2
    assert next_book_number(db, book, 2027) == 3


def test_so_bat_reset_yearly_van_dem_lai_tu_dau(db):
    """Vế còn lại phải giữ nguyên — sổ theo năm thì sang năm là số 1."""
    book = DocumentBook(code="SD001", name="Sổ công văn đến", kind=1, company_id=1,
                        reset_yearly=True, start_no=1, is_active=True)
    db.add(book)
    db.commit()

    assert next_book_number(db, book, 2026) == 1
    assert next_book_number(db, book, 2026) == 2
    assert next_book_number(db, book, 2027) == 1
