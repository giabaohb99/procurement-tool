"""D05 — bãi bỏ văn bản thì SỐ CỦA NÓ KHÔNG quay lại cho văn bản sau dùng.

Đây là một trong ba bài nghiệm thu của Phase 1 (`02` mục 5). Hai bài kia:
đếm lại theo năm ở `test_number_sequence.py`, và 100 kết nối cùng lúc ở
`check_number_sequence_concurrency.py` (chạy trên MySQL thật).

Vì sao phải có bài này: cách hỏng tự nhiên nhất là ai đó "dọn dẹp" bằng cách trừ
bộ đếm khi hủy, hoặc đổi `assign()` sang `MAX(seq_no) + 1`. Cả hai đều làm số của
văn bản đã bãi bỏ được cấp lại — mà số đó đã phát ra ngoài rồi, nên hai văn bản
khác nhau cùng mang một số hiệu.
"""
from datetime import date

import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import numbering
from app.modules.document.model import STATUS_DRAFT, STATUS_EFFECTIVE, Document
from app.modules.document.service import revoke

YEAR = 2026


@pytest.fixture()
def catalog(db):
    company = Company(code="CT", name="Công ty", issue_code="DEGO", is_active=True)
    db.add(company)
    db.flush()
    doc_type = DocType(code="TB", name="Thông báo", id_scheme=2, number_when=2,
                       is_active=True)
    db.add(doc_type)
    db.commit()
    return company, doc_type


def _cap_so(db, company, doc_type, title: str) -> Document:
    """Tạo một văn bản rồi cấp số thật cho nó."""
    doc = Document(title=title, doc_type_id=doc_type.id, company_id=company.id,
                   owner_employee_id=1, status=STATUS_DRAFT)
    db.add(doc)
    db.flush()
    numbering.assign(db, doc, doc_type, YEAR)
    db.commit()
    db.refresh(doc)
    return doc


def test_bai_bo_van_ban_thi_so_cua_no_khong_duoc_cap_lai(db, catalog):
    company, doc_type = catalog

    thu_nhat = _cap_so(db, company, doc_type, "Thông báo nghỉ lễ")
    thu_hai = _cap_so(db, company, doc_type, "Thông báo họp")
    assert (thu_nhat.seq_no, thu_hai.seq_no) == (1, 2)

    so_cu = thu_nhat.issue_number
    thu_nhat.status = STATUS_EFFECTIVE
    db.commit()
    revoke(db, thu_nhat, reason="ban hành nhầm", actor=9)

    #  Số nằm lại trong sổ: tra sổ vẫn ra "số này từng cấp cho văn bản gì".
    assert thu_nhat.issue_number == so_cu
    assert thu_nhat.seq_no == 1

    #  Và văn bản tiếp theo đi tiếp từ 3, không nhặt lại số 1.
    thu_ba = _cap_so(db, company, doc_type, "Thông báo lịch trực")
    assert thu_ba.seq_no == 3
    assert thu_ba.issue_number != so_cu


def test_bai_bo_lan_hai_bi_tu_choi(db, catalog):
    """Bấm bãi bỏ hai lần không được sinh ra thao tác thứ hai trong sổ nhật ký."""
    company, doc_type = catalog
    doc = _cap_so(db, company, doc_type, "Thông báo nghỉ lễ")
    doc.status = STATUS_EFFECTIVE
    db.commit()
    revoke(db, doc, reason="ban hành nhầm", actor=9)

    with pytest.raises(HTTPException):
        revoke(db, doc, reason="bấm nhầm lần nữa", actor=9)


def test_cap_so_lai_tren_van_ban_da_co_so_thi_khong_lam_gi(db, catalog):
    """`assign()` gọi lại phải im lặng: số đã phát ra ngoài, cấp lại là ra hai số."""
    company, doc_type = catalog
    doc = _cap_so(db, company, doc_type, "Thông báo nghỉ lễ")
    so_cu, seq_cu = doc.issue_number, doc.seq_no

    numbering.assign(db, doc, doc_type, YEAR)
    db.commit()

    assert (doc.issue_number, doc.seq_no) == (so_cu, seq_cu)
    #  Bộ đếm cũng không nhích: văn bản kế tiếp vẫn là số 2.
    assert _cap_so(db, company, doc_type, "Thông báo họp").seq_no == 2


def test_ngay_bai_bo_dong_luon_ngay_het_hieu_luc(db, catalog):
    company, doc_type = catalog
    doc = _cap_so(db, company, doc_type, "Thông báo nghỉ lễ")
    doc.status = STATUS_EFFECTIVE
    db.commit()

    revoke(db, doc, reason="ban hành nhầm", actor=9)
    assert doc.expire_date == date.today()
