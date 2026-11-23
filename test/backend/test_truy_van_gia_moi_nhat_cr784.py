"""duoc-CR-784 — `latest_priced_by_code`: n lần mua có giá gần nhất + số gộp theo mã trong MỘT câu SQL, không hàm cửa sổ.

Chạy trên SQLite nên kiểm cách CHUẨN; cách LATERAL của MySQL được (a) kiểm hình dạng SQL sinh ra, (b) đối chiếu kết quả với cách
chuẩn trên MySQL thật khi đặt biến môi trường `PKG784_MYSQL_URL` (bài đối chiếu bên dưới, bỏ qua khi không đặt)."""
import os
import random
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import case, create_engine, func
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Session

from app.modules.product_price.latest_priced_query import latest_priced_by_code, uses_lateral
from app.modules.product_price.model import ProductPriceLedger as L
from lich_lam_viec_factory import count_queries
from so_gia_factory_cr784 import add_ledger

PRICED = [L.price > 0]


def _ids(entry):
    return [r.id for r in entry.rows]


def _latest(db, n=2, codes=None, **kw):
    return latest_priced_by_code(db, n, codes=codes, rank_conds=kw.pop("rank_conds", PRICED), strategy="portable", **kw)


def test_may_dong_cung_ngay_vuot_n_van_lay_dung_n_theo_doc_id_roi_id(db):
    rows = [add_ledger(db, "A", 100 + i, "2026-03-01", doc_id=d) for i, d in enumerate((5, 9, 9, 2, 7, 9))]
    older = add_ledger(db, "A", 1, "2026-01-01", doc_id=99)
    out = _latest(db, 3)["A"]
    # cùng ngày: doc_id lớn trước (9, 9, 9), cùng doc_id thì id lớn trước → ba dòng doc_id = 9, id giảm
    assert _ids(out) == [rows[5].id, rows[2].id, rows[1].id]
    assert older.id not in _ids(out)


def test_it_hon_n_dong_lay_het_va_dong_gia_0_khong_xep_hang_nhung_van_dem_khi_khong_loc_gia(db):
    add_ledger(db, "A", 10, "2026-01-01")
    zero = add_ledger(db, "A", 0, "2026-05-01")
    add_ledger(db, "B", 0, "2026-05-01")                        # chỉ có giá 0
    out = _latest(db, 5, agg_cols=[func.count(L.id), func.max(L.price_date)], agg_conds=[])
    assert zero.id not in _ids(out["A"]) and len(out["A"].rows) == 1
    assert out["A"].stats == (2, date(2026, 5, 1))              # đếm cả dòng giá 0, ngày cuối cũng tính nó
    assert out["B"].rows == [] and out["B"].stats[0] == 1       # có mặt nhờ số gộp nhưng không có lần mua có giá


def test_pham_vi_phap_nhan_duoc_chuyen_sang_ca_truy_van_con_lan_phan_nhom(db):
    add_ledger(db, "A", 100, "2026-01-01", company_id=1)
    add_ledger(db, "A", 200, "2026-02-01", company_id=1)
    other = add_ledger(db, "A", 999, "2026-09-01", company_id=2)       # mới nhất nhưng của pháp nhân khác
    mine = [L.price > 0, L.company_id.in_([1])]
    out = _latest(db, 1, rank_conds=mine, agg_conds=mine, agg_cols=[func.count(L.id)])["A"]
    assert out.rows[0].price == 200 and out.stats == (2,) and other.id not in _ids(out)
    both = _latest(db, 1, rank_conds=[L.price > 0, L.company_id.in_([1, 2])])["A"]
    assert both.rows[0].price == 999


def test_che_do_nhe_khong_co_so_gop_va_gioi_han_ma(db):
    for code in "ABC":
        add_ledger(db, code, 10, "2026-01-01")
    assert {c: e.stats for c, e in _latest(db).items()} == {"A": (), "B": (), "C": ()}
    assert set(_latest(db, codes={"A", "C", "KHONG_CO"})) == {"A", "C"}
    assert _latest(db, codes=set()) == {}


def test_ma_la_va_nhieu_ma_khong_vo_loi(db):
    add_ledger(db, "A'; DROP TABLE tab_product_price_ledger; --", 5, "2026-01-01")
    add_ledger(db, "Ó-Đ", 6, "2026-01-01")
    out = _latest(db, codes={"A'; DROP TABLE tab_product_price_ledger; --", "Ó-Đ", *[f"M{i}" for i in range(900)]})
    assert set(out) == {"A'; DROP TABLE tab_product_price_ledger; --", "Ó-Đ"}


def test_n_khong_hop_le_bi_chan(db):
    with pytest.raises(ValueError):
        latest_priced_by_code(db, 0, codes=None, rank_conds=PRICED)


def test_moi_cach_deu_la_mot_cau_sql_khong_ham_cua_so(db):
    for i in range(40):
        add_ledger(db, f"M{i % 8}", 10 + i, "2026-01-01")
    _, sqls = count_queries(db, lambda: _latest(db, 5, agg_cols=[func.count(L.id)], agg_conds=PRICED))
    assert len(sqls) == 1 and "row_number" not in sqls[0].lower() and " over (" not in sqls[0].lower()


def test_cach_lateral_sinh_sql_lateral_khong_ham_cua_so_va_sqlite_khong_dung_no(db):
    assert uses_lateral(db) is False                                  # bài kiểm chạy SQLite → cách chuẩn
    captured: list[str] = []

    class Spy:
        """Bắt câu SQL biên dịch cho MySQL mà không chạy nó."""
        def get_bind(self):
            return db.get_bind()

        def execute(self, stmt):
            captured.append(str(stmt.compile(dialect=mysql.dialect())))
            return []

    latest_priced_by_code(Spy(), 5, codes={"A"}, rank_conds=PRICED, agg_conds=PRICED, agg_cols=[func.count(L.id)],
                          strategy="lateral")
    sql = captured[0].upper()
    assert "LATERAL" in sql and "ROW_NUMBER" not in sql and "LIMIT" in sql


def test_model_va_migration_cung_khai_chi_muc_phu():
    names = {ix.name: [c.name for c in ix.columns] for ix in L.__table__.indexes}
    # `source_type` thêm ở cuối bởi migration `misa784` (điều kiện mốc sổ Misa đọc được từ chỉ mục phủ)
    assert names["ix_ppl_code_latest"] == ["product_code", "price_date", "doc_id", "id", "price", "company_id", "source_type"]
    assert "ix_ppl_code_date" not in names                          # chỉ mục cũ đã được thay
    root = Path(__file__).resolve().parents[2]           # gốc repo (máy chủ) hoặc /app (trong container, nơi `migrations/` nằm ngay dưới)
    migration = next(p for p in (root / "backend/migrations/versions", root / "migrations/versions")
                     if p.is_dir()) / "pkgcost784_tac_dong_gia_bao_bi.py"
    text = migration.read_text(encoding="utf-8")
    assert '"ix_ppl_code_latest"' in text and '"ix_ppl_code_date"' not in text.replace("`ix_ppl_code_date`", "")
    assert '["product_code", "price_date", "doc_id", "id", "price", "company_id"]' in text.replace("\n", " ").replace("  ", " ")
    misa = migration.with_name("misa784_nguon_so_misa_ten_ncc.py").read_text(encoding="utf-8")
    assert 'down_revision: Union[str, None] = "pkgcost784"' in misa and '[*OLD_COLUMNS, "source_type"]' in misa


@pytest.mark.skipif(not os.environ.get("PKG784_MYSQL_URL"), reason="chỉ chạy khi có MySQL thật có sổ giá (PKG784_MYSQL_URL)")
@pytest.mark.parametrize("n", [1, 2, 5, 10])
def test_doi_chieu_lateral_va_chuan_tren_mysql_that(n):
    """Cách LATERAL (MySQL) phải cho đúng từng id / số gộp như cách chuẩn, có và không có phạm vi pháp nhân."""
    engine = create_engine(os.environ["PKG784_MYSQL_URL"])
    with Session(engine) as session:
        assert uses_lateral(session), "cần MySQL 8.0.14+"
        codes = [c for (c,) in session.query(L.product_code).distinct().limit(400).all()]
        sample = set(random.Random(n).sample(codes, min(120, len(codes))))
        for scope in (None, [L.company_id.in_([1, 2])]):
            conds = [L.price > 0, *(scope or [])]
            ranged = case((L.price > 0, L.price))
            kw = {"codes": sample, "rank_conds": conds, "agg_conds": scope or [],
                  "agg_cols": [func.count(L.id), func.max(L.price_date), func.min(ranged), func.max(ranged)]}
            a = latest_priced_by_code(session, n, strategy="portable", **kw)
            b = latest_priced_by_code(session, n, strategy="lateral", **kw)
            assert set(a) == set(b) and all(a[c].stats == b[c].stats and _ids(a[c]) == _ids(b[c]) for c in a)
