"""bao-CR-619 — cảnh báo đặt vượt khi tạo thêm ĐMH từ YCMH.

`order_progress` trả thêm `pending` (đơn nháp / chờ duyệt / bị trả lại) và `orders` (từng đơn theo mã
hàng). `ordered` phải giữ NGUYÊN nghĩa cũ: chỉ đơn đã duyệt trở đi, bỏ dòng «Chưa đặt hàng» / «Hủy đơn».
"""
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_request import service

PR = "PYC-T619"


def add_order(db, code, status, lines, pr_code=PR):
    po = PurchaseOrder(code=code, pr_code=pr_code, status=status)
    db.add(po)
    db.flush()
    for product_code, qty, received, progress in lines:
        db.add(POItem(po_id=po.id, product_code=product_code, product_name=product_code,
                      qty_order=qty, qty_received=received, progress_status=progress))
    db.commit()
    return po


def test_ordered_giu_nghia_cu_pending_tach_rieng(db):
    add_order(db, "PO-A", "approved", [("KCL", 50, 10, po_service.PROG_ORDERED),
                                       ("UREA", 7, 0, po_service.PROG_NOT_ORDERED)])
    add_order(db, "PO-B", "received", [("KCL", 30, 30, po_service.PROG_RECEIVED)])
    add_order(db, "PO-C", "draft", [("KCL", 100, 0, po_service.PROG_NOT_ORDERED)])
    add_order(db, "PO-D", "submitted", [("KCL", 5, 0, po_service.PROG_NOT_ORDERED)])
    add_order(db, "PO-E", "rejected", [("KCL", 2, 0, po_service.PROG_NOT_ORDERED)])
    add_order(db, "PO-F", "cancelled", [("KCL", 999, 0, po_service.PROG_ORDERED)])
    add_order(db, "PO-G", "approved", [("KCL", 888, 0, po_service.PROG_CANCELLED)])
    add_order(db, "PO-H", "approved", [("KCL", 777, 0, po_service.PROG_ORDERED)], pr_code="PYC-KHAC")

    out = service.order_progress(db, PR)

    assert out["ordered"] == {"KCL": 80.0}                  # 50 + 30; dòng «Chưa đặt hàng» UREA không tính
    assert out["pending"] == {"KCL": 107.0}                 # nháp 100 + chờ duyệt 5 + bị trả lại 2
    codes = [(o["code"], o["status"], o["pending"], o["qty"], o["received"]) for o in out["orders"]["KCL"]]
    assert codes == [("PO-A", "approved", False, 50.0, 10.0), ("PO-B", "received", False, 30.0, 30.0),
                     ("PO-C", "draft", True, 100.0, 0.0), ("PO-D", "submitted", True, 5.0, 0.0),
                     ("PO-E", "rejected", True, 2.0, 0.0)]
    assert out["orders"]["KCL"][2]["status_label"] == "Nháp"


def test_cung_ma_hai_dong_tren_mot_don_gop_mot_muc(db):
    add_order(db, "PO-X", "approved", [("KCL", 20, 5, po_service.PROG_ORDERED),
                                       ("KCL", 30, 0, po_service.PROG_ORDERED)])
    out = service.order_progress(db, PR)
    assert out["ordered"] == {"KCL": 50.0}
    assert [(o["code"], o["qty"], o["received"]) for o in out["orders"]["KCL"]] == [("PO-X", 50.0, 5.0)]


def test_khong_co_don_hoac_ma_rong(db):
    assert service.order_progress(db, PR) == {"ordered": {}, "pending": {}, "orders": {}}
    assert service.order_progress(db, "") == {"ordered": {}, "pending": {}, "orders": {}}
