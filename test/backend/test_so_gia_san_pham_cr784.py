"""duoc-CR-784 phase 02 — SỔ GIÁ (tab_product_price_ledger) theo từng mốc sửa ĐMH, lịch sử mua và nạp lại dữ liệu cũ."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func

from app.core.packaging_price_codes import PriceSourceType
from app.modules.product_price import ledger_sync_service as sync
from app.modules.product_price.model import ProductPriceLedger
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_history.service import snapshot_line
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import POItem
from app.modules.purchase_order.schema import POItemIn, POUpdate
from so_gia_factory_cr784 import ledger_rows, make_item, make_po

PO_LINE = int(PriceSourceType.PO_LINE)
HISTORY = int(PriceSourceType.PURCHASE_HISTORY)


def _approve(db, po, user=1):
    return po_service.set_status(db, po.id, "approved", user)


# ── Điều kiện vào sổ: chỉ đơn từ trạng thái ĐÃ DUYỆT ────────────────────────────
@pytest.mark.parametrize("status", ["draft", "submitted", "rejected", "cancelled"])
def test_don_chua_duyet_hoac_da_huy_khong_vao_so(db, status):
    po = make_po(db, status=status)
    make_item(db, po)
    sync.sync_po_price_ledger(db, po)
    assert ledger_rows(db) == []


def test_duyet_don_thi_vao_so_bo_duyet_thi_ra_khoi_so(db):
    po = make_po(db, status="submitted")
    it = make_item(db, po, price=1000)
    _approve(db, po)
    rows = ledger_rows(db)
    assert len(rows) == 1
    r = rows[0]
    assert (r.source_type, r.source_id, r.doc_id) == (PO_LINE, it.id, po.id)
    assert (r.product_code, r.supplier_code, r.company_id) == ("CPT0075", "NCC01", 1)
    assert r.price_date == date(2026, 10, 1)
    assert (r.price, r.vat, r.qty, r.unit) == (Decimal("1000"), Decimal("8"), Decimal("1000"), "Cái")

    po_service.set_status(db, po.id, "draft", 1, "bỏ duyệt")
    assert ledger_rows(db) == []


def test_huy_don_thi_ra_khoi_so(db):
    po = make_po(db, status="approved")
    make_item(db, po)
    sync.sync_po_price_ledger(db, po)
    assert len(ledger_rows(db)) == 1
    po_service.set_status(db, po.id, "cancelled", 1, "hủy")
    assert ledger_rows(db) == []


def test_don_xoa_mem_thi_ra_khoi_so(db):
    from app.core.base_model import mark_deleted
    po = make_po(db, status="approved")
    make_item(db, po)
    sync.sync_po_price_ledger(db, po)
    mark_deleted(po, 1)
    db.commit()
    sync.sync_po_price_ledger(db, po)
    assert ledger_rows(db) == []


# ── Sửa dòng: cùng id dòng sổ, giá trị mới ──────────────────────────────────────
def test_sua_gia_sl_vat_giu_nguyen_id_dong_so(db):
    po = make_po(db, status="processing")
    it = make_item(db, po, price=1000, qty_order=10, vat=8)
    sync.sync_po_price_ledger(db, po)
    first = ledger_rows(db)[0]

    po_service.update_po(db, po.id, POUpdate(items=[
        POItemIn(id=it.id, product_code="CPT0075", product_name="Chai 1L", unit="Cái", qty_order=25, price=1200, vat=10)
    ]), 1)
    rows = ledger_rows(db)
    assert len(rows) == 1 and rows[0].id == first.id
    assert (rows[0].price, rows[0].qty, rows[0].vat) == (Decimal("1200"), Decimal("25"), Decimal("10"))


def test_xoa_dong_hang_thi_mat_dong_so(db):
    po = make_po(db, status="processing")
    a = make_item(db, po, product_code="CPT0075")
    b = make_item(db, po, product_code="NAP0085")
    sync.sync_po_price_ledger(db, po)
    assert len(ledger_rows(db)) == 2

    po_service.update_po(db, po.id, POUpdate(items=[
        POItemIn(id=a.id, product_code="CPT0075", product_name="Chai 1L", unit="Cái", qty_order=1000, price=1000)
    ]), 1)
    rows = ledger_rows(db)
    assert [r.source_id for r in rows] == [a.id] and b.id not in {r.source_id for r in rows}


def test_huy_dong_thi_mat_dong_so(db):
    po = make_po(db, status="approved")
    it = make_item(db, po)
    sync.sync_po_price_ledger(db, po)
    po_service.set_item_progress(db, po.id, it.id, "cancelled", "NCC hết hàng", 1)
    assert ledger_rows(db) == []


def test_dong_ma_hang_trong_khong_vao_so(db):
    po = make_po(db, status="approved")
    make_item(db, po, product_code="")
    sync.sync_po_price_ledger(db, po)
    assert ledger_rows(db) == []


def test_ngoai_te_quy_ve_vnd_theo_ti_gia(db):
    po = make_po(db, status="approved")
    make_item(db, po, price=2, currency="USD", exchange_rate=25000)
    sync.sync_po_price_ledger(db, po)
    assert ledger_rows(db)[0].price == Decimal("50000")


def test_ngay_don_hong_thi_bo_dong(db):
    po = make_po(db, status="approved", order_date="khong-phai-ngay")
    make_item(db, po)
    sync.sync_po_price_ledger(db, po)
    assert ledger_rows(db) == []


def test_goi_lai_khong_dung_lai_dong_khong_doi(db):
    po = make_po(db, status="approved")
    make_item(db, po)
    assert sync.sync_po_price_ledger(db, po)["inserted"] == 1
    stats = sync.sync_po_price_ledger(db, po)
    assert stats == {"inserted": 0, "updated": 0, "deleted": 0}


def test_gia_doi_ngoai_hook_reprice_duoc_hoa_giai_khi_dong_bo(db):
    """Mô phỏng `reprice_po` (hook CHƯA gắn — việc treo): đổi giá thẳng rồi đồng bộ thì dòng sổ đổi theo, cùng id."""
    po = make_po(db, status="approved")
    it = make_item(db, po, price=1000)
    sync.sync_po_price_ledger(db, po)
    first_id = ledger_rows(db)[0].id
    it.price = 1500
    db.commit()
    assert sync.sync_po_price_ledger(db, po)["updated"] == 1
    row = ledger_rows(db)[0]
    assert (row.id, row.price) == (first_id, Decimal("1500"))


# ── Lịch sử mua hàng: nguồn 1, thay thế nguồn 2 ─────────────────────────────────
def test_dong_vao_completed_thi_co_nguon_1_va_mat_nguon_2(db):
    po = make_po(db, status="approved")
    it = make_item(db, po, price=1000, progress_status="doc_sent", qty_received=1000, invoice_no="HD1")
    sync.sync_po_price_ledger(db, po)
    assert [r.source_type for r in ledger_rows(db)] == [PO_LINE]

    it.progress_status = "completed"
    snapshot_line(db, po, it)
    db.commit()
    rows = ledger_rows(db)
    assert [r.source_type for r in rows] == [HISTORY]
    ph = db.query(PurchaseHistory).one()
    assert rows[0].source_id == ph.id and rows[0].price == Decimal("1000")

    # đồng bộ lại sau khi dòng đã có lịch sử: không dựng lại nguồn 2
    sync.sync_po_price_ledger(db, po)
    assert [r.source_type for r in ledger_rows(db)] == [HISTORY]


def test_snapshot_ngoai_te_quy_vnd(db):
    po = make_po(db, status="approved")
    it = make_item(db, po, price=2, currency="USD", exchange_rate=25000, progress_status="completed")
    snapshot_line(db, po, it)
    db.commit()
    assert ledger_rows(db, source_type=HISTORY)[0].price == Decimal("50000")


def test_loi_so_gia_khong_chan_dong_lich_su(db, monkeypatch):
    """Hook sổ giá hỏng thì lịch sử mua vẫn ghi được (sổ giá dựng lại được bằng script)."""
    def boom(*_a, **_k):
        raise RuntimeError("giả lập lỗi sổ giá")
    monkeypatch.setattr(sync, "record_history_row", boom)
    po = make_po(db, status="approved")
    it = make_item(db, po, progress_status="completed")
    assert snapshot_line(db, po, it) is not None
    db.commit()
    assert db.query(PurchaseHistory).count() == 1 and ledger_rows(db) == []


def test_loi_csdl_giua_chung_so_gia_chi_lui_phan_so_gia(db, monkeypatch):
    """bao-CR-789: lỗi CSDL GIỮA CHỪNG phần sổ giá (đã thêm dòng rồi mới hỏng) chỉ lùi phần sổ giá trong savepoint; dòng
    lịch sử vẫn lưu và phiên commit tiếp được (trước đây phiên có thể kẹt trạng thái lỗi)."""
    def half_then_boom(db_, ph, *_a, **_k):
        db_.add(ProductPriceLedger(source_type=HISTORY, source_id=ph.id, product_code="X", price=1,
                                   price_date=date(2026, 1, 1)))
        db_.flush()
        raise RuntimeError("giả lập lỗi sau khi đã ghi một phần sổ giá")
    monkeypatch.setattr(sync, "record_history_row", half_then_boom)
    po = make_po(db, status="approved")
    it = make_item(db, po, progress_status="completed")
    assert snapshot_line(db, po, it) is not None
    db.commit()
    assert db.query(PurchaseHistory).count() == 1
    assert ledger_rows(db) == [], "dòng sổ giá ghi dở phải bị lùi cùng savepoint"


def test_hook_trong_sync_po_khong_nem_loi_khi_hong(db, monkeypatch):
    po = make_po(db, status="approved")
    make_item(db, po)
    monkeypatch.setattr(sync, "values_from_line", lambda *_a: (_ for _ in ()).throw(RuntimeError("hỏng")))
    assert sync.sync_po_price_ledger(db, po) == {"inserted": 0, "updated": 0, "deleted": 0}


# ── Nạp lại dữ liệu cũ (legacy) ─────────────────────────────────────────────────
def _legacy(db, n, code="CPT0075", on="2026-09-01", price=900):
    for i in range(n):
        db.add(PurchaseHistory(po_item_id=None, po_id=0, source="legacy", legacy_key=f"K:{code}:{on}:{i}:{price}",
                               product_code=code, supplier_code="NCC01", company_id=1, order_date=on, unit="Cái",
                               qty_order=10, price=price, vat=8, created_by=0, updated_by=0))
    db.commit()


def test_nap_lai_legacy_xoa_mo_coi_chen_moi_chay_lan_hai_khong_doi(db):
    _legacy(db, 3)
    # Dòng hệ thống nằm SAU các dòng legacy: giữ id tăng dần như MySQL (SQLite tái dùng id lớn nhất khi xóa hết đuôi).
    db.add(PurchaseHistory(po_item_id=None, po_id=0, source="system", product_code="NAP0085", supplier_code="NCC01",
                           company_id=1, order_date="2026-09-05", price=200, vat=8, qty_order=1, created_by=0,
                           updated_by=0))
    db.commit()
    first = sync.sync_history_ledger(db)
    db.commit()
    assert first["inserted"] == 4 and db.query(ProductPriceLedger).count() == 4

    # giả lập script nạp lại: xóa toàn bộ legacy rồi chèn lại (id đổi)
    db.query(PurchaseHistory).filter(PurchaseHistory.source == "legacy").delete()
    db.commit()
    _legacy(db, 2, price=950)
    second = sync.sync_history_ledger(db)
    db.commit()
    assert (second["deleted_orphans"], second["inserted"]) == (3, 2)
    assert sorted(r.price for r in ledger_rows(db)) == [Decimal("200"), Decimal("950"), Decimal("950")]

    third = sync.sync_history_ledger(db)
    assert (third["inserted"], third["deleted_orphans"], third["deleted_covered_po_lines"]) == (0, 0, 0)


def test_sync_history_dem_ngay_tuong_lai_gia_0_ngay_hong(db):
    future = (date.today().replace(year=date.today().year + 1)).isoformat()
    _legacy(db, 1, on=future)
    _legacy(db, 1, on="1970-01-01", price=500)   # ngoài dải 1990..2100 → bỏ
    _legacy(db, 1, code="X1", price=0)
    stats = sync.sync_history_ledger(db)
    assert stats["future_date"] == 1 and stats["zero_price"] == 1 and stats["skipped_bad_row"] == 1
    assert stats["inserted"] == 2


def test_sync_history_ti_gia_lay_tu_dong_dmh_va_dem_thieu(db):
    po = make_po(db, status="approved")
    usd = make_item(db, po, price=2, currency="USD", exchange_rate=25000, progress_status="completed")
    db.add(PurchaseHistory(po_item_id=usd.id, po_id=po.id, source="system", product_code="CPT0075",
                           supplier_code="NCC01", company_id=1, order_date="2026-10-01", price=2, vat=8,
                           qty_order=1, created_by=0, updated_by=0))
    db.add(PurchaseHistory(po_item_id=987654, po_id=po.id, source="system", product_code="CPT0075",
                           supplier_code="NCC01", company_id=1, order_date="2026-10-02", price=3, vat=8,
                           qty_order=1, created_by=0, updated_by=0))
    db.commit()
    stats = sync.sync_history_ledger(db)
    prices = sorted(r.price for r in ledger_rows(db))
    assert prices == [Decimal("3"), Decimal("50000")]
    assert stats["foreign_currency"] == 1 and stats["missing_po_item"] == 1


def test_sync_history_xoa_nguon_2_da_co_lich_su(db):
    po = make_po(db, status="approved")
    it = make_item(db, po)
    sync.sync_po_price_ledger(db, po)
    db.add(PurchaseHistory(po_item_id=it.id, po_id=po.id, source="system", product_code="CPT0075", supplier_code="NCC01",
                           company_id=1, order_date="2026-10-01", price=1000, vat=8, qty_order=1, created_by=0,
                           updated_by=0))
    db.commit()
    stats = sync.sync_history_ledger(db)
    assert stats["deleted_covered_po_lines"] == 1
    assert [r.source_type for r in ledger_rows(db)] == [HISTORY]


def test_dry_run_khong_ghi(db):
    _legacy(db, 2)
    stats = sync.sync_history_ledger(db, dry_run=True)
    assert stats["inserted"] == 2 and db.query(func.count(ProductPriceLedger.id)).scalar() == 0


# ── Tên kho trên dòng sổ (duoc-CR-784) ──────────────────────────────────────────
def _kho(db):
    from app.modules.catalog.model import Warehouse
    db.add(Warehouse(code="HL", name="Kho Hà Long", created_by=1, updated_by=1))
    db.commit()


def test_nguon_2_lay_ten_kho_tu_danh_muc_hoac_giu_ma_va_cap_nhat_khi_doi_kho(db):
    _kho(db)
    po = make_po(db, status="approved")
    a = make_item(db, po, warehouse_code="HL")
    b = make_item(db, po, warehouse_code="MA_LA")            # mã không có trong danh mục: giữ chính mã
    c = make_item(db, po, warehouse_code="")
    sync.sync_po_price_ledger(db, po)
    names = {r.source_id: r.warehouse_name for r in ledger_rows(db)}
    assert names == {a.id: "Kho Hà Long", b.id: "MA_LA", c.id: None}
    a.warehouse_code = ""
    db.commit()
    assert sync.sync_po_price_ledger(db, po)["updated"] == 1
    assert {r.source_id: r.warehouse_name for r in ledger_rows(db)}[a.id] is None


def test_nguon_1_lay_ten_kho_tu_extra_cua_dong_lich_su_ca_luc_chen_moi_lan_nap_lai(db):
    import json
    _kho(db)
    po = make_po(db, status="approved")
    it = make_item(db, po, warehouse_code="HL", progress_status="completed")
    snapshot_line(db, po, it)                                 # đường thật: chụp lịch sử + ghi sổ nguồn 1
    db.commit()
    assert [r.warehouse_name for r in ledger_rows(db, source_type=HISTORY)] == ["Kho Hà Long"]
    # dòng lịch sử cũ (đã có trong sổ từ trước khi sổ có cột kho) được điền khi nạp lại
    ph = db.query(PurchaseHistory).one()
    ph.extra = json.dumps({"warehouse_code": "HL"})
    ledger_rows(db, source_type=HISTORY)[0].warehouse_name = None
    db.commit()
    assert sync.sync_history_ledger(db)["updated_warehouse"] == 1
    assert [r.warehouse_name for r in ledger_rows(db, source_type=HISTORY)] == ["Kho Hà Long"]
    assert sync.sync_history_ledger(db)["updated_warehouse"] == 0   # chạy lại không đổi gì
    ph.extra = "không phải JSON"                               # JSON hỏng: coi như không có kho, không nổ
    db.commit()
    assert sync.history_warehouse_code(ph) == ""


# ── Script nạp lại ──────────────────────────────────────────────────────────────
def test_script_backfill_chay_thu_roi_ghi_roi_check_exit_0(db, capsys):
    from scripts import backfill_product_price_ledger as script
    po = make_po(db, status="approved")
    make_item(db, po)
    _legacy(db, 2)
    dry = script.run(db, apply=False)
    assert dry["inserted"] == 2 and dry["po_inserted"] == 1 and db.query(ProductPriceLedger).count() == 0
    done = script.run(db, apply=True)
    assert script.changes_of(done) == 3 and db.query(ProductPriceLedger).count() == 3
    assert script.changes_of(script.run(db, apply=False)) == 0   # --check: không còn lệch


def test_script_don_het_du_dieu_kien_thi_don_dong_so_cu(db):
    from scripts import backfill_product_price_ledger as script
    po = make_po(db, status="approved")
    make_item(db, po)
    script.run(db, apply=True)
    po.status = "cancelled"
    db.commit()
    res = script.run(db, apply=True)
    assert res["po_deleted"] == 1 and db.query(ProductPriceLedger).count() == 0


def test_po_import_goi_hook_khi_apply():
    """`po_import.run` (đường nhập Misa cũ) phải đồng bộ sổ giá khi ghi thật — dựng cả tệp Excel quá nặng, khóa bằng mã nguồn."""
    import inspect
    from app.modules.import_tool import po_import
    src = inspect.getsource(po_import.run)
    assert "if apply:\n            # duoc-CR-784" in src and "sync_po_price_ledger(db, po, commit=False)" in src


# ── Lịch sử hỏng ngày: không được làm mất giá ───────────────────────────────────
def test_lich_su_hong_ngay_khong_xoa_dong_dmh_giu_gia_trong_so(db):
    po = make_po(db, status="approved")
    it = make_item(db, po, price=1000, progress_status="doc_sent")
    sync.sync_po_price_ledger(db, po)
    po.order_date = "khong-phai-ngay"          # lịch sử chụp theo ngày đơn → ngày hỏng, KHÔNG vào được sổ
    it.progress_status = "completed"
    snapshot_line(db, po, it)
    db.commit()
    po.order_date = "2026-10-01"               # đơn được sửa lại ngày hợp lệ sau đó (lịch sử vẫn giữ ngày hỏng)
    db.commit()
    sync.sync_po_price_ledger(db, po)
    assert [r.source_type for r in ledger_rows(db)] == [PO_LINE]       # dòng ĐMH còn nguyên, giá không biến mất


def test_sync_history_dem_lich_su_hong_ngay_va_khong_xoa_nguon_2(db):
    po = make_po(db, status="approved")
    it = make_item(db, po)
    sync.sync_po_price_ledger(db, po)
    db.add(PurchaseHistory(po_item_id=it.id, po_id=po.id, source="system", product_code="CPT0075", supplier_code="NCC01",
                           company_id=1, order_date="31/12/2026", price=1000, vat=8, qty_order=1, created_by=0,
                           updated_by=0))
    db.commit()
    stats = sync.sync_history_ledger(db)
    assert (stats["skipped_bad_date"], stats["skipped_bad_row"], stats["deleted_covered_po_lines"]) == (1, 1, 0)
    assert [r.source_type for r in ledger_rows(db)] == [PO_LINE]


def test_hoa_ngay_dong_chuyen_tu_dmh_sang_lich_su_khong_doi_cho_lan_1_lan_2(db):
    """Hai ĐMH cùng ngày, cùng mã: dòng của ĐMH cũ chuyển sang lịch sử (id sổ mới lớn hơn) vẫn là lần 2."""
    from app.modules.product_price.price_state_service import get_price_states
    old_po = make_po(db, code="PO1", status="approved")
    new_po = make_po(db, code="PO2", misa_code="M2", status="approved")
    a = make_item(db, old_po, price=900)
    make_item(db, new_po, price=1000)
    sync.sync_po_price_ledger(db, old_po)
    sync.sync_po_price_ledger(db, new_po)
    before = get_price_states(db, {"CPT0075"})["CPT0075"]
    assert (before.p1.price, before.p2.price) == (Decimal(1000), Decimal(900))
    a.progress_status = "completed"
    snapshot_line(db, old_po, a)
    db.commit()
    assert {r.source_type for r in ledger_rows(db, doc_id=old_po.id)} == {HISTORY}
    after = get_price_states(db, {"CPT0075"})["CPT0075"]
    assert (after.p1.price, after.p2.price) == (Decimal(1000), Decimal(900))
