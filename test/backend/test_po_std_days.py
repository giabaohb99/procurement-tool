"""Số ngày QĐ (`PODelivery.std_days`) — CR-065.

Hai luật: (1) mặc định LUÔN lấy mốc dài nhất của phân loại (không sẵn hàng), KHÔNG còn phụ thuộc
checkbox "NCC có sẵn hàng"; (2) số đã có trên dòng giao là do người dùng đặt -> giữ nguyên,
mỗi lần lưu đơn không được tính đè.
"""
from app.modules.catalog.model import ItemGroup
from app.modules.purchase_order.model import PODelivery, PurchaseOrder
from app.modules.purchase_order.schema import DeliveryIn, POItemIn
from app.modules.purchase_order.service import _save_items, recompute_effects


def _po(db):
    db.add_all([ItemGroup(code="PL1", name="NL", std_days="10", std_days_unavail="14"),
                ItemGroup(code="PL3", name="Vận chuyển", std_days="", std_days_unavail="")])
    po = PurchaseOrder(code="PO1", status="draft", order_date="2026-08-01")
    db.add(po)
    db.commit()
    return po


def _luu(db, po, deliveries, item_group="NL", supplier_ready=False, item_id=None):
    _save_items(db, po, [POItemIn(id=item_id, product_code="SP1", product_name="Hàng A",
                                  qty_order=10, required_date="2026-08-08", item_group=item_group,
                                  supplier_ready=supplier_ready, deliveries=deliveries)], user_id=1)
    recompute_effects(db, po, user_id=1)
    db.commit()
    return db.query(PODelivery).filter(PODelivery.po_id == po.id).order_by(PODelivery.id).all()


def test_lay_moc_dai_nhat_du_ncc_co_san_hang(db):
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10)], supplier_ready=True)
    assert dels[0].std_days == 14                     # không phải 10 (mốc có sẵn)
    assert dels[0].regulated_date == "2026-08-15"     # 01/08 + 14


def test_phan_loai_chua_khai_bao_thi_15_ngay(db):
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10)], item_group="Vận chuyển")
    assert dels[0].std_days == 15 and dels[0].regulated_date == "2026-08-16"


def test_so_ngay_sua_tay_thi_giu_va_ngay_qd_tinh_theo(db):
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10, std_days=3)])
    assert dels[0].std_days == 3 and dels[0].regulated_date == "2026-08-04"


def test_luu_lai_don_khong_tinh_de_so_da_sua(db):
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10, std_days=3)])
    item_id, did = dels[0].po_item_id, dels[0].id
    dels = _luu(db, po, [DeliveryIn(id=did, delivery_no=1, ship_qty=20, std_days=3)],
                item_id=item_id)
    assert dels[0].std_days == 3
