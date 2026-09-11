"""bao-CR-367 — Ngày hóa đơn trên Đơn mua hàng KHÔNG được hệ thống đoán hộ.

Lỗi thật trên hệ đang chạy (ticket TK10092603, 10/09/2026): thu mua sửa Ngày hóa đơn
đúng 9/9 cho 4 dòng giao hàng của PO00103, bấm Lưu, ngày nhảy thành 10/9. Nguyên nhân
là HAI chỗ cộng lại:

1. Giao diện (`frontend/src/pages/PurchaseOrderDetail.tsx`) khi dựng dữ liệu gửi lên
   cho bảng Giao hàng nhiều đợt đã QUÊN trường `invoice_date` — ngày người dùng gõ
   không bao giờ rời khỏi trình duyệt.
2. Backend nhận ô rỗng, tưởng người dùng bỏ trống, rồi dập `date.today()` đè lên.

Hậu quả: mỗi lần lưu một ĐMH là mọi dòng giao hàng có số hóa đơn mất ngày thật —
90/96 dòng trên hệ thật mang đúng ngày lưu cuối cùng. Ngày sai còn chảy tiếp sang
Yêu cầu thanh toán qua `delivery_invoice_date`.

Bộ kiểm này canh vế backend (vế giao diện đã sửa cùng CR). Trống thì để TRỐNG:
người dùng còn nhìn ra mà điền, chứ điền bừa ngày hôm nay thì không ai biết là ngày bịa.
"""
from datetime import date

from app.modules.purchase_order import service
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_order.schema import DeliveryIn, POItemIn

TODAY = date.today().isoformat()


def _make_po(db, seed, code="PO-CR367"):
    po = PurchaseOrder(code=code, company_id=seed.company_id, supplier_code="NCC01",
                       supplier_name=seed.sup_name, order_date="2026-09-08", status="draft")
    db.add(po)
    db.flush()
    return po


def _item_in(deliveries, invoice_no="", invoice_date="", item_id=None):
    return POItemIn(id=item_id, product_code="SP01", product_name="Hàng thử",
                    item_group="Nhãn", unit="cái", qty_request=1, qty_order=4, price=100,
                    vat=0, required_date="2026-09-20", warehouse_code="KHO01",
                    invoice_no=invoice_no, invoice_date=invoice_date, deliveries=deliveries)


def _deliv_in(invoice_no="", invoice_date="", deliv_id=None):
    return DeliveryIn(id=deliv_id, delivery_no=1, warehouse_code="KHO01", ship_qty=4,
                      received_qty=4, received_date="2026-09-08",
                      invoice_no=invoice_no, invoice_date=invoice_date)


def _save(db, po, item):
    service._save_items(db, po, [item], user_id=1)
    db.flush()
    it = service.items_of(db, po.id)[0]
    return it, service.deliveries_of(db, it.id)


def test_delivery_khong_tu_dien_ngay_hom_nay_khi_chi_co_so_hoa_don(db, seed):
    """Có Số hóa đơn mà trống Ngày hóa đơn thì để TRỐNG, không lấy ngày hôm nay."""
    po = _make_po(db, seed)
    _, delivs = _save(db, po, _item_in([_deliv_in(invoice_no="5017")]))
    assert delivs[0].invoice_no == "5017"
    assert delivs[0].invoice_date == ""


def test_dong_hang_khong_tu_dien_ngay_hom_nay_khi_chi_co_so_hoa_don(db, seed):
    """Cùng luật ở cấp DÒNG HÀNG — `_save_items` trước đây cũng dập ngày hôm nay."""
    po = _make_po(db, seed, code="PO-CR367-B")
    it, _ = _save(db, po, _item_in([], invoice_no="5017"))
    assert it.invoice_no == "5017"
    assert it.invoice_date == ""


def test_giu_nguyen_ngay_hoa_don_nguoi_dung_nhap(db, seed):
    """Ngày người dùng gõ phải sống sót qua lần lưu — đây là ca hỏng trong ticket."""
    po = _make_po(db, seed, code="PO-CR367-C")
    _, delivs = _save(db, po, _item_in([_deliv_in(invoice_no="5017", invoice_date="2026-09-09")]))
    assert delivs[0].invoice_date == "2026-09-09"


def test_luu_lai_lan_nua_khong_dap_ngay_cu(db, seed):
    """Lưu đơn lần thứ hai không được đổi ngày — đây chính là nhịp làm hỏng dữ liệu thật."""
    po = _make_po(db, seed, code="PO-CR367-D")
    it, delivs = _save(db, po, _item_in([_deliv_in(invoice_no="5017", invoice_date="2026-09-09")]))
    _, delivs = _save(db, po, _item_in([_deliv_in(invoice_no="5017", invoice_date="2026-09-09",
                                                  deliv_id=delivs[0].id)], item_id=it.id))
    assert delivs[0].invoice_date != TODAY
    assert delivs[0].invoice_date == "2026-09-09"


def test_xoa_trang_ngay_hoa_don_thi_ra_trong_chu_khong_ra_hom_nay(db, seed):
    """Người dùng CỐ Ý xóa trắng ô ngày thì ô đó trống.

    Đây là ranh giới của bản vá: ô rỗng vẫn ghi đè như mọi trường khác của bảng, chỉ
    khác là không còn bị thay bằng ngày hôm nay. Sau bản vá, giao diện luôn gửi kèm
    `invoice_date` nên rỗng ở đây nghĩa là người dùng thật sự muốn xóa.
    """
    po = _make_po(db, seed, code="PO-CR367-E")
    it, delivs = _save(db, po, _item_in([_deliv_in(invoice_no="5017", invoice_date="2026-09-09")]))
    _, delivs = _save(db, po, _item_in([_deliv_in(invoice_no="5017", deliv_id=delivs[0].id)],
                                       item_id=it.id))
    assert delivs[0].invoice_date == ""
