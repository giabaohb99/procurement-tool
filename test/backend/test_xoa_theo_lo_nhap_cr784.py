"""duoc-CR-784 phase 07 (25/11/2026) — đánh dấu lô nhập trên định mức / sổ Misa và XÓA DỮ LIỆU THEO LÔ (module 4, 5, 6).

Phủ: nhập Excel ghi `import_batch_id` (lần ghi cuối thắng, form không đổi), xem trước tách dòng đã sửa tay, xóa mặc định giữ dòng
sửa tay / `include_edited` xóa hết, thành phần xóa theo, báo giá chỉ dòng của lô, sổ Misa tính lại mốc, 403 / 404 / 400,
nhật ký thao tác, và migration `bombatch784` (đánh dấu dữ liệu đang có, lệch số thì bỏ qua).
"""
import importlib.util
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import openpyxl
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.core.packaging_price_codes import PriceSourceType, QuoteSourceType
from app.modules.audit.model import AuditLog
from app.modules.import_tool.model import ImportBatch, ImportMode, ImportModule, ImportStatus
from app.modules.packaging_cost import batch_purge_service as svc
from app.modules.packaging_cost import bom_import, misa_xlsx_import, quote_import
from app.modules.packaging_cost.model import PackagingBom, PackagingBomPart
from app.modules.product_price.misa_cutoff import get_misa_cutoff
from app.modules.product_price.model import ProductPriceLedger as L
from app.modules.product_price.model import ProductPriceQuote as Q
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from so_gia_factory_cr784 import add_ledger, add_products, add_quote, build_bom

MISA = int(PriceSourceType.MISA)
BOMS = "/api/packaging-boms"
MIGRATION = next((Path(__file__).resolve().parents[2] / "backend" / "migrations" / "versions").glob("bombatch784_*.py"))
BOM_HEAD = ["Mã chai", "Mã nắp", "Mã HH", "Tên HH", "Tên pháp lý", "Quy cách", "x", "x", "Nhãn", "Nhãn thùng", "Thùng"]
MISA_HEAD = ["Ngày hạch toán", "Mã nhà cung cấp", "Tên nhà cung cấp", "Tên kho", "Mã hàng", "Tên hàng", "ĐVT", "Số lượng",
             "Đơn giá", "Giá trị"]
QUOTE_HEAD = ["Mã VTBB", "Đơn giá", "Ngày hiệu lực", "Mã NCC", "VAT (%)", "Ghi chú"]


@pytest.fixture
def catalog(db):
    add_products(db, ("CPT0075", "Chai", "Cái"), ("NAP0056", "Nắp", "Cái"), ("CET0028", "Chai khác", "Cái"))


PURGE_KEYS = ("packaging_bom", "packaging_price_list", "packaging_history")


def _grant(cap_quyen, uid, *, imp=True, delete=True):
    if imp:
        cap_quyen(uid, "import", scope="all", read=True)
    for key in PURGE_KEYS:                                      # bao-CR-792: mỗi loại lô gác bằng khóa của màn giữ dữ liệu
        cap_quyen(uid, key, scope="all", read=True, create=True, write=True, delete=delete)


@pytest.fixture
def api(db, seed, cap_quyen, client_as, catalog):  # noqa: F811
    _grant(cap_quyen, seed.u_req_id)
    return client_as(db.get(User, seed.u_req_id))


def _bom_wb(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "MAP_SP"
    ws.append(BOM_HEAD)
    for _ in range(3):
        ws.append([None] * 11)
    for r in rows:
        ws.append(r)
    return wb


def _sheet(head, rows, title="Sheet1", lead=0):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title
    for _ in range(lead):
        ws.append(["Sổ chi tiết mua hàng"])
    ws.append(head)
    for r in rows:
        ws.append(r)
    return wb


def _run(db, seed, runner, module, wb, apply=True):
    batch = ImportBatch(module=int(module), mode=int(ImportMode.APPLY if apply else ImportMode.DRY_RUN), filename="x.xlsx",
                        status=int(ImportStatus.RUNNING), created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(batch)
    db.commit()
    runner.run(db, batch, wb, apply=apply)
    db.refresh(batch)
    return batch


def _bom_batch(db, seed, rows, apply=True):
    return _run(db, seed, bom_import, ImportModule.PACKAGING_BOM, _bom_wb(rows), apply)


def _finish(db, batch, *, minutes_ago=60):
    """Đặt giờ kết thúc lô lùi về trước để bài kiểm tách được dòng 'sửa sau khi nhập' (ghi trực tiếp, không qua ORM onupdate)."""
    batch.finished_at = datetime.utcnow() - timedelta(minutes=minutes_ago)
    db.commit()


def _touch(db, model, where, when):
    """Giả lập một lần sửa tay SAU giờ kết thúc lô (đặt cột giờ sửa cuối)."""
    col = {PackagingBom: "updated_at", Q: "updated_at", L: "synced_at"}[model]
    db.execute(sa.update(model).where(where).values({col: when}))
    db.commit()


ROWS = [["CPT0075", "NAP0056", "HH1", "Sản phẩm 1", "", 12, None, None, "", "", ""],
        ["CPT0075", "", "HH2", "Sản phẩm 2", "", 6, None, None, "", "", ""],
        ["CET0028", "", "HH3", "Sản phẩm 3", "", 24, None, None, "", "", ""]]


# ── Ghi id lô khi nhập ────────────────────────────────────────────────────────────
def test_nhap_excel_dinh_muc_ghi_id_lo_cho_dong_tao_va_dong_sua_con_dong_giu_nguyen_thi_khong(db, seed, catalog):
    b1 = _bom_batch(db, seed, ROWS)
    assert {r.fg_code: r.import_batch_id for r in db.query(PackagingBom).all()} == {"HH1": b1.id, "HH2": b1.id, "HH3": b1.id}
    changed = [list(r) for r in ROWS]
    changed[0][5] = 20                                    # HH1 đổi quy cách -> lô 2 SỬA
    b2 = _bom_batch(db, seed, changed)
    assert (b2.created_count, b2.updated_count, b2.skipped_count) == (0, 1, 2)
    got = {r.fg_code: r.import_batch_id for r in db.query(PackagingBom).all()}
    assert got == {"HH1": b2.id, "HH2": b1.id, "HH3": b1.id}      # lần ghi cuối thắng; dòng không đổi giữ id lô cũ


def test_chay_thu_khong_ghi_gi_va_form_tao_tay_co_id_lo_0_sua_tay_khong_doi(db, seed, api, catalog):
    _bom_batch(db, seed, ROWS, apply=False)
    assert db.query(PackagingBom).count() == 0
    b = _bom_batch(db, seed, ROWS)
    res = api.post(BOMS, json={"fg_code": "HH9", "fg_name": "Tay", "bottle_code": "CPT0075"})
    assert res.status_code in (200, 201), res.text
    assert db.query(PackagingBom).filter_by(fg_code="HH9").one().import_batch_id == 0
    hh1 = db.query(PackagingBom).filter_by(fg_code="HH1").one()
    assert api.patch(f"{BOMS}/{hh1.id}", json={"fg_name": "Đổi tay"}).status_code == 200
    db.expire_all()
    assert db.get(PackagingBom, hh1.id).import_batch_id == b.id          # form sửa tay KHÔNG đổi cột


def test_nap_misa_ghi_id_lo_cho_dong_them_con_dong_script_html_giu_0(db, seed, catalog):
    html = add_ledger(db, "CET0028", 4000, "2025-01-10", source_type=PriceSourceType.MISA, source_id=77)
    wb = _sheet(MISA_HEAD, [["17/01/2025", "NCC38", "A", "K", "CET0028", "Chai", "Cái", 12000, 4724, 56688000],
                            ["24/12/2025", "NCC01", "B", "K", "CET0028", "Chai", "Cái", 5000, 4300, 21500000]],
                title="Sổ chi tiết mua hàng", lead=2)
    b = _run(db, seed, misa_xlsx_import, ImportModule.PACKAGING_MISA, wb)
    ids = {(r.price_date, r.import_batch_id) for r in db.query(L).filter(L.source_type == MISA).all()}
    assert (date(2025, 1, 17), b.id) in ids and (date(2025, 12, 24), b.id) in ids
    assert db.get(L, html.id).import_batch_id == 0                              # dòng script HTML ngoài khoảng ngày: giữ nguyên, id lô 0


# ── Xem trước ──────────────────────────────────────────────────────────────────────
def test_xem_truoc_dem_tong_va_tach_dong_da_sua_tay_sau_khi_nhap(db, seed, api):
    b = _bom_batch(db, seed, ROWS)
    _finish(db, b)
    _touch(db, PackagingBom, PackagingBom.fg_code == "HH2", datetime.utcnow())      # HH2 sửa tay sau lô
    _touch(db, PackagingBom, PackagingBom.fg_code != "HH2", datetime.utcnow() - timedelta(hours=2))
    res = api.get(f"/api/imports/{b.id}/purge-preview")
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert (data["total"], data["untouched"], data["edited"], data["recomputes_cutoff"]) == (3, 2, 1, False)
    assert data["module"] == 4 and data["target_label"] == "định mức bao bì"


# ── Xóa định mức ─────────────────────────────────────────────────────────────────────
def test_xoa_mac_dinh_giu_dong_sua_tay_thanh_phan_xoa_theo_va_khong_dung_dong_khac_lo(db, seed, api):
    b = _bom_batch(db, seed, ROWS)
    other = build_bom(fg_code="HH7", fg_name="Tay", bottle_code="CPT0075", cap_code="NAP0056", created_by=1, updated_by=1)
    db.add(other)
    db.commit()
    _finish(db, b)
    _touch(db, PackagingBom, PackagingBom.fg_code == "HH2", datetime.utcnow())
    _touch(db, PackagingBom, PackagingBom.fg_code.in_(("HH1", "HH3")), datetime.utcnow() - timedelta(hours=2))
    res = api.post(f"/api/imports/{b.id}/purge", json={})
    assert res.status_code == 200, res.text
    assert (res.json()["data"]["deleted"], res.json()["data"]["kept_edited"]) == (2, 1)
    db.expire_all()
    assert {r.fg_code for r in db.query(PackagingBom).all()} == {"HH2", "HH7"}
    kept_ids = {r.id for r in db.query(PackagingBom).all()}
    assert {p.bom_id for p in db.query(PackagingBomPart).all()} <= kept_ids      # thành phần của dòng đã xóa cũng mất
    assert api.post(f"/api/imports/{b.id}/purge", json={}).json()["data"]["deleted"] == 0        # gọi lại: không còn gì


def test_xoa_kem_dong_sua_tay_khi_chon_include_edited(db, seed, api):
    b = _bom_batch(db, seed, ROWS)
    _finish(db, b)
    _touch(db, PackagingBom, PackagingBom.fg_code == "HH2", datetime.utcnow())
    res = api.post(f"/api/imports/{b.id}/purge", json={"include_edited": True})
    assert res.json()["data"]["deleted"] == 3
    db.expire_all()
    assert db.query(PackagingBom).count() == 0 and db.query(PackagingBomPart).count() == 0


def test_xoa_lo_cu_khong_dung_dong_da_bi_lo_moi_ghi_de(db, seed, api):
    b1 = _bom_batch(db, seed, ROWS)
    changed = [list(r) for r in ROWS]
    changed[0][5] = 20
    b2 = _bom_batch(db, seed, changed)
    _finish(db, b1)
    res = api.post(f"/api/imports/{b1.id}/purge", json={"include_edited": True})
    assert res.json()["data"]["deleted"] == 2
    db.expire_all()
    assert [(r.fg_code, r.import_batch_id) for r in db.query(PackagingBom).all()] == [("HH1", b2.id)]


def test_xoa_theo_lo_ghi_nhat_ky_thao_tac(db, seed, api):
    b = _bom_batch(db, seed, ROWS)
    api.post(f"/api/imports/{b.id}/purge", json={})
    log = db.query(AuditLog).filter(AuditLog.entity == "import_batch", AuditLog.entity_id == b.id).one()
    assert log.action == "delete" and "xóa 3 dòng" in log.message and log.created_by == seed.u_req_id


# ── Báo giá ──────────────────────────────────────────────────────────────────────────
def test_xoa_lo_bao_gia_chi_dung_dong_nguon_excel_cua_lo(db, seed, api):
    manual = add_quote(db, "CPT0075", 1000, "2026-11-01")
    wb = _sheet(QUOTE_HEAD, [["CPT0075", 2650, "01/12/2026", "NCC0185", 8, ""], ["NAP0056", 1250, "01/12/2026", "", 8, ""]])
    b = _run(db, seed, quote_import, ImportModule.PACKAGING_QUOTE, wb)
    assert db.query(Q).filter_by(source_type=int(QuoteSourceType.EXCEL_IMPORT), source_id=b.id).count() == 2
    _finish(db, b)
    _touch(db, Q, Q.product_code == "NAP0056", datetime.utcnow())
    _touch(db, Q, Q.product_code == "CPT0075", datetime.utcnow() - timedelta(hours=2))
    pv = api.get(f"/api/imports/{b.id}/purge-preview").json()["data"]
    assert (pv["total"], pv["edited"], pv["target_label"]) == (2, 1, "báo giá VTBB")
    assert api.post(f"/api/imports/{b.id}/purge", json={}).json()["data"]["deleted"] == 1
    db.expire_all()
    assert {q.id for q in db.query(Q).all()} >= {manual.id} and db.query(Q).filter_by(product_code="CPT0075", supplier_code="NCC0185").count() == 0
    assert db.query(Q).filter_by(product_code="NAP0056").count() == 1               # dòng sửa tay được giữ


# ── Sổ Misa ──────────────────────────────────────────────────────────────────────────
def _misa_batch(db, seed, rows):
    return _run(db, seed, misa_xlsx_import, ImportModule.PACKAGING_MISA,
                _sheet(MISA_HEAD, rows, title="Sổ chi tiết mua hàng", lead=2))


def test_xoa_lo_misa_tinh_lai_moc_theo_dong_con_lai_va_bo_moc_khi_het(db, seed, api):
    old = add_ledger(db, "CET0028", 4000, "2024-05-05", source_type=PriceSourceType.MISA, source_id=500)      # dòng script HTML, id lô 0
    b = _misa_batch(db, seed, [["17/01/2025", "NCC38", "A", "K", "CET0028", "Chai", "Cái", 12000, 4724, 56688000],
                               ["24/12/2025", "NCC01", "B", "K", "CET0028", "Chai", "Cái", 5000, 4300, 21500000]])
    assert get_misa_cutoff(db) == date(2025, 12, 24)
    pv = api.get(f"/api/imports/{b.id}/purge-preview").json()["data"]
    assert pv["recomputes_cutoff"] is True and pv["total"] == 2 and pv["edited"] == 0
    res = api.post(f"/api/imports/{b.id}/purge", json={})
    assert res.json()["data"]["deleted"] == 2 and "Mốc sổ Misa" in res.json()["message"]
    db.expire_all()
    assert [r.id for r in db.query(L).filter(L.source_type == MISA).all()] == [old.id]
    assert get_misa_cutoff(db) == date(2024, 5, 5)                                 # mốc lùi về dòng Misa còn lại
    db.delete(db.get(L, old.id))
    db.commit()
    b2 = _misa_batch(db, seed, [["10/03/2025", "NCC38", "A", "K", "CET0028", "Chai", "Cái", 10, 100, 1000]])
    api.post(f"/api/imports/{b2.id}/purge", json={})
    assert get_misa_cutoff(db) is None                                             # hết dòng Misa -> bỏ mốc


# ── Quyền, lỗi ───────────────────────────────────────────────────────────────────────
def test_thieu_quyen_xoa_o_gia_bao_bi_hoac_thieu_import_doc_la_403(db, seed, cap_quyen, client_as, catalog):  # noqa: F811
    b = _bom_batch(db, seed, ROWS)
    _grant(cap_quyen, seed.u_req_id, delete=False)                                                 # KHÔNG có delete
    api = client_as(db.get(User, seed.u_req_id))
    assert api.get(f"/api/imports/{b.id}/purge-preview").status_code == 403
    assert api.post(f"/api/imports/{b.id}/purge", json={}).status_code == 403
    assert db.query(PackagingBom).count() == 3


def test_thieu_quyen_doc_import_la_403(db, seed, cap_quyen, client_as, catalog):  # noqa: F811
    b = _bom_batch(db, seed, ROWS)
    _grant(cap_quyen, seed.u_req_id, imp=False)                                                    # không có import.read
    api = client_as(db.get(User, seed.u_req_id))
    assert api.get(f"/api/imports/{b.id}/purge-preview").status_code == 403
    assert api.post(f"/api/imports/{b.id}/purge", json={}).status_code == 403


def test_lo_khong_ton_tai_la_404_chay_thu_chua_xong_hoac_sai_loai_la_400(db, seed, api):
    assert api.get("/api/imports/99999/purge-preview").status_code == 404
    dry = _bom_batch(db, seed, ROWS, apply=False)
    assert api.get(f"/api/imports/{dry.id}/purge-preview").status_code == 400
    done = _bom_batch(db, seed, ROWS)
    done.status = int(ImportStatus.RUNNING)
    db.commit()
    assert api.post(f"/api/imports/{done.id}/purge", json={}).status_code == 400
    survey = ImportBatch(module=int(ImportModule.SURVEY), mode=1, status=int(ImportStatus.DONE), filename="k.xlsx",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(survey)
    db.commit()
    res = api.post(f"/api/imports/{survey.id}/purge", json={})
    assert res.status_code == 400 and "Định mức" in res.json()["error"]["message"]
    assert db.query(PackagingBom).count() == 3


def test_xoa_loi_giua_chung_thi_lui_het(db, seed, monkeypatch):
    b = _bom_batch(db, seed, ROWS)

    def boom(*a, **k):
        raise RuntimeError("hỏng giữa chừng")

    monkeypatch.setattr(svc, "record", boom)
    with pytest.raises(RuntimeError):
        svc.purge(db, b, seed.u_req_id)
    assert db.query(PackagingBom).count() == 3 and db.query(PackagingBomPart).count() > 0


# ── Migration ─────────────────────────────────────────────────────────────────────────
def _load_migration():
    spec = importlib.util.spec_from_file_location("bombatch784", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OLD_DDL = [
    "CREATE TABLE tab_packaging_bom (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at DATETIME NOT NULL, created_by BIGINT NOT NULL,"
    " fg_code VARCHAR(50) NOT NULL UNIQUE)",
    "CREATE TABLE tab_product_price_ledger (id INTEGER PRIMARY KEY AUTOINCREMENT, product_code VARCHAR(50) NOT NULL)",
    "CREATE TABLE tab_import_batch (id INTEGER PRIMARY KEY, module SMALLINT, mode SMALLINT, status SMALLINT, created_count INTEGER,"
    " created_by BIGINT, created_at DATETIME, finished_at DATETIME)",
]


@pytest.fixture
def old_conn():
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conn:
        for ddl in OLD_DDL:
            conn.execute(sa.text(ddl))
    with engine.connect() as conn:
        yield conn
    engine.dispose()


def _seed_boms(conn, n, by, at):
    for i in range(n):
        conn.execute(sa.text("INSERT INTO tab_packaging_bom (created_at, created_by, fg_code) VALUES (:t, :b, :c)"),
                     {"t": at + timedelta(seconds=i % 2), "b": by, "c": f"{by}-{at:%H%M%S}-{i}"})


def _batch_row(conn, bid, count, by, at, *, mode=1, status=2, module=4):
    conn.execute(sa.text("INSERT INTO tab_import_batch VALUES (:i, :m, :mode, :s, :c, :by, :a, :f)"),
                 {"i": bid, "m": module, "mode": mode, "s": status, "c": count, "by": by, "a": at, "f": at + timedelta(seconds=2)})


def _run_mig(conn, fn):
    with Operations.context(MigrationContext.configure(conn)):
        fn()
    conn.commit()


def test_migration_danh_dau_lo_khop_so_dong_con_lech_hoac_chay_thu_thi_bo_qua(old_conn):
    mig = _load_migration()
    assert (mig.revision, mig.down_revision) == ("bombatch784", "fgname784")
    t1, t2, t3 = datetime(2026, 11, 21, 3, 57, 30), datetime(2026, 11, 21, 8, 0, 0), datetime(2026, 11, 22, 9, 0, 0)
    _seed_boms(old_conn, 5, 275, t1)
    _batch_row(old_conn, 98, 5, 275, t1)                       # khớp 5 = 5 -> đánh dấu
    _seed_boms(old_conn, 3, 275, t2)
    _batch_row(old_conn, 99, 4, 275, t2)                       # ghi 4 nhưng chỉ 3 dòng -> bỏ qua
    _seed_boms(old_conn, 2, 5, t3)
    _batch_row(old_conn, 100, 2, 5, t3, mode=0)                # chạy thử -> không xét
    old_conn.commit()
    _run_mig(old_conn, mig.upgrade)
    rows = old_conn.execute(sa.text("SELECT import_batch_id, COUNT(*) FROM tab_packaging_bom GROUP BY 1 ORDER BY 1")).all()
    assert [tuple(r) for r in rows] == [(0, 5), (98, 5)]
    insp = sa.inspect(old_conn)
    assert "import_batch_id" in {c["name"] for c in insp.get_columns("tab_product_price_ledger")}
    assert "ix_pbom_import_batch" in {i["name"] for i in insp.get_indexes("tab_packaging_bom")}
    assert "ix_ppl_import_batch" in {i["name"] for i in insp.get_indexes("tab_product_price_ledger")}


def test_migration_downgrade_bo_cot_va_chi_muc_va_chay_lai_duoc(old_conn):
    mig = _load_migration()
    _run_mig(old_conn, mig.upgrade)
    _run_mig(old_conn, mig.downgrade)
    insp = sa.inspect(old_conn)
    assert "import_batch_id" not in {c["name"] for c in insp.get_columns("tab_packaging_bom")}
    assert "import_batch_id" not in {c["name"] for c in insp.get_columns("tab_product_price_ledger")}
    _run_mig(old_conn, mig.upgrade)
    assert "import_batch_id" in {c["name"] for c in sa.inspect(old_conn).get_columns("tab_packaging_bom")}


def test_chuoi_migration_mot_dau_bombatch784_noi_sau_fgname784_va_cleanup784():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATION.parents[1]))
    script = ScriptDirectory.from_config(cfg)
    assert len(script.get_heads()) == 1                         # đầu chuỗi nay là migration sau (bao-CR-790 phstage790, bao-CR-792 permsplit792)
    assert script.get_revision("bombatch784").down_revision == "fgname784"
    assert script.get_revision("fgname784").down_revision == "cleanup784"
