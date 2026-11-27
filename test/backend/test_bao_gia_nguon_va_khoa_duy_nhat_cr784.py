"""duoc-CR-784 phase 03 (migration `quotesrc784`, 25/11/2026) — báo giá VTBB có NGUỒN bắt buộc + khóa duy nhất (mã, NCC, ngày hiệu lực).

Phủ: (1) bộ mã `QuoteSourceType`, (2) form: tạo tay = (1, 0), schema không nhận nguồn từ người dùng, trùng khóa = 409 (tạo và sửa),
sửa giá / VAT / khóa đổi nguồn về nhập tay còn sửa ghi chú thì giữ, (3) nhập Excel: thêm = (2, đợt), đè giá = đổi sang đợt mới (C4),
chỉ đè ghi chú / chạy thử không đổi nguồn, (4) API trả `source_type` / `source_id` / `source_label`, (5) bài canh: cột NOT NULL không
mặc định phía CSDL, mọi nơi dựng `ProductPriceQuote(` ngoài CRUD đều truyền nguồn, (6) migration lên / xuống trên SQLite: điền lại
nguồn, dừng khi trùng khóa, giữ dữ liệu.
"""
import importlib.util
import re
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import openpyxl
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.exc import IntegrityError

from app.core import status_catalog
from app.core.packaging_price_codes import QUOTE_SOURCE_TYPE_LABELS, QuoteSourceType
from app.modules.import_tool.model import ImportBatch, ImportMode, ImportModule, ImportStatus
from app.modules.packaging_cost import quote_import
from app.modules.product_price.model import ProductPriceQuote
from app.modules.product_price.quote_limit_controller import QUOTE_DUPLICATE_MESSAGE
from app.modules.product_price.schema import QuoteCreate, QuoteOut
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from so_gia_factory_cr784 import add_products, add_quote

QUOTES = "/api/product-price-quotes"
MANUAL, EXCEL = int(QuoteSourceType.MANUAL), int(QuoteSourceType.EXCEL_IMPORT)
HEAD = ["Mã VTBB", "Đơn giá", "Ngày hiệu lực", "Mã NCC", "VAT (%)", "Ghi chú"]
ROOT = Path(__file__).resolve().parents[2]
MIGRATION = next((ROOT / "backend" / "migrations" / "versions").glob("quotesrc784_*.py"))


@pytest.fixture
def api(db, seed, cap_quyen, client_as):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_price_list", scope="all", read=True, create=True, write=True, delete=True)
    add_products(db, ("CPT0075", "Chai 1L", "Cái"), ("NAP0056", "Nắp", "Cái"))
    return client_as(db.get(User, seed.u_req_id))


def _post(api, **over):
    body = {"product_code": "CPT0075", "supplier_code": "", "price": 1000, "vat": 8, "valid_from": "2026-12-01", "note": "", **over}
    return api.post(QUOTES, json=body)


def _import(db, seed, rows, apply=True):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(HEAD)
    for r in rows:
        ws.append(r)
    batch = ImportBatch(module=int(ImportModule.PACKAGING_QUOTE), mode=int(ImportMode.APPLY if apply else ImportMode.DRY_RUN),
                        filename="bao-gia.xlsx", status=int(ImportStatus.RUNNING), created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(batch)
    db.commit()
    quote_import.run(db, batch, openpyxl.load_workbook(_save(wb)), apply=apply)
    db.refresh(batch)
    return batch


def _save(wb) -> BytesIO:
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _src(db, code="CPT0075"):
    db.expire_all()
    row = db.query(ProductPriceQuote).filter_by(product_code=code).one()
    return int(row.source_type), int(row.source_id)


# ── 1. Bộ mã ────────────────────────────────────────────────────────────────────
def test_bo_ma_nguon_bao_gia_dung_so_nhan_va_da_dang_ky():
    assert (QuoteSourceType.MANUAL, QuoteSourceType.EXCEL_IMPORT) == (1, 2)       # số đã cấp không đổi; 3 để dành cho YCBG
    assert QUOTE_SOURCE_TYPE_LABELS == {QuoteSourceType.MANUAL: "Nhập tay", QuoteSourceType.EXCEL_IMPORT: "Nhập Excel"}
    quote_set = status_catalog.all_sets()["quote_source_type"]
    assert [(o["value"], o["label"]) for o in quote_set.options] == [("1", "Nhập tay"), ("2", "Nhập Excel")]


# ── 2. Form ─────────────────────────────────────────────────────────────────────
def test_tao_tay_ghi_nhap_tay_id_0_va_api_tra_nguon_kem_nhan(api, db):
    res = _post(api)
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert (data["source_type"], data["source_id"], data["source_label"]) == (MANUAL, 0, "Nhập tay")
    assert _src(db) == (MANUAL, 0)
    listed = api.get(QUOTES).json()["data"]["items"][0]
    assert (listed["source_type"], listed["source_id"], listed["source_label"]) == (MANUAL, 0, "Nhập tay")
    assert api.get(f"{QUOTES}/{data['id']}").json()["data"]["source_type"] == MANUAL


def test_schema_ghi_khong_nhan_nguon_tu_nguoi_dung(api, db):
    assert "source_type" not in QuoteCreate.model_fields and "source_id" not in QuoteCreate.model_fields
    res = _post(api, source_type=EXCEL, source_id=99)                       # trường lạ bị bỏ qua, không lỗi, không ghi
    assert res.status_code == 201 and _src(db) == (MANUAL, 0)
    qid = res.json()["data"]["id"]
    assert api.patch(f"{QUOTES}/{qid}", json={"source_type": EXCEL, "source_id": 7, "note": "x"}).status_code == 200
    assert _src(db) == (MANUAL, 0)
    assert {"source_type", "source_id"} <= set(QuoteOut.model_fields)


def test_tao_trung_khoa_ma_ncc_ngay_la_409_khong_ghi_them_dong(api, db):
    assert _post(api, supplier_code="").status_code == 201
    dup = _post(api, supplier_code="", price=2000)
    assert dup.status_code == 409 and QUOTE_DUPLICATE_MESSAGE in dup.text and QUOTE_DUPLICATE_MESSAGE == "Đã có báo giá cùng mã, NCC và ngày hiệu lực"
    assert db.query(ProductPriceQuote).count() == 1
    #  Khác một thành phần của khóa thì vẫn được.
    assert _post(api, valid_from="2026-12-02").status_code == 201
    assert _post(api, product_code="NAP0056").status_code == 201
    assert db.query(ProductPriceQuote).count() == 3


def test_sua_sang_khoa_da_co_la_409_con_sua_giu_nguyen_khoa_thi_khong(api, db):
    a = _post(api).json()["data"]["id"]
    b = _post(api, valid_from="2026-12-02").json()["data"]["id"]
    res = api.patch(f"{QUOTES}/{b}", json={"valid_from": "2026-12-01"})
    assert res.status_code == 409 and QUOTE_DUPLICATE_MESSAGE in res.text
    assert api.patch(f"{QUOTES}/{a}", json={"valid_from": "2026-12-01", "price": 1500}).status_code == 200   # chính nó: không tự trùng


def test_sua_gia_vat_hoac_khoa_doi_nguon_ve_nhap_tay_sua_ghi_chu_thi_giu_nguon(api, db):
    qid = _post(api).json()["data"]["id"]
    for patch in ({"price": 1100}, {"vat": 10}, {"supplier_code": ""}, {"valid_from": "2026-12-05"}):
        db.query(ProductPriceQuote).filter_by(id=qid).update({"source_type": EXCEL, "source_id": 42})
        db.commit()
        res = api.patch(f"{QUOTES}/{qid}", json=patch)
        assert res.status_code == 200, res.text
        expected = (EXCEL, 42) if patch == {"supplier_code": ""} else (MANUAL, 0)   # gửi lại đúng giá trị cũ = không đổi gì
        assert _src(db) == expected, patch
    db.query(ProductPriceQuote).filter_by(id=qid).update({"source_type": EXCEL, "source_id": 42})
    db.commit()
    assert api.patch(f"{QUOTES}/{qid}", json={"note": "ghi chú mới"}).status_code == 200
    assert _src(db) == (EXCEL, 42)


# ── 3. Nhập Excel ───────────────────────────────────────────────────────────────
def test_excel_them_moi_ghi_nguon_2_cung_id_dot_chay_thu_khong_ghi(db, seed):
    add_products(db, ("CPT0075", "Chai 1L", "Cái"))
    dry = _import(db, seed, [["CPT0075", 2650, "01/12/2026", "", 8, ""]], apply=False)
    assert db.query(ProductPriceQuote).count() == 0 and dry.created_count == 1
    done = _import(db, seed, [["CPT0075", 2650, "01/12/2026", "", 8, ""]])
    assert _src(db) == (EXCEL, done.id)


def test_excel_de_gia_hoac_vat_doi_nguon_sang_dot_moi_de_ghi_chu_hoac_giong_het_thi_khong(db, seed):
    add_products(db, ("CPT0075", "Chai 1L", "Cái"))
    first = _import(db, seed, [["CPT0075", 2650, "01/12/2026", "", 8, "a"]])
    #  Chạy thử đè giá: không ghi gì, nguồn không đổi.
    _import(db, seed, [["CPT0075", 9999, "01/12/2026", "", 8, "a"]], apply=False)
    assert _src(db) == (EXCEL, first.id)
    #  Giống hệt: bỏ qua. Chỉ đổi ghi chú: nguồn giữ nguyên (nguồn = nơi ra GIÁ).
    _import(db, seed, [["CPT0075", 2650, "01/12/2026", "", 8, "a"]])
    note_only = _import(db, seed, [["CPT0075", 2650, "01/12/2026", "", 8, "b"]])
    assert (note_only.updated_count, _src(db)) == (1, (EXCEL, first.id))
    #  Đè đơn giá: nguồn = đợt này.
    price = _import(db, seed, [["CPT0075", 2700, "01/12/2026", "", 8, "b"]])
    assert _src(db) == (EXCEL, price.id) and price.id != first.id
    #  Đè VAT cũng vậy.
    vat = _import(db, seed, [["CPT0075", 2700, "01/12/2026", "", 10, "b"]])
    assert _src(db) == (EXCEL, vat.id)


def test_excel_de_len_bao_gia_nhap_tay_doi_nguon_sang_excel_va_form_sua_lai_ve_tay(db, seed, api):
    add_quote_row = _post(api, price=1000)
    assert add_quote_row.status_code == 201 and _src(db) == (MANUAL, 0)
    batch = _import(db, seed, [["CPT0075", 1500, "01/12/2026", "", 8, ""]])
    assert _src(db) == (EXCEL, batch.id)
    qid = db.query(ProductPriceQuote).one().id
    assert api.patch(f"{QUOTES}/{qid}", json={"price": 1600}).status_code == 200
    assert _src(db) == (MANUAL, 0)


# ── 4. Ràng buộc ở tầng CSDL + bài canh ─────────────────────────────────────────
def test_khoa_duy_nhat_o_tang_csdl_chan_hai_bao_gia_cung_khoa(db):
    add_quote(db, "CPT0075", 1000, "2026-12-01", supplier="NCC01")
    with pytest.raises(IntegrityError):
        add_quote(db, "CPT0075", 2000, "2026-12-01", supplier="NCC01")
    db.rollback()
    add_quote(db, "CPT0075", 2000, "2026-12-01", supplier="NCC02")          # khác NCC thì được


def test_cot_nguon_not_null_khong_co_mac_dinh_o_csdl(db):
    cols = {c["name"]: c for c in sa.inspect(db.get_bind()).get_columns("tab_product_price_quote")}
    for name in ("source_type", "source_id"):
        assert cols[name]["nullable"] is False and cols[name]["default"] is None, name
    uniques = {tuple(u["column_names"]) for u in sa.inspect(db.get_bind()).get_unique_constraints("tab_product_price_quote")}
    assert ("product_code", "supplier_code", "valid_from") in uniques


def test_moi_cho_dung_product_price_quote_ngoai_crud_deu_truyen_nguon():
    """Đường ghi mới sau này quên nguồn thì bài này đỏ: mỗi `ProductPriceQuote(` trong mã ứng dụng phải kèm `source_type=`."""
    offenders = []
    for path in (ROOT / "backend" / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"(?<!class )\bProductPriceQuote\(", text):
            if "source_type=" not in text[m.start():m.start() + 300]:
                offenders.append(f"{path.relative_to(ROOT)}:{text.count(chr(10), 0, m.start()) + 1}")
    assert offenders == []


# ── 5. Migration trên SQLite ────────────────────────────────────────────────────
OLD_QUOTE = ("CREATE TABLE tab_product_price_quote (id INTEGER PRIMARY KEY, created_at DATETIME, created_by BIGINT, updated_at DATETIME, "
             "updated_by BIGINT, product_code VARCHAR(50) NOT NULL, supplier_code VARCHAR(50) NOT NULL, price NUMERIC(18,4), "
             "vat NUMERIC(5,2), valid_from DATE NOT NULL, note VARCHAR(500))")
OLD_BATCH = "CREATE TABLE tab_import_batch (id INTEGER PRIMARY KEY, module SMALLINT, mode SMALLINT, status SMALLINT, created_by BIGINT)"
OLD_LOG = "CREATE TABLE tab_import_log (id INTEGER PRIMARY KEY, batch_id BIGINT, category VARCHAR(40), message TEXT, created_at DATETIME)"
USER = 7


def _load_migration():
    spec = importlib.util.spec_from_file_location("quotesrc784", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(conn, fn):
    with Operations.context(MigrationContext.configure(conn)):
        fn()
    conn.commit()


def _add_quote(conn, qid, code, supplier, valid_from, stamp, by=USER):
    conn.execute(sa.text("INSERT INTO tab_product_price_quote (id, created_at, created_by, updated_at, updated_by, product_code, "
                         "supplier_code, price, vat, valid_from, note) VALUES (:i, :s, :b, :s, :b, :c, :sp, 100, 8, :v, '')"),
                 dict(i=qid, s=stamp, b=by, c=code, sp=supplier, v=valid_from))


def _add_log(conn, batch_id, category, message, stamp):
    conn.execute(sa.text("INSERT INTO tab_import_log (batch_id, category, message, created_at) VALUES (:b, :c, :m, :s)"),
                 dict(b=batch_id, c=category, m=message, s=stamp))


@pytest.fixture
def old_conn():
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conn:
        for ddl in (OLD_QUOTE, OLD_BATCH, OLD_LOG, "CREATE INDEX ix_ppq_code_from ON tab_product_price_quote (product_code, valid_from, id)"):
            conn.execute(sa.text(ddl))
        # Đợt 10, 11, 12 = nhập Excel module 5 thực ghi xong; 13 = chạy thử; 14 = module khác.
        for bid, module, mode, status in ((10, 5, 1, 2), (11, 5, 1, 2), (12, 5, 1, 2), (13, 5, 0, 2), (14, 6, 1, 2)):
            conn.execute(sa.text("INSERT INTO tab_import_batch VALUES (:i, :m, :mo, :s, :u)"), dict(i=bid, m=module, mo=mode, s=status, u=USER))
        # 1: Excel thêm mới (đợt 10).
        _add_quote(conn, 1, "CPT0075", "NCC01", "2026-12-01", "2026-11-20 10:00:01")
        _add_log(conn, 10, "quote_new", "Thêm báo giá CPT0075 · NCC NCC01 · từ 01/12/2026: 2.650", "2026-11-20 10:00:02")
        # 2: tạo ở đợt 10 rồi đợt 11 ĐÈ GIÁ (NCC trống) -> nguồn = đợt 11.
        _add_quote(conn, 2, "NAP0056", "", "2026-12-01", "2026-11-21 09:00:00")
        _add_log(conn, 10, "quote_new", "Thêm báo giá NAP0056 · NCC (trống) · từ 01/12/2026: 1.000", "2026-11-20 10:00:03")
        _add_log(conn, 11, "quote_update", "Cập nhật báo giá NAP0056 · NCC (trống) · từ 01/12/2026: Đơn giá: 1.000 → 1.250",
                 "2026-11-21 09:00:01")
        # 3: tạo ở đợt 10, đợt 12 chỉ đổi GHI CHÚ -> nguồn vẫn là đợt 10 (nơi ra giá).
        _add_quote(conn, 3, "CET0028", "NCC02", "2026-12-02", "2026-11-22 08:00:00")
        _add_log(conn, 10, "quote_new", "Thêm báo giá CET0028 · NCC NCC02 · từ 02/12/2026: 500", "2026-11-20 10:00:04")
        _add_log(conn, 12, "quote_update", "Cập nhật báo giá CET0028 · NCC NCC02 · từ 02/12/2026: Ghi chú: a → b", "2026-11-22 08:00:01")
        # 4: nhập tay, không có nhật ký -> (1, 0).
        _add_quote(conn, 4, "CPT0075", "NCC09", "2026-12-03", "2026-11-23 12:00:00")
        # 5: có nhật ký Excel nhưng người dùng sửa tay SAU đó (updated_at cách xa) -> (1, 0).
        _add_quote(conn, 5, "NAP0056", "NCC03", "2026-12-04", "2026-11-25 15:00:00")
        _add_log(conn, 10, "quote_new", "Thêm báo giá NAP0056 · NCC NCC03 · từ 04/12/2026: 100", "2026-11-20 10:00:05")
        # 6: chỉ có nhật ký của đợt CHẠY THỬ (13) -> (1, 0).
        _add_quote(conn, 6, "CPT0075", "NCC06", "2026-12-06", "2026-11-24 10:00:00")
        _add_log(conn, 13, "quote_new", "Thêm báo giá CPT0075 · NCC NCC06 · từ 06/12/2026: 100", "2026-11-24 10:00:01")
        # 7: mơ hồ - hai đợt cùng chạm trong cửa sổ -> (1, 0).
        _add_quote(conn, 7, "CPT0075", "NCC07", "2026-12-07", "2026-11-26 10:00:00")
        _add_log(conn, 10, "quote_new", "Thêm báo giá CPT0075 · NCC NCC07 · từ 07/12/2026: 100", "2026-11-26 10:00:01")
        _add_log(conn, 11, "quote_update", "Cập nhật báo giá CPT0075 · NCC NCC07 · từ 07/12/2026: VAT: 8 → 10", "2026-11-26 10:00:02")
        # 8: mã in thường + ngày kiểu dd/mm khác dòng khác -> không lẫn.
        _add_quote(conn, 8, "cpt0075", "ncc01", "2026-12-08", "2026-11-27 10:00:00")
        _add_log(conn, 12, "quote_new", "Thêm báo giá CPT0075 · NCC NCC01 · từ 08/12/2026: 100", "2026-11-27 10:00:01")
    with engine.connect() as conn:
        yield conn
    engine.dispose()


def _sources(conn):
    return {r[0]: (r[1], r[2]) for r in conn.execute(sa.text("SELECT id, source_type, source_id FROM tab_product_price_quote ORDER BY id"))}


def test_migration_len_dien_lai_nguon_theo_nhat_ky_nhap_excel(old_conn):
    mig = _load_migration()
    _run(old_conn, mig.upgrade)
    assert _sources(old_conn) == {1: (EXCEL, 10), 2: (EXCEL, 11), 3: (EXCEL, 10), 4: (MANUAL, 0), 5: (MANUAL, 0), 6: (MANUAL, 0),
                                  7: (MANUAL, 0), 8: (EXCEL, 12)}
    cols = {c["name"]: c for c in sa.inspect(old_conn).get_columns("tab_product_price_quote")}
    assert all(cols[n]["nullable"] is False and cols[n]["default"] is None for n in ("source_type", "source_id"))
    inspector = sa.inspect(old_conn)
    assert ("product_code", "supplier_code", "valid_from") in {tuple(u["column_names"]) for u in inspector.get_unique_constraints("tab_product_price_quote")}
    assert "ix_ppq_source" in {i["name"] for i in inspector.get_indexes("tab_product_price_quote")}


def test_migration_dem_so_dong_theo_loai_nguon(old_conn):
    mig = _load_migration()
    with Operations.context(MigrationContext.configure(old_conn)):
        from alembic import op
        with op.batch_alter_table("tab_product_price_quote") as batch:
            batch.add_column(sa.Column("source_type", sa.SmallInteger(), nullable=False, server_default="1"))
            batch.add_column(sa.Column("source_id", sa.BigInteger(), nullable=False, server_default="0"))
        stats = mig.backfill_quote_sources(old_conn)
    assert stats == {"excel": 4, "ambiguous": 1, "manual": 3}


def test_migration_dung_khi_co_bao_gia_trung_khoa_va_khong_dong_vao_bang(old_conn):
    mig = _load_migration()
    _add_quote(old_conn, 9, "CPT0075", "NCC01", "2026-12-01", "2026-11-28 10:00:00")        # trùng dòng 1
    old_conn.commit()
    assert mig.find_duplicate_quote_keys(old_conn) == [("CPT0075", "NCC01", "2026-12-01", 2)]
    with pytest.raises(RuntimeError) as exc:
        _run(old_conn, mig.upgrade)
    assert "DỪNG" in str(exc.value) and "CPT0075" in str(exc.value) and "GROUP BY" in str(exc.value)
    cols = {c["name"] for c in sa.inspect(old_conn).get_columns("tab_product_price_quote")}
    assert "source_type" not in cols                                                       # chưa đổi cấu trúc
    assert old_conn.execute(sa.text("SELECT COUNT(*) FROM tab_product_price_quote")).scalar() == 9   # không xóa dòng nào


def test_migration_xuong_bo_cot_khoa_chi_muc_giu_du_lieu_con_lai_roi_len_lai_ra_cung_ket_qua(old_conn):
    mig = _load_migration()
    _run(old_conn, mig.upgrade)
    first = _sources(old_conn)
    _run(old_conn, mig.downgrade)
    inspector = sa.inspect(old_conn)
    assert {"source_type", "source_id"}.isdisjoint(c["name"] for c in inspector.get_columns("tab_product_price_quote"))
    assert not inspector.get_unique_constraints("tab_product_price_quote")
    assert {i["name"] for i in inspector.get_indexes("tab_product_price_quote")} == {"ix_ppq_code_from"}
    assert old_conn.execute(sa.text("SELECT COUNT(*) FROM tab_product_price_quote")).scalar() == 8
    _run(old_conn, mig.upgrade)
    assert _sources(old_conn) == first


def test_migration_noi_tiep_srcmerge784_va_bang_sao_khop_enum():
    mig = _load_migration()
    assert (mig.revision, mig.down_revision) == ("quotesrc784", "srcmerge784")
    assert (mig.MANUAL, mig.EXCEL_IMPORT) == (QuoteSourceType.MANUAL, QuoteSourceType.EXCEL_IMPORT)
    assert (mig.MODULE_PACKAGING_QUOTE, mig.MODE_APPLY, mig.STATUS_DONE) == (
        int(ImportModule.PACKAGING_QUOTE), int(ImportMode.APPLY), int(ImportStatus.DONE))


def test_chuoi_migration_van_mot_dau_va_quotesrc784_noi_sau_srcmerge784():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config()
    cfg.set_main_option("script_location", str(ROOT / "backend" / "migrations"))
    script = ScriptDirectory.from_config(cfg)
    assert len(script.get_heads()) == 1, script.get_heads()
    assert script.get_revision("quotesrc784").down_revision == "srcmerge784"


def test_gia_tri_ngay_dung_kieu_date_khong_lech_khi_dem_trung_theo_chuoi(db):
    """`valid_from` luôn là kiểu ngày: khóa duy nhất so theo ngày, không theo chuỗi nhập."""
    add_quote(db, "CPT0075", 1000, "2026-12-01")
    row = db.query(ProductPriceQuote).one()
    assert row.valid_from == date(2026, 12, 1) and row.price == Decimal("1000") and isinstance(row.created_at, datetime)
