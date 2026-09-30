"""bao-CR-535 — seed văn thư không được đẻ lại công ty trùng mã số thuế mỗi lần deploy.

bao-CR-532 gộp «DEGO HOLDING» vào «DEGO» (cùng MST 1801722464) rồi xóa. Nhưng
`seed_document_phase1` chạy ở MỖI lần khởi động (`seed_prod`) và danh sách
`DOCUMENT_COMPANIES` còn dòng «DEGO HOLDING», nên deploy dev xong là nó mọc lại (id 17).
"""
from app.modules.company.model import Company
from app.seed import seed_document_phase1
from app.seed_data.document_phase1 import DOCUMENT_COMPANIES

MST = "1801722464"


def _tax_key(value: str) -> str:
    return "".join((value or "").split()).upper()


def test_seed_data_has_no_duplicate_tax_code():
    keys = [_tax_key(row["tax_code"]) for row in DOCUMENT_COMPANIES if _tax_key(row["tax_code"])]
    assert len(keys) == len(set(keys))
    assert "DEGO HOLDING" not in {row["code"] for row in DOCUMENT_COMPANIES}


def test_seed_does_not_recreate_merged_duplicate(db, seed):
    seed_document_phase1(db)
    seed_document_phase1(db)
    assert db.query(Company).filter(Company.tax_code == MST).count() == 1
    assert db.query(Company).filter(Company.code == "DEGO HOLDING").count() == 0


def test_seed_skips_company_whose_tax_code_belongs_to_another_code(db, seed, monkeypatch):
    """Lỡ danh sách seed lại có một dòng trùng MST với công ty đang có (khác mã) — không tạo."""
    db.add(Company(code="DEGO", name="CÔNG TY TNHH DEGO HOLDING", tax_code=f" {MST} ", is_active=True))
    db.commit()
    extra = {"code": "DEGO COPY", "name": "Bản trùng", "tax_code": MST,
             "issue_code": "DEGOCOPY", "short_name": "Copy", "level": 1}
    monkeypatch.setattr("app.seed.DOCUMENT_COMPANIES", [*DOCUMENT_COMPANIES, extra])
    seed_document_phase1(db)
    assert db.query(Company).filter(Company.code == "DEGO COPY").count() == 0
