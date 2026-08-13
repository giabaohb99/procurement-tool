"""Cam kết giao (`promised_date`) mặc định lấy theo NGÀY QĐ CÓ HÀNG của phân loại (CR-065).

Ngày QĐ = Ngày đặt hàng + số ngày QĐ; số ngày QĐ luôn lấy mốc DÀI NHẤT (không sẵn hàng),
thiếu thì mốc có sẵn, thiếu cả hai thì 15 ngày.

Đây là GIÁ TRỊ KHỞI TẠO, không phải ràng buộc đồng bộ: NSTM sửa lại theo cam kết thật
của NCC được, và lần giao đã tồn tại thì không bị điền đè ở các lần lưu sau.
"""
from app.modules.catalog.model import ItemGroup
from app.modules.purchase_order.model import PODelivery, PurchaseOrder
from app.modules.purchase_order.schema import DeliveryIn, POItemIn
from app.modules.purchase_order.service import _save_items


def _groups(db):
    db.add_all([ItemGroup(code="PL1", name="NL", std_days="10", std_days_unavail="14"),
                ItemGroup(code="PL2", name="Chỉ có sẵn", std_days="6", std_days_unavail=""),
                ItemGroup(code="PL3", name="Vận chuyển", std_days="", std_days_unavail="")])
    db.commit()


def _po(db, order_date="2026-08-01"):
    _groups(db)
    po = PurchaseOrder(code="PO1", status="draft", order_date=order_date)
    db.add(po)
    db.commit()
    return po


def _luu(db, po, deliveries, item_group="NL", item_id=None):
    _save_items(db, po, [POItemIn(id=item_id, product_code="SP1", product_name="Hàng A",
                                  qty_order=10, required_date="2026-08-08",
                                  item_group=item_group, deliveries=deliveries)], user_id=1)
    db.commit()
    return db.query(PODelivery).filter(PODelivery.po_id == po.id).order_by(PODelivery.id).all()


def test_lan_giao_moi_lay_ngay_qd_theo_phan_loai(db):
    """Mốc "không sẵn hàng" (14) chứ không phải "có sẵn" (10): 01/08 + 14 = 15/08."""
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10)])
    assert len(dels) == 1 and dels[0].promised_date == "2026-08-15"


def test_thieu_moc_khong_san_thi_lay_moc_co_san(db):
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10)], item_group="Chỉ có sẵn")
    assert dels[0].promised_date == "2026-08-07"      # 01/08 + 6


def test_phan_loai_chua_khai_bao_thi_15_ngay(db):
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10)], item_group="Vận chuyển")
    assert dels[0].promised_date == "2026-08-16"      # 01/08 + 15


def test_nhap_tay_thi_giu_nguyen(db):
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10, promised_date="2026-09-30")])
    assert dels[0].promised_date == "2026-09-30"


def test_don_khong_co_ngay_dat_hang_thi_de_trong(db):
    po = _po(db, order_date="")
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10)])
    assert dels[0].promised_date == ""


def test_lan_giao_da_co_thi_khong_dien_de(db):
    """Xóa trắng cam kết giao trên lần giao cũ thì phải giữ trắng, không tự điền lại."""
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10)])
    item_id = dels[0].po_item_id
    dels = _luu(db, po, [DeliveryIn(id=dels[0].id, delivery_no=1, ship_qty=10, promised_date="")],
                item_id=item_id)
    assert dels[0].promised_date == ""
