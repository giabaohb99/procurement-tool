"""CR-068 — xuất Excel màn Tiến độ mua hàng.

Màn này vốn đã phẳng (một hàng = một LẦN GIAO của một dòng hàng) nên không phải bung thêm:
lấy đúng dòng của bảng, đúng bộ lọc, đúng thứ tự cột đang hiện.

Cột NCC + khối vận chuyển bị bỏ khỏi file với người không có `supplier.read` — cùng luật
`_SUPPLIER_HIDDEN` của API danh sách (dữ liệu cũng đã bị gỡ khỏi row trước khi tới đây).
"""
from app.core.export_xlsx import Col
from app.core.status_codes import (PO_DELIVERY_STATUS, PO_DOCUMENT_STATUS,
                                   PO_ITEM_LINE_STATUS, PO_PROGRESS_STATUS)
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder

# Bốn cột của B-06 lưu MÃ tiếng Anh. File Excel là để NGƯỜI đọc nên phải dịch ngược ngay trước
# khi ghi. `row_values` cố ý KHÔNG dịch sẵn: cùng hàm đó nuôi luôn API danh sách, mà giao diện
# cần MÃ để tô màu badge và để gửi lại làm tham số lọc.
_BO_MA_THEO_COT = {
    "progress_status": PO_PROGRESS_STATUS,
    "line_status": PO_ITEM_LINE_STATUS,
    "delivery_status": PO_DELIVERY_STATUS,
    "document_status": PO_DOCUMENT_STATUS,
}


def dich_ma(r: dict) -> dict:
    """Đổi MÃ trạng thái trong một hàng sang nhãn tiếng Việt — CHỈ dùng cho file xuất.

    Sửa tại chỗ và trả về chính `r`. Mã lạ giữ nguyên chứ không nuốt thành ô trống.
    """
    for k, bo in _BO_MA_THEO_COT.items():
        if k in r:
            r[k] = bo.label_of(r[k]) or (r[k] or "")
    return r

# Key bị GỠ KHỎI DỮ LIỆU với người không có `supplier.read` (rộng hơn `SUPPLIER_ONLY`
# bên dưới vì có cả key không lên bảng, vd `ship_unit`).
SUPPLIER_HIDDEN_KEYS = ("supplier_code", "supplier_name", "carrier_code", "carrier_name",
                        "shipping_unit_price", "shipping_amount", "ship_unit")

# Bộ cột đầy đủ — key và nhãn khớp bảng trên màn hình (frontend/src/pages/PurchaseProgress.tsx)
COLS = [
    Col("stt", "STT", "int", 7),
    Col("po_code", "Mã ĐMH", width=18),
    Col("misa_code", "Mã MISA", width=14),
    Col("pr_code", "Mã PYC", width=16),
    Col("company", "Công ty", width=26),
    Col("department", "Bộ phận", width=18),
    Col("supplier_code", "Mã NCC", width=14),
    Col("supplier_name", "Nhà cung cấp", width=28),
    Col("nspt", "NSPT", width=20),
    Col("order_date", "Ngày ĐH", "date", 12),
    Col("product_code", "Mã SP", width=16),
    Col("product_name", "Tên SP", width=30),
    Col("invoice_name", "Tên hóa đơn", width=26),
    Col("item_group", "Nhóm hàng", width=16),
    Col("spec", "Quy cách", width=26),
    Col("fg_code", "Mã HH", width=12),
    Col("invoice_no", "Số HĐ", width=16),
    Col("required_date", "Ngày cần", "date", 12),
    Col("expected_date", "Dự kiến nhận", "date", 13),
    Col("unit", "ĐVT", width=8),
    Col("qty_request", "SL YC", "qty", 10),
    Col("qty_order", "SL đặt", "qty", 10),
    Col("price", "Đơn giá", "price", 14),
    Col("vat", "VAT%", "int", 8),
    Col("order_amount", "Thành tiền ĐH", "money", 16),
    Col("progress_status", "Tiến độ", width=18),
    Col("delivery_no", "Lần giao", "int", 9),
    Col("warehouse_code", "Kho", width=12),
    Col("carrier_code", "Mã ĐVVC", width=14),
    Col("carrier_name", "Đơn vị VC", width=22),
    Col("ship_qty", "SL giao", "qty", 10),
    Col("received_qty", "SL nhận", "qty", 10),
    Col("promised_date", "Cam kết giao", "date", 13),
    Col("received_date", "Ngày nhận", "date", 12),
    Col("std_days", "Ngày QĐ", "int", 9),
    Col("regulated_date", "Ngày quy định", "date", 13),
    Col("diff_promise", "CL cam kết", "int", 11),
    Col("diff_regulated", "CL quy định", "int", 11),
    Col("diff_required", "CL vs YC", "int", 10),
    Col("delivery_invoice_no", "Số HĐ (giao)", width=16),
    Col("shipping_unit_price", "Đơn giá VC", "price", 13),
    Col("shipping_amount", "Tiền VC", "money", 14),
    Col("qc_result", "QC", width=10),
    Col("delivery_status", "TT giao", width=14),
    Col("amount", "Thành tiền nhận", "money", 16),
    Col("document_status", "Hồ sơ CT", width=18),
]

# Cột chỉ dành cho người có `supplier.read` (trùng _SUPPLIER_HIDDEN của controller)
SUPPLIER_ONLY = {"supplier_code", "supplier_name", "carrier_code", "carrier_name",
                 "shipping_unit_price", "shipping_amount"}

# ----- Riêng của màn Tiến độ (KHÔNG đụng `COLS`, vì file xuất màn ĐMH bê nguyên bộ đó) -----
# Số HĐ có hai chỗ: `invoice_no` ghi ở DÒNG ĐMH và `delivery_invoice_no` ghi ở LẦN GIAO.
# Thực tế người dùng chỉ nhập ở lần giao, cột kia luôn trống mà vẫn chiếm chỗ, nên bảng Tiến độ
# bỏ hẳn cột dòng và để cột lần giao mang đúng nhãn "Số HĐ".
PROGRESS_SKIP = {"invoice_no"}
PROGRESS_RENAME = {"delivery_invoice_no": Col("delivery_invoice_no", "Số HĐ", width=16)}

SHEET_TITLE = "Tien do mua hang"
FILE_NAME = "tien-do-mua-hang"


def columns_for(show_supplier: bool) -> list[Col]:
    cols = [PROGRESS_RENAME.get(c.key, c) for c in COLS if c.key not in PROGRESS_SKIP]
    return cols if show_supplier else [c for c in cols if c.key not in SUPPLIER_ONLY]


def row_values(po: PurchaseOrder, it: POItem, dl: PODelivery | None, show_supplier: bool) -> dict:
    """Một hàng của màn Tiến độ: đơn + dòng hàng + LẦN GIAO (thiếu lần giao thì để trống).

    Dùng chung cho API danh sách (`controller._row`), file xuất của màn Tiến độ và **file xuất của
    màn Đơn mua hàng** (CR-068 bổ sung) — chỉ một chỗ tính `Thành tiền ĐH` / `Thành tiền nhận` /
    các cột chênh lệch, để ba nơi không bao giờ lệch số.
    """
    qty_recv = float(dl.received_qty or 0) if dl else 0.0
    qty_order = float(it.qty_order or 0)
    price = float(it.price or 0)
    vat = float(it.vat or 0)
    # Thành tiền ĐƠN HÀNG (col AB): SL đặt × đơn giá × (1+VAT%) — ổn định, không phụ thuộc đã nhận hay chưa
    order_amount = round(qty_order * price * (1 + vat / 100), 2)
    # Thành tiền theo SL thực NHẬN của lần giao (gồm VAT) — dùng đối chiếu công nợ đã chốt
    amount = round(qty_recv * price * (1 + vat / 100), 2)
    r = {
        # ----- Đơn mua hàng -----
        "po_id": po.id, "po_code": po.code, "misa_code": po.misa_code,
        "pr_code": po.pr_code, "company_id": po.company_id, "department": po.department,
        "supplier_code": po.supplier_code, "supplier_name": po.supplier_name,
        "nspt": po.nspt, "order_date": po.order_date, "po_status": po.status,
        "document_status": po.document_status, "payment_terms": po.payment_terms,
        "is_urgent": bool(po.is_urgent),
        # ----- Dòng hàng -----
        "item_id": it.id, "product_code": it.product_code, "product_name": it.product_name,
        "invoice_name": it.invoice_name, "item_group": it.item_group, "spec": it.spec,
        "fg_code": it.fg_code, "fg_name": it.fg_name, "invoice_no": it.invoice_no,
        "required_date": it.required_date, "expected_date": it.expected_date or "",
        "supplier_ready": bool(it.supplier_ready),
        "unit": it.unit, "qty_request": float(it.qty_request or 0),
        "qty_order": qty_order, "price": price, "vat": vat, "order_amount": order_amount,
        "line_status": it.line_status,
        "progress_status": it.progress_status or PO_PROGRESS_STATUS.ordered_values[0],
        "document_delivery_date": it.document_delivery_date or "",
        # ----- Lần giao -----
        "delivery_id": dl.id if dl else None,
        "delivery_no": dl.delivery_no if dl else None,
        "warehouse_code": dl.warehouse_code if dl else "",
        "carrier_code": dl.carrier_code if dl else "",
        "carrier_name": dl.carrier_name if dl else "",
        "ship_qty": float(dl.ship_qty or 0) if dl else 0.0,
        "ship_unit": dl.ship_unit if dl else "",
        "received_qty": qty_recv,
        "promised_date": dl.promised_date if dl else "",
        "received_date": dl.received_date if dl else "",
        "std_days": dl.std_days if dl else 0,
        "regulated_date": dl.regulated_date if dl else "",
        "diff_promise": dl.diff_promise if dl else 0,
        "diff_regulated": dl.diff_regulated if dl else 0,
        "diff_required": dl.diff_required if dl else 0,
        "delivery_invoice_no": dl.invoice_no if dl else "",
        "shipping_unit_price": float(dl.shipping_unit_price or 0) if dl else 0.0,
        "shipping_amount": float(dl.shipping_amount or 0) if dl else 0.0,
        "qc_result": dl.qc_result if dl else "",
        "delivery_status": dl.status if dl else "",
        "progress_note": dl.progress_note if dl else "",
        "amount": amount,
    }
    if not show_supplier:
        for k in SUPPLIER_HIDDEN_KEYS:
            r.pop(k, None)
    return r
