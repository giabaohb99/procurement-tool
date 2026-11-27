"""Sửa giá sau duyệt của Đơn mua hàng — đổi SL đặt / Đơn giá / VAT mà đơn vẫn giữ trạng thái đã duyệt.

Khóa sau duyệt CR-108 vẫn đứng nguyên cho đường Lưu chung; đây là đường riêng gác quyền Duyệt, không hỏi lý do.
Bài kiểm soi: chuỗi phía sau (công nợ, tồn kho) đổi theo giá mới; YCTT nháp tự cập nhật; dòng đã nằm trên
YCTT đã gửi duyệt / công nợ đã trả / dòng Hoàn thành bị chặn; SL đặt không nhỏ hơn SL đã nhận.
"""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.audit.model import AuditLog
from app.modules.inventory.model import InventoryMove
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.purchase_order import service
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.reprice_service import get_reprice_locks, reprice_po
from app.modules.purchase_order.schema import DeliveryIn, POItemIn, RepriceIn, RepriceLineIn

def _make_po(db, status="approved", received_qty=4.0):
    """Đơn 2 dòng: dòng 1 đã nhận một phần (sinh công nợ + tồn kho), dòng 2 chưa nhận."""
    po = PurchaseOrder(code="PO-SG01", status=status, company_id=1, supplier_code="NCC01",
                       supplier_name="NCC Một", department="Thu mua", order_date="2026-11-01", misa_code="MS01")
    db.add(po)
    db.flush()
    items = [
        POItemIn(product_code="SP01", product_name="Hàng một", item_group="Nhãn", unit="cái", qty_request=10,
                 qty_order=10, price=1000, vat=8, warehouse_code="KHO01",
                 deliveries=[DeliveryIn(delivery_no=1, ship_qty=received_qty, received_qty=received_qty,
                                        received_date="2026-11-05", invoice_no="HD01")]),
        POItemIn(product_code="SP02", product_name="Hàng hai", item_group="Nhãn", unit="cái", qty_request=5,
                 qty_order=5, price=2000, vat=10, warehouse_code="KHO01"),
    ]
    service._save_items(db, po, items, user_id=1)
    service.recompute_effects(db, po, 1)
    db.commit()
    rows = db.query(POItem).filter(POItem.po_id == po.id).order_by(POItem.id).all()
    return po, rows[0], rows[1]


def _line(it, **change):
    base = dict(id=it.id, qty_order=float(it.qty_order), price=float(it.price), vat=float(it.vat))
    base.update(change)
    return RepriceLineIn(**base)


def _goods_payable(db, po):
    return db.query(Payable).filter(Payable.po_id == po.id, Payable.source_type == "goods").one()


def _payment_request(db, po, status, amount):
    req = PaymentRequest(code=f"YCTT-{status}", status=status, supplier_code="NCC01", source_type="goods",
                         total=amount)
    db.add(req)
    db.flush()
    db.add(PaymentRequestLine(request_id=req.id, payable_id=_goods_payable(db, po).id, po_code=po.code,
                              invoice_no="HD01", amount=amount))
    db.commit()
    return req


def test_doi_gia_tinh_lai_cong_no_va_ton_kho(db):
    po, it1, _ = _make_po(db)
    assert float(_goods_payable(db, po).total) == pytest.approx(4 * 1000 * 1.08)

    reprice_po(db, po.id, RepriceIn(items=[_line(it1, price=1200)]), user_id=1)

    db.refresh(it1)
    assert float(it1.price) == 1200
    assert po.status == "partial"                        # giữ trạng thái theo tiến độ nhận, không tụt về Nháp
    assert float(_goods_payable(db, po).total) == pytest.approx(4 * 1200 * 1.08)
    move = db.query(InventoryMove).filter(InventoryMove.product_code == "SP01").one()
    assert float(move.unit_price) == pytest.approx(1200)


def test_nhat_ky_ghi_gia_cu_gia_moi(db):
    po, it1, it2 = _make_po(db)
    reprice_po(db, po.id, RepriceIn(items=[_line(it1, price=1200), _line(it2, vat=8)]), user_id=1)
    log = db.query(AuditLog).filter(AuditLog.entity_id == po.id, AuditLog.action == "reprice").one()
    assert "Lý do" not in log.message
    assert "Đơn giá 1.000 → 1.200" in log.message
    assert "VAT (%) 10% → 8%" in log.message
    assert "2 dòng" in log.message


def test_dong_khong_doi_bi_bo_qua_va_khong_doi_gi_thi_bao_loi(db):
    po, it1, _ = _make_po(db)
    with pytest.raises(HTTPException) as e:
        reprice_po(db, po.id, RepriceIn(items=[_line(it1)]), user_id=1)
    assert "Không có dòng nào thay đổi" in e.value.detail


def test_khong_hoi_ly_do_va_bo_qua_ly_do_cu_gui_kem(db):
    """Người chủ chốt 20/11/2026: sửa giá không cần lý do; giao diện cũ còn gửi `reason` thì bỏ qua, không lỗi."""
    po, it1, _ = _make_po(db)
    reprice_po(db, po.id, RepriceIn(items=[_line(it1, price=1100)]), user_id=1)
    reprice_po(db, po.id, RepriceIn.model_validate({"reason": "x" * 600, "items": [_line(it1, price=1150)]}),
               user_id=1)
    db.refresh(it1)
    assert float(it1.price) == 1150


@pytest.mark.parametrize("status", ["draft", "submitted", "rejected", "completed", "cancelled"])
def test_chi_ap_cho_don_da_duyet(db, status):
    po, it1, _ = _make_po(db, status=status)
    with pytest.raises(HTTPException) as e:
        reprice_po(db, po.id, RepriceIn(items=[_line(it1, price=1)]), user_id=1)
    assert "Chỉ sửa giá được đơn" in e.value.detail


def test_sl_dat_khong_nho_hon_sl_da_nhan(db):
    po, it1, _ = _make_po(db, received_qty=4)
    with pytest.raises(HTTPException) as e:
        reprice_po(db, po.id, RepriceIn(items=[_line(it1, qty_order=3)]), user_id=1)
    assert "SL đã nhận" in e.value.detail
    # bằng đúng SL đã nhận thì được
    reprice_po(db, po.id, RepriceIn(items=[_line(it1, qty_order=4)]), user_id=1)


def test_sl_dat_bang_0_bi_chan(db):
    po, _, it2 = _make_po(db)
    with pytest.raises(HTTPException) as e:
        reprice_po(db, po.id, RepriceIn(items=[_line(it2, qty_order=0)]), user_id=1)
    assert "lớn hơn 0" in e.value.detail


def test_dong_cua_don_khac_bi_chan(db):
    po, it1, _ = _make_po(db)
    with pytest.raises(HTTPException) as e:
        reprice_po(db, po.id, RepriceIn(items=[RepriceLineIn(id=999999, qty_order=1, price=1, vat=0)]),
                   user_id=1)
    assert "không thuộc đơn" in e.value.detail


def test_schema_chan_so_am_va_vat_vuot():
    with pytest.raises(ValidationError):
        RepriceLineIn(id=1, qty_order=1, price=-1, vat=0)
    with pytest.raises(ValidationError):
        RepriceLineIn(id=1, qty_order=1, price=1, vat=101)


def test_dong_hoan_thanh_bi_chan(db):
    po, it1, _ = _make_po(db)
    it1.progress_status = service.PROG_COMPLETED
    db.commit()
    assert "Hoàn thành" in get_reprice_locks(db, po)[it1.id]
    with pytest.raises(HTTPException) as e:
        reprice_po(db, po.id, RepriceIn(items=[_line(it1, price=1)]), user_id=1)
    assert "Hoàn thành" in e.value.detail


def test_cong_no_da_tra_tien_bi_chan(db):
    po, it1, it2 = _make_po(db)
    p = _goods_payable(db, po)
    p.paid_amount = 100
    db.commit()
    locks = get_reprice_locks(db, po)
    assert "đã có tiền trả" in locks[it1.id]
    assert it2.id not in locks                            # dòng chưa nhận hàng vẫn sửa được


@pytest.mark.parametrize("status", ["submitted", "approved", "paid"])
def test_dong_tren_yctt_da_gui_duyet_bi_chan(db, status):
    po, it1, _ = _make_po(db)
    _payment_request(db, po, status, 4320)
    reason = get_reprice_locks(db, po)[it1.id]
    assert f"YCTT-{status}" in reason
    with pytest.raises(HTTPException):
        reprice_po(db, po.id, RepriceIn(items=[_line(it1, price=1200)]), user_id=1)


def test_yctt_bi_tu_choi_khong_chan(db):
    po, it1, _ = _make_po(db)
    _payment_request(db, po, "cancelled", 4320)
    assert it1.id not in get_reprice_locks(db, po)


def test_yctt_nhap_tu_cap_nhat_theo_cong_no_moi(db):
    po, it1, _ = _make_po(db)
    req = _payment_request(db, po, "draft", 4320)
    _, changed, refreshed = reprice_po(db, po.id, RepriceIn(items=[_line(it1, price=1200)]),
                                       user_id=1)
    assert changed == 1
    assert refreshed == [req.code]
    ln = db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == req.id).one()
    assert float(ln.amount) == pytest.approx(4 * 1200 * 1.08)
    db.refresh(req)
    assert float(req.total) == pytest.approx(4 * 1200 * 1.08)


def test_khoa_sau_duyet_cua_duong_luu_chung_van_dung_nguyen(db):
    """Đường riêng không được làm hở khóa CR-108: Lưu chung vẫn chặn đổi đơn giá."""
    from app.modules.purchase_order.schema import POUpdate
    po, it1, _ = _make_po(db)
    with pytest.raises(HTTPException):
        service.block_edit_approved_order(db, po, POUpdate(items=[POItemIn(
            id=it1.id, product_code=it1.product_code, product_name=it1.product_name, unit=it1.unit,
            item_group=it1.item_group, qty_order=10, price=5, vat=8, warehouse_code="KHO01")]))


def test_so_trong_nhat_ky_theo_kieu_viet():
    from app.modules.purchase_order.reprice_service import _format_value
    assert _format_value("price", 69444.44) == "69.444,44"
    assert _format_value("price", 15300) == "15.300"
    assert _format_value("qty_order", 0.5) == "0,5"
    assert _format_value("vat", 8) == "8%"
