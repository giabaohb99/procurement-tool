"""duoc-CR-784 phase 02 (migration `srcmerge784`, 25/11/2026) — lần mua của hệ thống = MỘT dòng sổ giá theo `po_item_id` suốt đời.

Phủ: (1) vòng đời dòng sổ: duyệt -> đang mở -> hoàn thành giữ id + số chụp -> đồng bộ / hủy / xóa mềm không đụng nữa,
(2) hai truy vấn cố định của `sync_po_price_ledger`, (3) nạp lại toàn bảng (`sync_history_ledger`) + script `--check` = 0 và dựng lại
từ số không ra đúng khóa cũ, (4) bài canh: không dòng nguồn 1 nào mang ĐMH, (5) API Lịch sử mua hàng: `line_stage` / `is_open`, nhãn
Nguồn, khóa xếp `source`, (6) bộ mã, (7) migration lên / xuống trên SQLite kèm ca va chạm.
"""
import importlib.util
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import openpyxl
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.core import status_catalog
from app.core.packaging_price_codes import (LedgerLineStage, PriceSourceType, is_open_po_line, price_source_text)
from app.modules.packaging_cost.history_service import build_history
from app.modules.product_price import ledger_sync_service as sync
from app.modules.product_price.model import ProductPriceLedger
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_history.service import snapshot_line
from app.modules.purchase_order import service as po_service
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from lich_lam_viec_factory import count_queries
from so_gia_factory_cr784 import add_ledger, add_products, column_values, ledger_rows, make_item, make_po

PO_LINE, HISTORY, MISA = (int(PriceSourceType.PO_LINE), int(PriceSourceType.PURCHASE_HISTORY), int(PriceSourceType.MISA))
OPEN, FINAL = int(LedgerLineStage.OPEN), int(LedgerLineStage.FINAL)
URL = "/api/packaging-cost/history"
MIGRATION = next((Path(__file__).resolve().parents[2] / "backend" / "migrations" / "versions").glob("srcmerge784_*.py"))


def _legacy(db, n=2, code="CPT0075", on="2026-01-01", price=900):
    for i in range(n):
        db.add(PurchaseHistory(po_item_id=None, po_id=0, source="legacy", legacy_key=f"K:{code}:{on}:{i}:{price}", product_code=code,
                               supplier_code="NCC01", company_id=1, order_date=on, unit="Cái", qty_order=10, price=price, vat=8,
                               created_by=0, updated_by=0))
    db.commit()


def _complete(db, po, item):
    item.progress_status = "completed"
    snapshot_line(db, po, item)
    db.commit()


# ── 1. Vòng đời của một dòng sổ ─────────────────────────────────────────────────
def test_vong_doi_duyet_mo_hoan_thanh_chot_cung_mot_id_roi_dong_bang(db):
    po = make_po(db, status="submitted")
    it = make_item(db, po, price=1000, qty_order=1000, vat=8, amount=1080000, progress_status="doc_sent", qty_received=1000)
    po_service.set_status(db, po.id, "approved", 1)                         # duyệt -> dòng đang mở
    (row,) = ledger_rows(db)
    assert (row.source_type, row.source_id, row.line_stage) == (PO_LINE, it.id, OPEN)

    it.price = 1200                                                         # sửa giá khi còn mở -> CÙNG id, giá mới
    db.commit()
    sync.sync_po_price_ledger(db, po)
    assert [(r.id, r.price, r.line_stage) for r in ledger_rows(db)] == [(row.id, Decimal("1200"), OPEN)]

    _complete(db, po, it)                                                   # hoàn thành -> cùng id, số chụp, đã chốt
    (done,) = ledger_rows(db)
    assert (done.id, done.line_stage, done.price, done.amount) == (row.id, FINAL, Decimal("1200"), Decimal("1000000.00"))

    it.price = 5000                                                         # đổi giá ĐMH sau khi chốt: dòng sổ bị đóng băng
    it.qty_order = 7
    db.commit()
    assert sync.sync_po_price_ledger(db, po) == {"inserted": 0, "updated": 0, "deleted": 0}
    frozen = ledger_rows(db)[0]
    assert (frozen.id, frozen.price, frozen.qty, frozen.line_stage) == (row.id, Decimal("1200"), Decimal("1000"), FINAL)


def test_huy_hoac_xoa_mem_don_sau_khi_chot_giu_dong_da_chot_con_dong_dang_mo_thi_mat(db):
    po = make_po(db, status="approved")
    done = make_item(db, po, product_code="CPT0075", progress_status="doc_sent")
    still_open = make_item(db, po, product_code="NAP0085")
    sync.sync_po_price_ledger(db, po)
    assert {r.source_id: r.line_stage for r in ledger_rows(db)} == {done.id: OPEN, still_open.id: OPEN}
    _complete(db, po, done)

    po_service.set_status(db, po.id, "cancelled", 1, "hủy")
    assert [(r.source_id, r.line_stage) for r in ledger_rows(db)] == [(done.id, FINAL)]       # lần mua đã chốt ở lại

    from app.core.base_model import mark_deleted
    mark_deleted(po, 1)
    db.commit()
    assert sync.sync_po_price_ledger(db, po) == {"inserted": 0, "updated": 0, "deleted": 0}
    assert [(r.source_id, r.line_stage) for r in ledger_rows(db)] == [(done.id, FINAL)]


def test_dong_hoan_thanh_ma_chua_tung_vao_so_duoc_chen_thang_la_da_chot(db):
    po = make_po(db, status="approved")
    it = make_item(db, po, progress_status="doc_sent")                      # chưa đồng bộ lần nào
    _complete(db, po, it)
    assert [(r.source_type, r.source_id, r.line_stage, r.doc_id) for r in ledger_rows(db)] == [(PO_LINE, it.id, FINAL, po.id)]


def test_hai_truy_van_co_dinh_moi_don_khong_phu_thuoc_so_dong(db):
    po = make_po(db, status="approved")
    for code in ("A1", "A2", "A3", "A4", "A5"):
        make_item(db, po, product_code=code)
    db.refresh(po)                                                           # đọc lại ĐMH trước: truy vấn nạp lại không tính vào đồng bộ
    _, queries = count_queries(db, lambda: sync.sync_po_price_ledger(db, po, commit=False))
    selects = [q for q in queries if q.lstrip().upper().startswith("SELECT")]
    assert len(selects) == 2, selects


# ── 2. Nạp lại + script ─────────────────────────────────────────────────────────
def _world(db):
    """Một ĐMH có dòng đã hoàn thành + dòng đang mở + hai dòng lịch sử cũ."""
    po = make_po(db, status="approved")
    done = make_item(db, po, product_code="CPT0075", price=1000, progress_status="doc_sent")
    make_item(db, po, product_code="NAP0085", price=200)
    sync.sync_po_price_ledger(db, po)
    _complete(db, po, done)
    _legacy(db, 2)
    sync.sync_history_ledger(db)                                             # lịch sử cũ vào sổ qua đường nạp lại (như script nạp Excel)
    db.commit()
    return po, done


def _keys(db):
    return sorted((r.source_type, r.source_id, r.line_stage, r.product_code, r.price_date, r.price) for r in ledger_rows(db))


def test_script_dung_lai_tu_so_khong_ra_dung_khoa_cu_va_chay_lai_check_bang_0(db):
    from scripts import backfill_product_price_ledger as script
    _world(db)
    before = _keys(db)
    assert len(before) == 4 and {k[0] for k in before} == {PO_LINE, HISTORY}
    db.query(ProductPriceLedger).delete()
    db.commit()
    done = script.run(db, apply=True)
    assert done["inserted"] == 3 and done["po_inserted"] == 1                # legacy x2 + dòng đã chốt (lịch sử); dòng mở do bước ĐMH
    assert _keys(db) == before
    assert script.changes_of(script.run(db, apply=False)) == 0               # --check: khớp, không còn gì để làm
    assert script.changes_of(script.run(db, apply=True)) == 0
    assert _keys(db) == before


def test_script_nang_dong_dang_mo_cua_lich_su_cu_len_chot_va_ghi_so_dem_finalized(db):
    from scripts import backfill_product_price_ledger as script
    po = make_po(db, status="approved")
    it = make_item(db, po, progress_status="completed")
    sync.sync_po_price_ledger(db, po)                                        # ĐMH đã completed trước khi có hook: dòng ở lại đang mở
    db.add(PurchaseHistory(po_item_id=it.id, po_id=po.id, source="system", product_code="CPT0075", supplier_code="NCC01",
                           company_id=1, order_date="2026-10-01", price=1000, vat=8, qty_order=1, created_by=0, updated_by=0))
    db.commit()
    (first,) = ledger_rows(db)
    res = script.run(db, apply=True)
    assert res["finalized"] == 1 and [(r.id, r.line_stage) for r in ledger_rows(db)] == [(first.id, FINAL)]
    assert script.changes_of(script.run(db, apply=False)) == 0


def test_bai_canh_khong_dong_nguon_1_nao_mang_dmh_sau_moi_duong_ghi(db):
    from scripts import backfill_product_price_ledger as script
    _world(db)
    script.run(db, apply=True)
    legacy_ids = {r.id for r in db.query(PurchaseHistory).filter(PurchaseHistory.po_item_id.is_(None))}
    src1 = ledger_rows(db, source_type=HISTORY)
    assert src1 and all(r.doc_id == 0 and r.source_id in legacy_ids for r in src1)
    assert all(r.line_stage == FINAL for r in ledger_rows(db) if r.source_type != PO_LINE)


def test_dong_nguon_1_sai_dang_tro_vao_lich_su_co_dmh_bi_don_roi_dong_chot_duoc_chen_dung_cho(db):
    po = make_po(db, status="approved")
    it = make_item(db, po)
    ph = PurchaseHistory(po_item_id=it.id, po_id=po.id, source="system", product_code="CPT0075", supplier_code="NCC01", company_id=1,
                        order_date="2026-10-01", price=1000, vat=8, qty_order=1, created_by=0, updated_by=0)
    db.add(ph)
    db.commit()
    add_ledger(db, "CPT0075", 1000, "2026-10-01", source_type=PriceSourceType.PURCHASE_HISTORY, source_id=ph.id, doc_id=po.id)
    stats = sync.sync_history_ledger(db)
    db.commit()
    assert (stats["deleted_orphans"], stats["inserted"]) == (1, 1)
    assert [(r.source_type, r.source_id, r.line_stage) for r in ledger_rows(db)] == [(PO_LINE, it.id, FINAL)]


# ── 3. API Lịch sử mua hàng ─────────────────────────────────────────────────────
@pytest.fixture
def api(db, seed, cap_quyen, client_as):  # noqa: F811
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"))
    po = make_po(db, code="PO-A")
    add_ledger(db, "CPT0105", 100, "2026-01-01", supplier="NCC01")                                               # lịch sử cũ (nguồn 1)
    add_ledger(db, "CPT0105", 105, "2026-01-15", source_type=PriceSourceType.MISA, supplier="MX")                # Misa
    add_ledger(db, "CPT0105", 110, "2026-02-01", source_type=PriceSourceType.PO_LINE, line_stage=LedgerLineStage.FINAL,
               doc_id=po.id, supplier="NCC01")                                                                   # ERP đã chốt
    add_ledger(db, "CPT0105", 120, "2026-03-01", source_type=PriceSourceType.PO_LINE, doc_id=po.id, supplier="NCC01")   # ERP đang mở
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True, export=True)
    return client_as(db.get(User, seed.u_req_id))


def _get(api, **params):
    res = api.get(URL, params=params)
    assert res.status_code == 200, res.text
    return res.json()["data"]["items"]


def test_api_tra_line_stage_va_is_open_chi_dong_dmh_dang_mo_la_true(api):
    rows = {r["date"]: r for r in _get(api, codes=["CPT0105"])}
    assert [(rows[d]["source_type"], rows[d]["line_stage"], rows[d]["is_open"]) for d in
            ("2026-01-01", "2026-01-15", "2026-02-01", "2026-03-01")] == [(1, 2, False), (3, 2, False), (2, 2, False), (2, 1, True)]
    assert rows["2026-02-01"]["doc_id"] > 0 and rows["2026-01-01"]["doc_id"] == 0         # số ĐMH vẫn hiện cho dòng đã chốt


def test_khoa_xep_source_theo_nhan_dang_hien_lich_su_truoc_dmh_mo_truoc_misa(api):
    asc = [r["date"] for r in _get(api, codes=["CPT0105"], sort_by="source", sort_dir="asc")]
    assert asc == ["2026-02-01", "2026-01-01", "2026-03-01", "2026-01-15"]      # lịch sử (ERP chốt + cũ, id giảm) < ĐMH mở < Misa
    desc = [r["date"] for r in _get(api, codes=["CPT0105"], sort_by="source", sort_dir="desc")]
    assert desc == ["2026-01-15", "2026-03-01", "2026-02-01", "2026-01-01"]


def test_xuat_excel_cot_nguon_giu_nguyen_chu_cu(api):
    res = api.get(URL + "/export", params={"codes": ["CPT0105"], "sort_by": "date", "sort_dir": "asc"})
    assert res.status_code == 200
    ws = openpyxl.load_workbook(BytesIO(res.content)).active
    assert column_values(ws, "Nguồn") == ["Lịch sử mua hàng", "Sổ Misa", "Lịch sử mua hàng", "Dòng đơn mua hàng"]


def test_mac_dinh_dau_vao_lich_su_dung_ham_service_cung_tra_cac_truong_moi(db, api):
    items = build_history(db, codes=["CPT0105"], page=1, page_size=50)["items"]
    assert sum(1 for i in items if i["is_open"]) == 1 and {i["line_stage"] for i in items} == {OPEN, FINAL}


def test_cong_cu_tro_ly_source_label_giu_nguyen_chu_cu_theo_cap_nguon_giai_doan(db):
    from app.modules.assistant.tools.packaging_cost_format import purchase_point
    from app.modules.product_price.price_state_service import get_price_states
    add_ledger(db, "L1", 100, "2026-01-01")                                                                       # lịch sử cũ
    add_ledger(db, "F1", 100, "2026-01-01", source_type=PriceSourceType.PO_LINE, line_stage=LedgerLineStage.FINAL, doc_id=5)
    add_ledger(db, "O1", 100, "2026-01-01", source_type=PriceSourceType.PO_LINE, doc_id=6)
    add_ledger(db, "M1", 100, "2026-01-01", source_type=PriceSourceType.MISA)
    states = get_price_states(db, {"L1", "F1", "O1", "M1"})
    assert {c: purchase_point(st.p1, {})["source_label"] for c, st in states.items()} == {
        "L1": "Lịch sử mua hàng", "F1": "Lịch sử mua hàng", "O1": "Dòng đơn mua hàng", "M1": "Sổ Misa"}


# ── 4. Bộ mã ────────────────────────────────────────────────────────────────────
def test_bo_ma_giai_doan_va_nhan_nguon_tinh_tu_cap_nguon_giai_doan():
    assert (OPEN, FINAL) == (1, 2)
    names = set(status_catalog.all_sets())
    assert "ledger_line_stage" in names and "price_source_type" in names
    assert is_open_po_line(PO_LINE, OPEN) and not is_open_po_line(PO_LINE, FINAL) and not is_open_po_line(HISTORY, OPEN)
    assert [price_source_text(*pair) for pair in ((PO_LINE, OPEN), (PO_LINE, FINAL), (HISTORY, FINAL), (MISA, FINAL))] == [
        "Dòng đơn mua hàng", "Lịch sử mua hàng", "Lịch sử mua hàng", "Sổ Misa"]


# ── 5. Migration `srcmerge784` trên SQLite ──────────────────────────────────────
OLD_LEDGER = """
CREATE TABLE tab_product_price_ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT, source_type SMALLINT NOT NULL, source_id BIGINT NOT NULL, doc_id BIGINT NOT NULL DEFAULT 0,
  product_code VARCHAR(50) NOT NULL, price_date DATE NOT NULL, price NUMERIC(18,4) NOT NULL DEFAULT 0,
  CONSTRAINT uq_ppl_source UNIQUE (source_type, source_id))
"""
OLD_HISTORY = "CREATE TABLE tab_purchase_history (id INTEGER PRIMARY KEY AUTOINCREMENT, po_item_id BIGINT UNIQUE, po_id BIGINT)"
#  (id sổ, nguồn, source_id, doc_id, mã, giá)
OLD_ROWS = [
    (10, 1, 1, 7, "A", 100),     # lịch sử hệ thống (ph 1 -> ĐMH 101)             -> (2, 101, chốt)
    (11, 1, 2, 7, "B", 110),     # lịch sử hệ thống (ph 2 -> ĐMH 102)             -> (2, 102, chốt)
    (12, 1, 3, 0, "C", 120),     # lịch sử cũ (ph 3, không ĐMH)                   -> giữ nguồn 1, chốt
    (13, 2, 103, 8, "D", 130),   # dòng ĐMH đang mở                               -> (2, 103, mở)
    (14, 2, 102, 7, "B", 111),   # VA CHẠM: ĐMH 102 đã có lịch sử trong sổ (dòng 11) -> bị xóa, lịch sử thắng
    (15, 3, 5, 0, "E", 140),     # Misa                                           -> chốt
]


def _load_migration():
    spec = importlib.util.spec_from_file_location("srcmerge784", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def old_conn():
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(sa.text(OLD_LEDGER))
        conn.execute(sa.text(OLD_HISTORY))
        conn.execute(sa.text("INSERT INTO tab_purchase_history (id, po_item_id, po_id) VALUES (1, 101, 7), (2, 102, 7), (3, NULL, 0)"))
        for row_id, src, sid, doc, code, price in OLD_ROWS:
            conn.execute(sa.text("INSERT INTO tab_product_price_ledger (id, source_type, source_id, doc_id, product_code, price_date, price) "
                                 "VALUES (:i, :t, :s, :d, :c, '2026-01-01', :p)"), dict(i=row_id, t=src, s=sid, d=doc, c=code, p=price))
    with engine.connect() as conn:
        yield conn
    engine.dispose()


def _run(conn, fn):
    with Operations.context(MigrationContext.configure(conn)):
        fn()
    conn.commit()


def _ledger(conn, with_stage=True):
    cols = "id, source_type, source_id, " + ("line_stage" if with_stage else "NULL") + ", product_code, price"
    return [tuple(r) for r in conn.execute(sa.text(f"SELECT {cols} FROM tab_product_price_ledger ORDER BY id"))]


def test_migration_len_gop_lich_su_he_thong_vao_dong_dmh_giu_id_xoa_ca_va_cham(old_conn):
    mig = _load_migration()
    _run(old_conn, mig.upgrade)
    assert _ledger(old_conn) == [
        (10, 2, 101, FINAL, "A", 100), (11, 2, 102, FINAL, "B", 110), (12, 1, 3, FINAL, "C", 120),
        (13, 2, 103, OPEN, "D", 130), (15, 3, 5, FINAL, "E", 140)]
    column = next(c for c in sa.inspect(old_conn).get_columns("tab_product_price_ledger") if c["name"] == "line_stage")
    assert column["nullable"] is False and column["default"] is None            # ghi mới phải đặt rõ, không còn mặc định
    uniques = {tuple(u["column_names"]) for u in sa.inspect(old_conn).get_unique_constraints("tab_product_price_ledger")}
    assert ("source_type", "source_id") in uniques


def test_migration_xuong_tra_dong_chot_ve_nguon_1_va_bo_cot_du_lieu_khong_mat(old_conn):
    mig = _load_migration()
    _run(old_conn, mig.upgrade)
    merged = _ledger(old_conn)
    _run(old_conn, mig.downgrade)
    assert "line_stage" not in {c["name"] for c in sa.inspect(old_conn).get_columns("tab_product_price_ledger")}
    back = _ledger(old_conn, with_stage=False)
    #  Dòng 14 (va chạm) đã bị xóa ở bước lên; mọi dòng còn lại về đúng khóa cũ, cùng id / mã / giá.
    assert back == [(10, 1, 1, None, "A", 100), (11, 1, 2, None, "B", 110), (12, 1, 3, None, "C", 120),
                    (13, 2, 103, None, "D", 130), (15, 3, 5, None, "E", 140)]
    assert [(r[0], r[4], r[5]) for r in merged] == [(r[0], r[4], r[5]) for r in _ledger(old_conn, with_stage=False)]
    _run(old_conn, mig.upgrade)                                                  # lên lại: ra đúng kết quả lần đầu
    assert _ledger(old_conn) == merged


def test_migration_xuong_dong_chot_khong_co_lich_su_o_lai_nguon_2(old_conn):
    mig = _load_migration()
    _run(old_conn, mig.upgrade)
    old_conn.execute(sa.text("DELETE FROM tab_purchase_history WHERE id = 2"))       # dòng 11 mất lịch sử
    old_conn.commit()
    _run(old_conn, mig.downgrade)
    assert {r[0]: (r[1], r[2]) for r in _ledger(old_conn, with_stage=False)}[11] == (2, 102)


def test_migration_head_la_srcmerge784_va_noi_tiep_bompart784():
    mig = _load_migration()
    assert (mig.revision, mig.down_revision) == ("srcmerge784", "bompart784")
    assert (mig.SRC_HISTORY, mig.SRC_PO, mig.OPEN, mig.FINAL) == (HISTORY, PO_LINE, OPEN, FINAL)    # bảng sao khớp enum hiện tại


def test_gia_tri_dong_so_van_dung_sau_migration_voi_model_hien_tai(db):
    """Model hiện tại bắt buộc `line_stage` (không mặc định): chèn thiếu là lỗi, không âm thầm thành một giá trị."""
    from sqlalchemy.exc import IntegrityError
    db.add(ProductPriceLedger(source_type=HISTORY, source_id=1, product_code="X", price_date=date(2026, 1, 1)))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
