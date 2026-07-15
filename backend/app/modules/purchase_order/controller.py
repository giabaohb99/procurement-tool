from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, apply_range_filters, apply_equals, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.company.model import Company
from app.modules.supplier.model import Supplier
from app.modules.catalog.model import Warehouse
from app.modules.notification.service import trigger_notification

from . import service
from .model import POItem, PurchaseOrder
from app.modules.payable.model import Payable
from .schema import POCreate, POUpdate, RejectIn, ItemProgressIn

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase_order"])

HEADER = ["id", "code", "misa_code", "pr_code", "survey_code", "company_id", "supplier_code",
          "supplier_name", "department", "nspt", "order_date", "vat_rate", "payment_terms",
          "is_urgent", "status", "note", "approve_note"]


def _delivery(d, pay=None) -> dict:
    return {"id": d.id, "delivery_no": d.delivery_no, "warehouse_code": d.warehouse_code,
            "carrier_code": d.carrier_code, "carrier_name": d.carrier_name,
            "ship_qty": float(d.ship_qty or 0), "ship_unit": d.ship_unit,
            "received_qty": float(d.received_qty or 0), "promised_date": d.promised_date,
            "expected_date": d.expected_date, "received_date": d.received_date,
            "std_days": d.std_days, "regulated_date": d.regulated_date,
            "diff_promise": d.diff_promise, "diff_regulated": d.diff_regulated, "diff_required": d.diff_required,
            "invoice_no": d.invoice_no, "shipping_unit_price": float(d.shipping_unit_price or 0),
            "shipping_amount": float(d.shipping_amount or 0), "qc_result": d.qc_result,
            "status": d.status, "extra_request": d.extra_request, "progress_note": d.progress_note,
            # Công nợ HÀNG của lần giao này (đã trả / còn lại)
            "goods_total": float(pay.total or 0) if pay else 0.0,
            "paid": float(pay.paid_amount or 0) if pay else 0.0,
            "remaining": float(pay.remaining or 0) if pay else 0.0}


def _item(db, it, pay_by_del: dict) -> dict:
    dels = service.deliveries_of(db, it.id)
    qty_order = float(it.qty_order or 0)
    del_out = [_delivery(d, pay_by_del.get(d.id)) for d in dels]
    return {"id": it.id, "product_code": it.product_code, "product_name": it.product_name,
            "invoice_name": it.invoice_name, "item_group": it.item_group, "spec": it.spec,
            "fg_code": it.fg_code, "fg_name": it.fg_name, "invoice_no": it.invoice_no,
            "supplier_ready": bool(it.supplier_ready), "required_date": it.required_date,
            "unit": it.unit, "qty_request": float(it.qty_request or 0), "qty_order": qty_order,
            "price": float(it.price or 0), "vat": float(it.vat or 0), "amount": float(it.amount or 0),
            "qty_received": float(it.qty_received or 0), "qty_remaining": float(it.qty_remaining or 0),
            "line_status": it.line_status, "warehouse_code": it.warehouse_code, "note": it.note,
            "progress_status": it.progress_status or "Chưa đặt hàng",
            "pause_reason": it.pause_reason or "", "status_before_pause": it.status_before_pause or "",
            # Giao thiếu: tổng SL đã nhận < SL đặt (dùng cho badge cảnh báo ở FE)
            "is_short_delivery": bool(qty_order > 0 and float(it.qty_received or 0) + 0.001 < qty_order),
            # Tiền theo DÒNG: đặt hàng (SL đặt) · tiền hàng đã nhận (có công nợ) · đã trả · còn lại
            "order_total": round(qty_order * float(it.price or 0) * (1 + float(it.vat or 0) / 100), 2),
            "goods_total": round(sum(x["goods_total"] for x in del_out), 2),
            "paid_total": round(sum(x["paid"] for x in del_out), 2),
            "remaining_total": round(sum(x["remaining"] for x in del_out), 2),
            "deliveries": del_out}


def _out(db: Session, po: PurchaseOrder) -> dict:
    d = {c: getattr(po, c) for c in HEADER}
    d["vat_rate"] = float(po.vat_rate or 0)
    # Công nợ theo lần giao: HÀNG (goods) hiện đã trả/còn lại trên dòng; gom cả VẬN CHUYỂN cho tổng chưa trả
    all_pays = db.query(Payable).filter(Payable.po_id == po.id, Payable.ref_type == "delivery").all()
    pay_by_del = {p.ref_id: p for p in all_pays if p.source_type == "goods"}
    items = [_item(db, it, pay_by_del) for it in service.items_of(db, po.id)]
    d["items"] = items
    # Tổng theo SL THỰC NHẬN (thành tiền đơn hàng = đã chốt)
    subtotal = round(sum(i["qty_received"] * i["price"] for i in items), 2)
    vat = round(sum(i["amount"] - i["qty_received"] * i["price"] for i in items), 2)
    shipping = round(sum(dl["shipping_amount"] for i in items for dl in i["deliveries"]), 2)
    d["subtotal"] = subtotal
    d["vat"] = vat
    d["total"] = round(subtotal + vat, 2)
    d["shipping_total"] = shipping
    # Tổng theo SL ĐẶT (cho bản in đặt hàng gửi NCC)
    order_sub = round(sum(i["qty_order"] * i["price"] for i in items), 2)
    order_vat = round(sum(i["qty_order"] * i["price"] * (i["vat"] / 100) for i in items), 2)
    d["order_subtotal"] = order_sub
    d["order_total"] = round(order_sub + order_vat, 2)
    # Tổng công nợ CHƯA TRẢ (hàng + vận chuyển) → dùng bật nút Tạo yêu cầu thanh toán
    d["unpaid_total"] = round(sum(float(p.remaining or 0) for p in all_pays), 2)
    return d


@router.get("")
def list_po(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
            user=Depends(require("purchase_order", "read"))):
    q = apply_filters(db.query(PurchaseOrder), PurchaseOrder, request, service.FILTERABLE)
    q = apply_range_filters(q, PurchaseOrder, request, ["order_date"])
    q = apply_equals(q, PurchaseOrder, request, ["company_id"])
    item_group = (request.query_params.get("item_group") or "").strip()
    if item_group:
        sub = select(POItem.po_id).where(POItem.item_group.like(f"%{item_group}%"))
        q = q.filter(PurchaseOrder.id.in_(sub))
    invoice_no = (request.query_params.get("invoice_no") or "").strip()
    if invoice_no:
        sub2 = select(POItem.po_id).where(POItem.invoice_no.like(f"%{invoice_no}%"))
        q = q.filter(PurchaseOrder.id.in_(sub2))
    q = apply_scope(q, PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))
    total, items = service.list_po(db, q, pg)
    out = []
    for p in items:
        row = {c: getattr(p, c) for c in HEADER}
        row["amount"] = round(sum(float(i.amount or 0) for i in service.items_of(db, p.id)), 2)
        out.append(row)
    # Gắn pr_id (id phiếu YCMH theo mã PYC) để FE điều hướng sang chi tiết PYC khi click Mã PYC
    codes = {r["pr_code"] for r in out if r.get("pr_code")}
    if codes:
        from app.modules.purchase_request.model import PurchaseRequest
        id_by_code = {c: i for i, c in db.query(PurchaseRequest.id, PurchaseRequest.code)
                      .filter(PurchaseRequest.code.in_(codes)).all()}
        for r in out:
            r["pr_id"] = id_by_code.get(r.get("pr_code"))
    return success({"total": total, "items": out})


@router.get("/{pid}")
def get_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "read"))):
    scoped = apply_scope(db.query(PurchaseOrder).filter(PurchaseOrder.id == pid),
                         PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))
    if not scoped.first():
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, service.get_po(db, pid)))


@router.get("/{pid}/print")
def print_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "print"))):
    po = service.get_po(db, pid)
    data = _out(db, po)
    company = db.get(Company, po.company_id) if po.company_id else None
    sup = db.query(Supplier).filter(Supplier.code == po.supplier_code).first()
    data["company"] = {"name": company.name, "address": company.address, "tax_code": company.tax_code,
                       "invoice_email": company.invoice_email} if company else {}
    data["supplier"] = {"name": sup.name, "address": sup.address, "tax_code": sup.tax_code,
                        "payment_terms": sup.payment_terms} if sup else {}
    # Nơi nhận hàng = kho nhận (lấy kho đầu tiên có trên dòng hàng / lần giao)
    wcode = ""
    for it in data["items"]:
        wcode = it.get("warehouse_code") or next((d.get("warehouse_code") for d in it["deliveries"] if d.get("warehouse_code")), "")
        if wcode:
            break
    wh = db.query(Warehouse).filter(Warehouse.code == wcode).first() if wcode else None
    data["warehouse"] = {"code": wh.code, "name": wh.name, "address": wh.address} if wh else {}
    # Map mã kho -> tên kho (cho cột "Tên kho nhập" của Đơn mua hàng)
    codes = {it.get("warehouse_code") for it in data["items"] if it.get("warehouse_code")}
    codes |= {d.get("warehouse_code") for it in data["items"] for d in it["deliveries"] if d.get("warehouse_code")}
    whs = db.query(Warehouse).filter(Warehouse.code.in_(list(codes))).all() if codes else []
    data["wh_names"] = {w.code: w.name for w in whs}
    return success(data)


@router.post("")
def create_po(data: POCreate, db: Session = Depends(get_db), user=Depends(require("purchase_order", "create"))):
    return success(_out(db, service.create_po(db, data, user.id)), "Đã tạo đơn mua hàng", 201)


@router.post("/{pid}/copy")
def copy_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "create"))):
    return success(_out(db, service.copy_po(db, pid, user.id)), "Đã nhân bản thành đơn Nháp mới", 201)


@router.post("/{pid}/clone")
def clone_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "create"))):
    """Alias của /copy — dùng cho nút Nhân bản ở danh sách (đồng bộ với YCMH/YCKS)."""
    return success(_out(db, service.copy_po(db, pid, user.id)), "Đã nhân bản thành đơn Nháp mới", 201)


@router.patch("/{pid}")
def update_po(pid: int, data: POUpdate, db: Session = Depends(get_db), user=Depends(require("purchase_order", "write"))):
    return success(_out(db, service.update_po(db, pid, data, user.id)), "Đã cập nhật")


@router.delete("/{pid}")
def delete_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "delete"))):
    service.delete_po(db, pid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_pos(ids: str, db: Session = Depends(get_db), user=Depends(require("purchase_order", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    for pid in id_list:
        try:
            service.delete_po(db, pid, user.id)
        except Exception as e:
            raise HTTPException(400, f"Lỗi khi xóa đơn ID {pid}: {str(e)}")
    return success(None, f"Đã xóa {len(id_list)} bản ghi")


@router.post("/{pid}/submit")
def submit_po(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "write"))):
    po = service.set_status(db, pid, "submitted", user.id)
    trigger_notification(db=db, event="po_submitted", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         is_urgent=bool(po.is_urgent), link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã gửi duyệt")


@router.post("/{pid}/approve")
def approve_po(pid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
               user=Depends(require("purchase_order", "approve"))):
    po = service.set_status(db, pid, "approved", user.id)
    trigger_notification(db=db, event="po_approved", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã duyệt")


@router.post("/{pid}/reject")
def reject_po(pid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "approve"))):
    # Từ chối = KHÓA đơn (Đã từ chối) — không sửa/gửi lại được, phải Nhân bản thành đơn mới.
    po = service.set_status(db, pid, "cancelled", user.id, data.reason)
    trigger_notification(db=db, event="po_rejected", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã từ chối")


@router.post("/{pid}/return")
def return_po(pid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "approve"))):
    # Trả về = Bị trả lại — người tạo SỬA & GỬI DUYỆT LẠI được (đồng bộ YCMH).
    po = service.set_status(db, pid, "rejected", user.id, data.reason)
    trigger_notification(db=db, event="po_returned", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã trả đơn về (Bị trả lại)")


@router.post("/{pid}/cancel")
def cancel_po(pid: int, data: RejectIn, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "cancel"))):
    # Hủy phải có lý do
    if not (data.reason or "").strip():
        raise HTTPException(400, "Vui lòng nhập lý do hủy đơn")
    # Có sản phẩm nào đã Hoàn thành → KHÔNG cho hủy
    if db.query(POItem).filter(POItem.po_id == pid, POItem.progress_status == "Hoàn thành").first():
        raise HTTPException(400, "Đơn có sản phẩm đã Hoàn thành — không thể hủy")
    return success(_out(db, service.set_status(db, pid, "cancelled", user.id, data.reason)), "Đã hủy đơn")


@router.post("/{pid}/complete")
def complete_po(pid: int, db: Session = Depends(get_db),
                user=Depends(require("purchase_order", "write"))):
    return success(_out(db, service.set_status(db, pid, "completed", user.id)), "Đã hoàn thành đơn")


@router.post("/{pid}/reopen")
def reopen_po(pid: int, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "write"))):
    return success(_out(db, service.set_status(db, pid, "draft", user.id)), "Đã mở lại đơn (về nháp)")


@router.post("/{pid}/items/{item_id}/progress")
def set_item_progress(pid: int, item_id: int, data: ItemProgressIn, db: Session = Depends(get_db),
                      user=Depends(require("purchase_order", "write"))):
    """Người phụ trách cập nhật trạng thái tiến độ 1 dòng (có gate điều kiện) + đồng bộ sang YCMH."""
    return success(_out(db, service.set_item_progress(db, pid, item_id, data.status, data.reason, user.id)),
                   "Đã cập nhật trạng thái dòng")


