"""bao-CR-790 — lịch sử mua hàng có từ lúc HÀNG VỀ KHO, đồng bộ theo ĐMH tới khi dòng hoàn thành. CHỈ kiểm phần vừa làm:

- dòng ĐMH đã duyệt, đã nhận hàng -> có bản ghi ĐANG MỞ; chưa nhận thì chưa có;
- đổi giá / SL trên ĐMH -> cập nhật ĐÚNG bản ghi đó (không sinh bản ghi thứ hai);
- dòng hủy, SL nhận về 0, dòng bị xóa, ĐMH hủy / bỏ duyệt / xóa mềm -> bản ghi đang mở bị xóa;
- dòng hoàn thành -> chốt đúng bản ghi đang mở (id giữ nguyên) và chốt dòng sổ giá; bản ghi đã chốt không bị đụng nữa;
- bản ghi đang mở KHÔNG chốt dòng sổ giá (sổ giá vẫn đi theo ĐMH), kể cả khi chạy đồng bộ toàn bảng;
- các đường thật: lưu lần nhận hàng (`update_po`), hủy dòng (`set_item_progress`), đổi trạng thái đơn (`set_status`);
- lỗi ở phần lịch sử không làm hỏng phiên của thao tác chính.
"""
import json

import pytest

from app.core.packaging_price_codes import LedgerLineStage, PriceSourceType
from app.modules.product.model import Product
from app.modules.product_price.ledger_sync_service import sync_history_ledger, sync_po_price_ledger
from app.modules.product_price.model import ProductPriceLedger
from app.modules.purchase_history import service as history_service
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_history.service import snapshot_line, sync_po_history, sync_po_history_safe
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.schema import DeliveryIn, POItemIn, POUpdate
from app.modules.purchase_order.serializer import _out
from app.modules.supplier.model import Supplier
from so_gia_factory_cr784 import make_item, make_po

OPEN, FINAL = int(LedgerLineStage.OPEN), int(LedgerLineStage.FINAL)
NOTHING = {"inserted": 0, "updated": 0, "deleted": 0, "finalized": 0}


def _history(db) -> list[PurchaseHistory]:
    db.expire_all()
    return db.query(PurchaseHistory).order_by(PurchaseHistory.id).all()


def _ledger(db) -> list[ProductPriceLedger]:
    db.expire_all()
    return db.query(ProductPriceLedger).order_by(ProductPriceLedger.id).all()


def _received(db, **over):
    """ĐMH đã duyệt có một dòng ĐÃ NHẬN HÀNG (500 / 1000)."""
    po = make_po(db, status="approved", order_date="2026-11-19")
    base = dict(product_code="CHT0230", product_name="Chai HDPE 550ml", qty_received=500, amount=540000,
                progress_status="received", warehouse_code="KHO1")
    base.update(over)
    return po, make_item(db, po, **base)


# ── Sinh bản ghi lúc nhận hàng ────────────────────────────────────────────────────────────────────────────────────
def test_received_line_gets_open_record_and_unreceived_line_does_not(db):
    po, got = _received(db)
    make_item(db, po, product_code="NAP0001", product_name="Nắp", progress_status="ordered")

    stats = sync_po_history(db, po)
    db.commit()

    rows = _history(db)
    assert stats == {**NOTHING, "inserted": 1}
    assert len(rows) == 1
    h = rows[0]
    assert (h.po_item_id, h.po_id, h.po_code, h.product_code) == (got.id, po.id, "PO0001", "CHT0230")
    assert (h.line_stage, h.completed_at, h.source) == (OPEN, "", "system")
    assert (h.order_date, h.supplier_code, h.company_id) == ("2026-11-19", "NCC01", 1)
    assert (float(h.price), float(h.qty_order), float(h.vat), float(h.amount)) == (1000, 1000, 8, 540000)
    extra = json.loads(h.extra)
    assert extra["qty_received"] == 500 and extra["warehouse_code"] == "KHO1"


def test_second_sync_changes_nothing(db):
    po, _ = _received(db)
    sync_po_history(db, po)
    db.commit()

    assert sync_po_history(db, po) == NOTHING
    db.commit()
    assert len(_history(db)) == 1


def test_price_change_updates_the_same_record(db):
    po, it = _received(db)
    sync_po_history(db, po)
    db.commit()
    first_id = _history(db)[0].id

    it.price, it.qty_received, it.amount = 1250.5, 800, 1080432
    db.commit()
    stats = sync_po_history(db, po)
    db.commit()

    rows = _history(db)
    assert stats == {**NOTHING, "updated": 1}
    assert [r.id for r in rows] == [first_id]
    assert (float(rows[0].price), float(rows[0].amount), rows[0].line_stage) == (1250.5, 1080432, OPEN)
    assert json.loads(rows[0].extra)["qty_received"] == 800


# ── Bản ghi đang mở bị xóa khi dòng hết đủ điều kiện ───────────────────────────────────────────────────────────────
def _cancel_line(db, po, it):
    it.progress_status = "cancelled"


def _unreceive(db, po, it):
    it.qty_received = 0


def _delete_line(db, po, it):
    db.delete(it)


def _soft_delete_order(db, po, it):
    po.is_deleted = True


def _unapprove_order(db, po, it):
    po.status = "draft"


def _cancel_order(db, po, it):
    po.status = "cancelled"


@pytest.mark.parametrize("change", [_cancel_line, _unreceive, _delete_line, _soft_delete_order, _unapprove_order,
                                    _cancel_order])
def test_open_record_removed_when_line_no_longer_counts(db, change):
    po, it = _received(db)
    sync_po_history(db, po)
    db.commit()
    assert len(_history(db)) == 1

    change(db, po, it)
    db.commit()
    stats = sync_po_history(db, po)
    db.commit()

    assert stats == {**NOTHING, "deleted": 1}
    assert _history(db) == []


def test_unapproved_order_writes_nothing(db):
    po = make_po(db, status="submitted")
    make_item(db, po, qty_received=100)

    assert sync_po_history(db, po) == NOTHING
    db.commit()
    assert _history(db) == []


# ── Chốt khi dòng hoàn thành ─────────────────────────────────────────────────────────────────────────────────────
def test_completion_finalizes_the_open_record_and_the_ledger_row(db):
    po, it = _received(db)
    sync_po_price_ledger(db, po)
    sync_po_history(db, po)
    db.commit()
    first_id = _history(db)[0].id
    assert [(r.source_type, r.line_stage) for r in _ledger(db)] == [(int(PriceSourceType.PO_LINE), OPEN)]

    it = db.get(POItem, it.id)
    it.price = 1500
    it.progress_status = "completed"
    db.commit()
    assert snapshot_line(db, db.get(PurchaseOrder, po.id), it) is not None
    db.commit()

    rows = _history(db)
    assert [r.id for r in rows] == [first_id]
    assert (rows[0].line_stage, float(rows[0].price)) == (FINAL, 1500) and rows[0].completed_at
    ledger = _ledger(db)
    assert [(r.source_type, r.source_id, r.line_stage, float(r.price)) for r in ledger] == [
        (int(PriceSourceType.PO_LINE), it.id, FINAL, 1500)]
    assert snapshot_line(db, db.get(PurchaseOrder, po.id), db.get(POItem, it.id)) is None      # chốt rồi thì thôi


def test_final_record_is_never_touched_again(db):
    po, it = _received(db)
    sync_po_history(db, po)
    snapshot_line(db, po, it)
    db.commit()

    it = db.get(POItem, it.id)
    po = db.get(PurchaseOrder, po.id)
    it.price = 9999
    po.status = "cancelled"
    db.commit()
    assert sync_po_history(db, po) == NOTHING
    db.commit()

    rows = _history(db)
    assert len(rows) == 1 and (rows[0].line_stage, float(rows[0].price)) == (FINAL, 1000)


def test_completed_line_without_record_is_finalized(db):
    po, it = _received(db, progress_status="completed")

    stats = sync_po_history(db, po)
    db.commit()

    rows = _history(db)
    assert stats == {**NOTHING, "finalized": 1}
    assert len(rows) == 1 and rows[0].line_stage == FINAL and rows[0].completed_at


# ── Sổ giá: bản ghi đang mở không chốt dòng sổ ───────────────────────────────────────────────────────────────────
def test_open_record_does_not_finalize_ledger_even_in_full_sync(db):
    po, it = _received(db)
    sync_po_price_ledger(db, po)
    sync_po_history(db, po)
    db.commit()

    stats = sync_history_ledger(db)
    db.commit()

    assert (stats["inserted"], stats["finalized"], stats["reopened"]) == (0, 0, 0)
    assert [(r.line_stage, float(r.price)) for r in _ledger(db)] == [(OPEN, 1000)]

    it = db.get(POItem, it.id)
    it.price = 1300
    db.commit()
    sync_po_price_ledger(db, db.get(PurchaseOrder, po.id))
    assert [(r.line_stage, float(r.price)) for r in _ledger(db)] == [(OPEN, 1300)]     # sổ giá vẫn đi theo ĐMH


def test_full_sync_still_finalizes_ledger_for_final_record(db):
    po, it = _received(db)
    sync_po_price_ledger(db, po)
    db.add(PurchaseHistory(po_item_id=it.id, po_id=po.id, po_code=po.code, product_code="CHT0230", supplier_code="NCC01",
                           company_id=1, order_date="2026-11-19", qty_order=1000, price=1000, vat=8, amount=540000,
                           completed_at="2026-11-25"))
    db.commit()

    stats = sync_history_ledger(db)
    db.commit()

    assert stats["finalized"] == 1
    assert [r.line_stage for r in _ledger(db)] == [FINAL]


# ── Các đường thật của ĐMH ────────────────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def order(db, seed):
    uid = seed.u_nstm_id
    db.add(Product(code="CHT0230", name="Chai HDPE 550ml", unit="Cái"))
    db.add(Supplier(code="PHL", name="Công ty Cổ phần PHL"))
    po = PurchaseOrder(code="PO00790", misa_code="MS790", supplier_code="PHL", supplier_name="Công ty Cổ phần PHL",
                       order_date="2026-11-19", status="approved", company_id=1, created_by=uid, updated_by=uid,
                       currency="VND", exchange_rate=1)
    db.add(po)
    db.flush()
    db.add(POItem(po_id=po.id, product_code="CHT0230", product_name="Chai HDPE 550ml", unit="Cái", item_group="Chai",
                  qty_order=2000, price=5105, vat=8, warehouse_code="KHO1", currency="VND", exchange_rate=1,
                  progress_status="ordered", created_by=uid, updated_by=uid))
    db.commit()
    return po, uid


def _save_receipt(db, po, qty, uid):
    """Đúng cách màn web lưu lần nhận hàng: lấy chi tiết đơn, thêm lần giao, gửi lại nguyên đơn qua `update_po`."""
    data = _out(db, db.get(PurchaseOrder, po.id))
    items = []
    for it in data["items"]:
        deliveries = [dict(d) for d in it["deliveries"]]
        deliveries.append({"delivery_no": len(deliveries) + 1, "ship_qty": qty, "received_qty": qty,
                           "received_date": "2026-11-24", "warehouse_code": "KHO1", "ship_unit": "Cái"})
        items.append(POItemIn.model_validate({**it, "deliveries": [DeliveryIn.model_validate(d) for d in deliveries]}))
    po_service.update_po(db, po.id, POUpdate(items=items), uid)


def test_saving_a_receipt_creates_the_record(db, order):
    po, uid = order
    assert _history(db) == []                                    # đã duyệt nhưng chưa nhận hàng: chưa có lịch sử

    _save_receipt(db, po, 2048, uid)

    rows = _history(db)
    assert len(rows) == 1
    h = rows[0]
    assert (h.po_code, h.product_code, h.supplier_code, h.line_stage) == ("PO00790", "CHT0230", "PHL", OPEN)
    assert (float(h.price), float(h.qty_order)) == (5105, 2000)
    assert json.loads(h.extra)["qty_received"] == 2048
    assert float(h.amount) == pytest.approx(2048 * 5105 * 1.08, abs=1)      # thành tiền theo SL thực nhận, gồm VAT
    assert [r.line_stage for r in _ledger(db)] == [OPEN]


def test_cancelling_the_line_removes_the_record(db, order):
    po, uid = order
    _save_receipt(db, po, 2048, uid)
    item = db.query(POItem).filter(POItem.po_id == po.id).one()

    po_service.set_item_progress(db, po.id, item.id, "cancelled", "nhà cung cấp giao sai hàng", uid)

    assert _history(db) == []


def test_order_status_change_removes_and_restores_the_record(db, order):
    po, uid = order
    _save_receipt(db, po, 2048, uid)

    po_service.set_status(db, po.id, "cancelled", uid, "hủy thử")
    assert _history(db) == []

    po_service.set_status(db, po.id, "received", uid)
    rows = _history(db)
    assert len(rows) == 1 and rows[0].line_stage == OPEN


# ── Canh: chỗ nào đồng bộ sổ giá theo ĐMH thì cũng phải đồng bộ lịch sử ───────────────────────────────────────────────
def test_every_order_change_point_syncs_history_too():
    """Hàm nào gọi `sync_po_price_ledger` (ĐMH vừa đổi) mà quên `sync_po_history_safe` thì lịch sử giữ giá cũ / giữ dòng đã hủy."""
    import inspect

    from app.modules.import_tool import po_import
    from app.modules.import_tool import service as import_service
    from app.modules.purchase_order import edit_service, price_adjust_service, progress_service

    sites = [edit_service.update_po, edit_service.delete_po, edit_service.set_status, progress_service.set_item_progress,
             price_adjust_service.adjust_prices, import_service._revert_po]
    for fn in sites:
        source = inspect.getsource(fn)
        assert "sync_po_price_ledger(" in source and "sync_po_history_safe(" in source, fn.__name__
    whole = inspect.getsource(po_import)
    assert whole.count("sync_po_price_ledger(db, po, commit=False)") == whole.count("sync_po_history_safe(db, po, commit=False)") == 1


# ── Lỗi ở phần lịch sử không làm hỏng thao tác chính ──────────────────────────────────────────────────────────────
def test_failure_is_swallowed_and_session_stays_usable(db, monkeypatch):
    po, it = _received(db)

    def boom(*args, **kwargs):
        raise RuntimeError("hỏng giả")

    monkeypatch.setattr(history_service, "_line_values", boom)
    assert sync_po_history_safe(db, po) == {}

    it = db.get(POItem, it.id)
    it.note = "phiên vẫn ghi được"
    db.commit()
    assert db.get(POItem, it.id).note == "phiên vẫn ghi được"
    assert _history(db) == []
