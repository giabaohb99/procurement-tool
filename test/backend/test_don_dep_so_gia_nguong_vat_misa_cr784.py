"""duoc-CR-784 phase 04 (migration `cleanup784`, 25/11/2026) — dọn sổ giá: bỏ HẲN ngưỡng sàn / trần, VAT dòng Misa = NULL, `synced_at` một nguồn
giờ (đồng hồ máy chủ CSDL), chốt chặn hai đường nạp Misa đá nhau, ô chọn nhà cung cấp của Giá mua gần nhất ổn định thứ tự.

(Bài kiểm "đường ngưỡng là 404" nằm ở `test_bao_gia_nguong_gia_cr784.py`, "cảnh báo 6 / 7 không bao giờ phát ra" ở
`test_tac_dong_gia_bao_bi_cr784.py`.)"""
import importlib.util
import itertools
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
from sqlalchemy import func, text

from app.core.packaging_price_codes import PriceSourceType
from app.modules.import_tool.model import ImportBatch, ImportMode, ImportModule, ImportStatus
from app.modules.packaging_cost import misa_xlsx_import
from app.modules.packaging_cost.last_prices_service import build_last_prices, supplier_options
from app.modules.product_price import ledger_sync_service
from app.modules.product_price.misa_ledger_import import (XLSX_GUARD_MESSAGE, MisaSourceError, build_misa_rows,
                                                          ensure_no_xlsx_misa_rows, import_misa_rows, purge_misa_rows)
from app.modules.product_price.model import ProductPriceLedger as L
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from so_gia_factory_cr784 import add_ledger, add_products, read_report_sheet

MISA = int(PriceSourceType.MISA)
ROOT = Path(__file__).resolve().parents[2]
MIGRATION = next((ROOT / "backend" / "migrations" / "versions").glob("cleanup784_*.py"))
URL = "/api/packaging-cost/history"
SRC = {"vtbb": {"NAP0056": ["Nắp 56", "Nắp", "Cái"]},
       "mua": [[1, "2025-09-20", "CÔNG TY A - VTBB", "NAP0056", 1000, 623, "NCC0019", "KHO1", None],
               [2, "2025-11-07", "CÔNG TY B", "NAP0056", 500, 700, "NCC116", "KHO1", None]]}


def _load(db_rows=None):
    rows, _ = build_misa_rows(db_rows or SRC, 1)
    return rows


def _applied_misa_batch(db, seed, apply=True, status=ImportStatus.DONE):
    db.add(ImportBatch(module=int(ImportModule.PACKAGING_MISA), mode=int(ImportMode.APPLY if apply else ImportMode.DRY_RUN),
                       filename="so-misa.xlsx", status=int(status), created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()


# ── 1. VAT dòng Misa = NULL ─────────────────────────────────────────────────────
def test_nap_misa_tu_html_ghi_vat_null():
    assert all(r["vat"] is None for r in _load())


def test_nap_misa_tu_html_vao_so_gia_vat_null_con_nguon_khac_giu_vat(db):
    add_ledger(db, "NAP0056", 100, "2025-01-01", vat=Decimal(8))
    import_misa_rows(db, _load())
    db.commit()
    assert {r.vat for r in db.query(L).filter(L.source_type == MISA)} == {None}
    assert {r.vat for r in db.query(L).filter(L.source_type != MISA)} == {Decimal(8)}


def test_nap_misa_tu_xlsx_module_6_ghi_vat_null(db, seed):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Ngày hạch toán", "Mã nhà cung cấp", "Tên nhà cung cấp", "Tên kho", "Mã hàng", "Tên hàng", "ĐVT", "Số lượng", "Đơn giá", "Giá trị"])
    ws.append(["17/01/2025", "NCC38", "CÔNG TY PHL", "KHO", "CET0028", "Chai", "Cái", 12000, 4724, 56688000])
    batch = ImportBatch(module=int(ImportModule.PACKAGING_MISA), mode=int(ImportMode.APPLY), filename="x.xlsx",
                        status=int(ImportStatus.RUNNING), created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(batch)
    db.commit()
    misa_xlsx_import.run(db, batch, wb, apply=True)
    rows = db.query(L).filter(L.source_type == MISA).all()
    assert len(rows) == 1 and rows[0].vat is None and rows[0].price == Decimal("4724.0000")


@pytest.fixture
def api(db, seed, cap_quyen, client_as):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True, export=True)
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"))
    add_ledger(db, "CPT0105", 100, "2026-01-01", source_type=PriceSourceType.PURCHASE_HISTORY)          # VAT 8
    add_ledger(db, "CPT0105", 110, "2026-02-01", source_type=PriceSourceType.MISA, supplier="NCC9")      # VAT NULL
    return client_as(db.get(User, seed.u_req_id))


def test_lich_su_api_tra_vat_null_cho_dong_misa_va_so_cho_dong_khac_gia_gop_khong_doi(api):
    data = api.get(URL, params={"codes": ["CPT0105"]}).json()["data"]
    by_source = {r["source_type"]: r for r in data["items"]}
    assert by_source[MISA]["vat"] is None and by_source[int(PriceSourceType.PURCHASE_HISTORY)]["vat"] == 8
    assert data["stats"]["min"] == 100 and data["stats"]["max"] == 110 and data["stats"]["priced_count"] == 2


@pytest.mark.parametrize("direction", ["asc", "desc"])
def test_lich_su_xep_theo_vat_dong_vat_null_xuong_cuoi_ca_hai_chieu(api, direction):
    items = api.get(URL, params={"codes": ["CPT0105"], "sort_by": "vat", "sort_dir": direction}).json()["data"]["items"]
    assert [r["vat"] for r in items] == [8, None]


def test_lich_su_excel_o_vat_cua_dong_misa_de_trong(api):
    res = api.get(URL + "/export", params={"codes": ["CPT0105"], "sort_by": "date", "sort_dir": "asc"})
    assert res.status_code == 200
    head, rows = read_report_sheet(openpyxl.load_workbook(BytesIO(res.content)).active)
    vat = [r[head.index("VAT (%)")].value for r in rows]
    assert vat == [8, None]                    # lịch sử cũ 8, Misa trống (không phải 0)


# ── 2. synced_at một nguồn giờ ──────────────────────────────────────────────────
def _server_now(db) -> datetime:
    return datetime.fromisoformat(str(db.execute(text("SELECT CURRENT_TIMESTAMP")).scalar()))


def test_synced_at_khong_con_mac_dinh_phia_python_chi_con_server_default():
    col = L.__table__.c.synced_at
    assert col.default is None and col.server_default is not None


def test_khong_con_noi_nao_gan_synced_at_bang_gio_python():
    offenders = []
    for path in (ROOT / "backend").rglob("*.py"):
        if "migrations" in path.parts:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"synced_at\s*=\s*datetime\.|synced_at.*utcnow", line):
                offenders.append(f"{path.relative_to(ROOT)}:{n}")
    assert offenders == []


def test_chen_dong_so_gia_lay_gio_may_chu(db):
    row = add_ledger(db, "NAP0056", 100, "2025-01-01")
    db.refresh(row)
    assert abs((row.synced_at - _server_now(db)).total_seconds()) < 5


def test_ghi_de_dong_so_gia_bang_gio_may_chu_khong_phai_gio_python(db):
    row = add_ledger(db, "NAP0056", 100, "2025-01-01")
    db.execute(text("UPDATE tab_product_price_ledger SET synced_at = '2000-01-01 00:00:00'"))
    db.commit()
    db.refresh(row)
    assert row.synced_at.year == 2000
    ledger_sync_service._apply(row, {"price": Decimal("120")})
    assert isinstance(row.synced_at, sa.sql.elements.ClauseElement)         # biểu thức SQL (CURRENT_TIMESTAMP), chưa phải giờ Python
    db.commit()
    db.refresh(row)
    assert abs((row.synced_at - _server_now(db)).total_seconds()) < 5 and row.price == Decimal("120")


def test_nap_lai_misa_co_doi_noi_dung_cap_nhat_synced_at_dong_khong_doi_thi_giu(db):
    import_misa_rows(db, _load())
    db.commit()
    db.execute(text("UPDATE tab_product_price_ledger SET synced_at = '2000-01-01 00:00:00'"))
    db.commit()
    changed = {**SRC, "mua": [SRC["mua"][0], [*SRC["mua"][1][:5], 999, *SRC["mua"][1][6:]]]}
    stats = import_misa_rows(db, _load(changed))
    db.commit()
    assert stats["updated"] == 1 and stats["unchanged"] == 1
    years = {r.source_id: r.synced_at.year for r in db.query(L).filter(L.source_type == MISA)}
    assert years[1] == 2000 and years[2] >= 2025


def test_bo_cap_nhat_giu_dong_ma_phien_ban_cu_se_ghi_vat_khong_nhap_lai_vat_null(db):
    """Dòng Misa nạp trước phase này có `vat = 0`; nạp lại bằng mã mới đổi nó thành NULL (cập nhật), không để hai kiểu trộn."""
    import_misa_rows(db, _load())
    db.execute(text("UPDATE tab_product_price_ledger SET vat = 0 WHERE source_type = 3"))
    db.commit()
    stats = import_misa_rows(db, _load())
    db.commit()
    assert stats["updated"] == 2 and {r.vat for r in db.query(L).filter(L.source_type == MISA)} == {None}


# ── 3. Chốt chặn hai đường nạp Misa ─────────────────────────────────────────────
def test_so_chua_co_misa_thi_script_html_chay_duoc_du_module_6_tung_nap(db, seed):
    _applied_misa_batch(db, seed)
    ensure_no_xlsx_misa_rows(db)                 # chưa có dòng Misa nào -> qua (vd sau --purge)
    assert import_misa_rows(db, _load())["inserted"] == 2


def test_script_html_bi_chan_khi_module_6_da_nap_that_va_so_con_dong_misa(db, seed):
    add_ledger(db, "NAP0056", 100, "2025-01-01", source_type=PriceSourceType.MISA, source_id=1)
    _applied_misa_batch(db, seed)
    with pytest.raises(MisaSourceError) as exc:
        import_misa_rows(db, _load())
    assert str(exc.value) == XLSX_GUARD_MESSAGE and "module 6" in XLSX_GUARD_MESSAGE and "--purge" in XLSX_GUARD_MESSAGE
    assert db.query(L).count() == 1                     # không đụng sổ


@pytest.mark.parametrize("apply,status", [(False, ImportStatus.DONE), (True, ImportStatus.FAILED), (True, ImportStatus.QUEUED)])
def test_lo_chay_thu_hoac_loi_cua_module_6_khong_chan_script_html(db, seed, apply, status):
    add_ledger(db, "NAP0056", 100, "2025-01-01", source_type=PriceSourceType.MISA, source_id=1)
    _applied_misa_batch(db, seed, apply=apply, status=status)
    ensure_no_xlsx_misa_rows(db)


def test_nap_html_roi_html_lai_van_chay_duoc_khi_chua_co_module_6(db):
    import_misa_rows(db, _load())
    db.commit()
    assert import_misa_rows(db, _load())["unchanged"] == 2


def test_gay_chan_het_hieu_luc_sau_purge_va_module_6_ghi_tiep_khong_dung_id_html(db, seed):
    import_misa_rows(db, _load())
    db.commit()
    _applied_misa_batch(db, seed)
    with pytest.raises(MisaSourceError):
        import_misa_rows(db, _load())
    purge_misa_rows(db)
    import_misa_rows(db, _load())                       # sổ trống Misa -> nạp lại được


def test_script_html_in_loi_tieng_viet_va_thoat_ma_2_khi_bi_chan():
    text_ = (ROOT / "backend" / "scripts" / "import_misa_price_ledger.py").read_text(encoding="utf-8")
    assert "except MisaSourceError" in text_ and "return 2" in text_ and "module 6" in text_


# ── 4. Ô chọn nhà cung cấp ổn định thứ tự ───────────────────────────────────────
def _row(code, *pairs):
    return {"code": code, "purchases": [{"supplier_code": sc, "supplier": name} for sc, name in pairs]}


def test_o_chon_nha_cung_cap_khong_phu_thuoc_thu_tu_dong_dau_vao():
    rows = [_row("A", ("NCC1", "Nhựa Việt"), ("NCC2", "Công ty Z")), _row("B", ("NCC1", "Nhựa Á Châu"), ("NCC3", "bao bì X")),
            _row("C", ("NCC1", "nhựa việt"), ("NCC2", "Công ty Z"))]
    results = {str(supplier_options(list(perm))) for perm in itertools.permutations(rows)}
    assert len(results) == 1
    options = supplier_options(rows)
    assert options == [{"code": "NCC3", "name": "bao bì X"}, {"code": "NCC2", "name": "Công ty Z"},
                       {"code": "NCC1", "name": "Nhựa Á Châu"}]      # xếp theo tên bỏ dấu; NCC1 lấy tên nhỏ nhất theo (bỏ dấu, chữ gốc)


def test_o_chon_nha_cung_cap_bo_qua_dong_khong_co_ma_ncc():
    assert supplier_options([_row("A", ("", "Không mã"), ("NCC1", "Một"))]) == [{"code": "NCC1", "name": "Một"}]


def test_gia_mua_gan_nhat_cung_mot_ma_ncc_nhieu_ten_ra_cung_ket_qua_moi_lan(db):
    add_products(db, ("A", "Chai A", "Cái"), ("B", "Chai B", "Cái"), ("C", "Chai C", "Cái"))
    add_ledger(db, "A", 100, "2026-01-01", supplier="NCC1", source_type=PriceSourceType.MISA).supplier_name = "Nhựa Việt"
    add_ledger(db, "B", 100, "2026-01-01", supplier="NCC1", source_type=PriceSourceType.MISA).supplier_name = "Nhựa Á Châu"
    add_ledger(db, "C", 100, "2026-01-01", supplier="NCC1", source_type=PriceSourceType.MISA).supplier_name = "NHỰA VIỆT"
    db.commit()
    runs = [build_last_prices(db, scope="all") for _ in range(3)]
    assert all(r["suppliers"] == runs[0]["suppliers"] for r in runs)
    assert runs[0]["suppliers"] == [{"code": "NCC1", "name": "Nhựa Á Châu"}]
    assert [r["code"] for r in runs[0]["rows"]] == ["A", "B", "C"]


# ── 5. Migration `cleanup784` trên SQLite ───────────────────────────────────────
OLD_LEDGER = ("CREATE TABLE tab_product_price_ledger (id INTEGER PRIMARY KEY, source_type SMALLINT NOT NULL, source_id BIGINT NOT NULL, "
              "product_code VARCHAR(50) NOT NULL, price NUMERIC(18,4) NOT NULL DEFAULT 0, vat NUMERIC(5,2) NOT NULL DEFAULT 0, "
              "synced_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, CONSTRAINT uq_ppl_source UNIQUE (source_type, source_id))")
OLD_LIMIT = ("CREATE TABLE tab_product_price_limit (id INTEGER PRIMARY KEY, created_at DATETIME, created_by BIGINT, updated_at DATETIME, "
             "updated_by BIGINT, product_code VARCHAR(50) NOT NULL, floor_price NUMERIC(18,4), ceiling_price NUMERIC(18,4), "
             "note VARCHAR(500) NOT NULL DEFAULT '', CONSTRAINT uq_tab_product_price_limit_product_code UNIQUE (product_code))")


def _load_migration():
    spec = importlib.util.spec_from_file_location("cleanup784", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(conn, fn):
    with Operations.context(MigrationContext.configure(conn)):
        fn()
    conn.commit()


@pytest.fixture
def old_conn():
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(sa.text(OLD_LEDGER))
        conn.execute(sa.text(OLD_LIMIT))
        conn.execute(sa.text("INSERT INTO tab_product_price_limit (id, product_code, floor_price) VALUES (1, 'CPT0075', 10)"))
        for sid, (stype, vat) in enumerate(((1, 8), (1, 0), (2, 10), (3, 0), (3, 0)), start=1):
            conn.execute(sa.text("INSERT INTO tab_product_price_ledger (source_type, source_id, product_code, price, vat) "
                                 "VALUES (:t, :i, 'CPT0075', 100, :v)"), dict(t=stype, i=sid, v=vat))
    with engine.connect() as conn:
        yield conn
    engine.dispose()


def _vats(conn):
    return [tuple(r) for r in conn.execute(sa.text("SELECT source_type, vat FROM tab_product_price_ledger ORDER BY id"))]


def test_migration_len_bo_bang_nguong_vat_cho_null_va_dong_misa_thanh_null_dong_khac_giu(old_conn):
    mig = _load_migration()
    _run(old_conn, mig.upgrade)
    inspector = sa.inspect(old_conn)
    assert not inspector.has_table("tab_product_price_limit")
    cols = {c["name"]: c for c in inspector.get_columns("tab_product_price_ledger")}
    assert cols["vat"]["nullable"] is True
    assert _vats(old_conn) == [(1, 8), (1, 0), (2, 10), (3, None), (3, None)]        # chỉ nguồn 3 thành NULL; 0% thật ở nguồn khác giữ
    assert "uq_ppl_source" in {u["name"] for u in inspector.get_unique_constraints("tab_product_price_ledger")}


def test_migration_xuong_dung_lai_bang_nguong_rong_vat_null_ve_0_va_not_null_roi_len_lai_ra_cung_ket_qua(old_conn):
    mig = _load_migration()
    _run(old_conn, mig.upgrade)
    first = _vats(old_conn)
    _run(old_conn, mig.downgrade)
    inspector = sa.inspect(old_conn)
    cols = {c["name"]: c for c in inspector.get_columns("tab_product_price_ledger")}
    assert cols["vat"]["nullable"] is False and _vats(old_conn) == [(1, 8), (1, 0), (2, 10), (3, 0), (3, 0)]
    assert inspector.has_table("tab_product_price_limit")
    limit_cols = {c["name"] for c in inspector.get_columns("tab_product_price_limit")}
    assert limit_cols == {"id", "created_at", "created_by", "updated_at", "updated_by", "product_code", "floor_price", "ceiling_price", "note"}
    assert old_conn.execute(sa.text("SELECT COUNT(*) FROM tab_product_price_limit")).scalar() == 0          # bảng dựng lại RỖNG
    assert "uq_tab_product_price_limit_product_code" in {u["name"] for u in inspector.get_unique_constraints("tab_product_price_limit")}
    _run(old_conn, mig.upgrade)
    assert _vats(old_conn) == first


def test_migration_len_chay_lai_khi_bang_nguong_da_mat_khong_vo(old_conn):
    mig = _load_migration()
    old_conn.execute(sa.text("DROP TABLE tab_product_price_limit"))
    old_conn.commit()
    _run(old_conn, mig.upgrade)
    assert _vats(old_conn)[-1] == (3, None)


def test_migration_noi_tiep_quotesrc784_nam_trong_chuoi_mot_dau_va_nguon_misa_khop_enum():
    mig = _load_migration()
    assert (mig.revision, mig.down_revision, mig.MISA_SOURCE_TYPE) == ("cleanup784", "quotesrc784", MISA)
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config()
    cfg.set_main_option("script_location", str(ROOT / "backend" / "migrations"))
    script = ScriptDirectory.from_config(cfg)
    assert len(script.get_heads()) == 1                                    # chuỗi một đầu (các phase sau nối tiếp cleanup784)
    assert "cleanup784" in {r.revision for r in script.walk_revisions()}


def test_func_now_dung_trong_model_va_khong_con_import_thua():
    assert func.now() is not None and "datetime.utcnow" not in (ROOT / "backend/app/modules/product_price/model.py").read_text(encoding="utf-8")
