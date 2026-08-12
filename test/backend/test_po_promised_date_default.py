"""Cam kết giao (`promised_date`) mặc định lấy theo Ngày yêu cầu có hàng của dòng ĐMH.

Đây là GIÁ TRỊ KHỞI TẠO, không phải ràng buộc đồng bộ: NSTM sửa lại theo cam kết thật
của NCC được, và lần giao đã tồn tại thì không bị điền đè ở các lần lưu sau.
"""
from app.modules.purchase_order.model import PODelivery, PurchaseOrder
from app.modules.purchase_order.schema import DeliveryIn, POItemIn
from app.modules.purchase_order.service import _save_items


def _po(db):
    po = PurchaseOrder(code="PO1", status="draft")
    db.add(po)
    db.commit()
    return po


def _luu(db, po, deliveries, required_date="2026-08-08", item_id=None):
    _save_items(db, po, [POItemIn(id=item_id, product_code="SP1", product_name="Hàng A",
                                  qty_order=10, required_date=required_date,
                                  deliveries=deliveries)], user_id=1)
    db.commit()
    return db.query(PODelivery).filter(PODelivery.po_id == po.id).order_by(PODelivery.id).all()


def test_lan_giao_moi_lay_ngay_yeu_cau_co_hang(db):
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10)])
    assert len(dels) == 1 and dels[0].promised_date == "2026-08-08"


def test_nhap_tay_thi_giu_nguyen(db):
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10, promised_date="2026-09-30")])
    assert dels[0].promised_date == "2026-09-30"


def test_dong_khong_co_ngay_yeu_cau_thi_de_trong(db):
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10)], required_date="")
    assert dels[0].promised_date == ""


def test_lan_giao_da_co_thi_khong_dien_de(db):
    """Xóa trắng cam kết giao trên lần giao cũ thì phải giữ trắng, không tự điền lại."""
    po = _po(db)
    dels = _luu(db, po, [DeliveryIn(delivery_no=1, ship_qty=10)])
    item_id = dels[0].po_item_id
    dels = _luu(db, po, [DeliveryIn(id=dels[0].id, delivery_no=1, ship_qty=10, promised_date="")],
                item_id=item_id)
    assert dels[0].promised_date == ""
