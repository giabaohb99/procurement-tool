"""Task 7 — Trang "Tiến độ mua hàng".

Nguồn: join tab_purchase_order -> tab_po_item -> tab_po_delivery, hiển thị theo LẦN GIAO.
Quyền: cho phép nếu có `purchase_order.read` HOẶC `purchase_request.read`
(phòng yêu cầu thường chỉ có cái sau). Che cột NCC + khối vận chuyển với người
không có `purchase_order.read`.

Bản 1: CHỈ dùng cột đã có trong DB. Các cột theo Mapping còn thiếu master
(product.legal_name...) để bản 2 bổ sung migration — xem
`doc/yeu-cau/Mapping_Sheet06_TienDoMuaHang.md`.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_perm_profile, user_has_permission
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder

router = APIRouter(prefix="/api/purchase-progress", tags=["purchase_progress"])

# Cột nhạy cảm — ẩn với người chỉ có purchase_request.read (phòng yêu cầu)
_SUPPLIER_HIDDEN = ("supplier_code", "supplier_name", "carrier_code", "carrier_name",
                    "shipping_unit_price", "shipping_amount", "ship_unit")


def _require_progress(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Gate OR: purchase_order.read HOẶC purchase_request.read."""
    if (user_has_permission(db, user, "purchase_order", "read")
            or user_has_permission(db, user, "purchase_request", "read")):
        return user
    raise HTTPException(403, "Không có quyền xem tiến độ mua hàng")


def _row(po: PurchaseOrder, it: POItem, dl: PODelivery, show_supplier: bool) -> dict:
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
        "required_date": it.required_date, "supplier_ready": bool(it.supplier_ready),
        "unit": it.unit, "qty_request": float(it.qty_request or 0),
        "qty_order": qty_order, "price": price, "vat": vat, "order_amount": order_amount,
        "line_status": it.line_status, "progress_status": it.progress_status or "Chưa đặt hàng",
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
        "expected_date": dl.expected_date if dl else "",
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
        for k in _SUPPLIER_HIDDEN:
            r.pop(k, None)
    return r


@router.get("")
def list_progress(request: Request, pg: dict = Depends(pagination),
                  db: Session = Depends(get_db), user=Depends(_require_progress)):
    prof = get_perm_profile(db, user)
    # Chỉ phòng thu mua (có purchase_order.read) mới thấy NCC + chi phí vận chuyển
    show_supplier = user_has_permission(db, user, "purchase_order", "read")

    q = (db.query(PurchaseOrder, POItem, PODelivery)
         .join(POItem, POItem.po_id == PurchaseOrder.id)
         .outerjoin(PODelivery, PODelivery.po_item_id == POItem.id))

    # ----- Filter -----
    company_id = (request.query_params.get("company_id") or "").strip()
    if company_id.isdigit():
        q = q.filter(PurchaseOrder.company_id == int(company_id))
    department = (request.query_params.get("department") or "").strip()
    if department:
        q = q.filter(PurchaseOrder.department == department)
    month = (request.query_params.get("month") or "").strip()   # YYYY-MM theo ngày đặt hàng
    if month:
        q = q.filter(PurchaseOrder.order_date.like(f"{month}%"))
    status = (request.query_params.get("status") or "").strip()  # theo tiến độ dòng
    if status:
        q = q.filter(POItem.progress_status == status)
    # Khoảng NGÀY ĐẶT HÀNG (chuỗi YYYY-MM-DD so sánh vẫn đúng thứ tự)
    od_from = (request.query_params.get("order_date_from") or "").strip()
    od_to = (request.query_params.get("order_date_to") or "").strip()
    if od_from:
        q = q.filter(PurchaseOrder.order_date != "", PurchaseOrder.order_date >= od_from)
    if od_to:
        q = q.filter(PurchaseOrder.order_date != "", PurchaseOrder.order_date <= od_to)
    # Khoảng NGÀY NHẬN thực tế của lần giao
    rd_from = (request.query_params.get("received_date_from") or "").strip()
    rd_to = (request.query_params.get("received_date_to") or "").strip()
    if rd_from:
        q = q.filter(PODelivery.received_date != "", PODelivery.received_date >= rd_from)
    if rd_to:
        q = q.filter(PODelivery.received_date != "", PODelivery.received_date <= rd_to)
    kw = (request.query_params.get("q") or "").strip()
    if kw:
        like = f"%{kw}%"
        q = q.filter((PurchaseOrder.code.like(like)) | (PurchaseOrder.pr_code.like(like))
                     | (POItem.product_code.like(like)) | (POItem.product_name.like(like)))

    # ----- Phạm vi dữ liệu -----
    if show_supplier:
        q = apply_scope(q, PurchaseOrder, "purchase_order", user, prof)
    else:
        # Phòng yêu cầu (chỉ purchase_request.read) → chỉ thấy ĐMH LIÊN KẾT với PYC
        # trong phạm vi của mình (đơn phát sinh từ yêu cầu mua hàng của mình/phòng mình).
        from app.modules.purchase_request.model import PurchaseRequest
        pr_q = apply_scope(db.query(PurchaseRequest.code), PurchaseRequest,
                           "purchase_request", user, prof)
        codes = [c for (c,) in pr_q.all() if c]
        q = q.filter(PurchaseOrder.pr_code.in_(codes)) if codes else q.filter(PurchaseOrder.id == -1)

    q = q.order_by(PurchaseOrder.code, POItem.id, PODelivery.delivery_no)
    total = q.count()
    rows = q.offset(pg["offset"]).limit(pg["limit"]).all()
    # STT liên tục theo trang
    base = pg["offset"]
    out = [{"stt": base + i + 1, **_row(po, it, dl, show_supplier)}
           for i, (po, it, dl) in enumerate(rows)]
    return success({"total": total, "items": out, "show_supplier": show_supplier})
