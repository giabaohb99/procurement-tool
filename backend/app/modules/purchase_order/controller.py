from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.company.model import Company
from app.modules.supplier.model import Supplier
from app.modules.catalog.model import Warehouse
from app.modules.notification.service import trigger_notification

from . import service
from .model import PurchaseOrder
from .schema import POCreate, POUpdate, RejectIn

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase_order"])

HEADER = ["id", "code", "misa_code", "pr_code", "survey_code", "company_id", "supplier_code",
          "supplier_name", "department", "nspt", "order_date", "vat_rate", "payment_terms",
          "is_urgent", "status", "note", "approve_note"]


def _delivery(d) -> dict:
    return {"id": d.id, "delivery_no": d.delivery_no, "warehouse_code": d.warehouse_code,
            "carrier_code": d.carrier_code, "carrier_name": d.carrier_name,
            "ship_qty": float(d.ship_qty or 0), "ship_unit": d.ship_unit,
            "received_qty": float(d.received_qty or 0), "promised_date": d.promised_date,
            "expected_date": d.expected_date, "received_date": d.received_date,
            "std_days": d.std_days, "regulated_date": d.regulated_date,
            "diff_promise": d.diff_promise, "diff_regulated": d.diff_regulated, "diff_required": d.diff_required,
            "invoice_no": d.invoice_no, "shipping_unit_price": float(d.shipping_unit_price or 0),
            "shipping_amount": float(d.shipping_amount or 0), "qc_result": d.qc_result,
            "status": d.status, "extra_request": d.extra_request, "progress_note": d.progress_note}


def _item(db, it) -> dict:
    return {"id": it.id, "product_code": it.product_code, "product_name": it.product_name,
            "invoice_name": it.invoice_name, "item_group": it.item_group, "spec": it.spec,
            "fg_code": it.fg_code, "invoice_no": it.invoice_no,
            "supplier_ready": bool(it.supplier_ready), "required_date": it.required_date,
            "unit": it.unit, "qty_request": float(it.qty_request or 0), "qty_order": float(it.qty_order or 0),
            "price": float(it.price or 0), "vat": float(it.vat or 0), "amount": float(it.amount or 0),
            "qty_received": float(it.qty_received or 0), "qty_remaining": float(it.qty_remaining or 0),
            "line_status": it.line_status, "warehouse_code": it.warehouse_code, "note": it.note,
            "deliveries": [_delivery(d) for d in service.deliveries_of(db, it.id)]}


def _out(db: Session, po: PurchaseOrder) -> dict:
    d = {c: getattr(po, c) for c in HEADER}
    d["vat_rate"] = float(po.vat_rate or 0)
    items = [_item(db, it) for it in service.items_of(db, po.id)]
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
    return d


@router.get("")
def list_po(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
            user=Depends(require("purchase_order", "read"))):
    q = apply_filters(db.query(PurchaseOrder), PurchaseOrder, request, service.FILTERABLE)
    q = apply_scope(q, PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))
    total, items = service.list_po(db, q, pg)
    out = []
    for p in items:
        row = {c: getattr(p, c) for c in HEADER}
        row["amount"] = round(sum(float(i.amount or 0) for i in service.items_of(db, p.id)), 2)
        out.append(row)
    return success({"total": total, "items": out})


@router.get("/{pid}")
def get_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "read"))):
    scoped = apply_scope(db.query(PurchaseOrder).filter(PurchaseOrder.id == pid),
                         PurchaseOrder, "purchase_order", user, get_perm_profile(db, user))
    if not scoped.first():
        from fastapi import HTTPException
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


@router.patch("/{pid}")
def update_po(pid: int, data: POUpdate, db: Session = Depends(get_db), user=Depends(require("purchase_order", "write"))):
    return success(_out(db, service.update_po(db, pid, data, user.id)), "Đã cập nhật")


@router.delete("/{pid}")
def delete_po(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_order", "delete"))):
    service.delete_po(db, pid, user.id)
    return success(None, "Đã xóa")


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
    po = service.set_status(db, pid, "rejected", user.id, data.reason)
    trigger_notification(db=db, event="po_rejected", doc_type="purchase_order", doc_code=po.code,
                         creator_id=po.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/purchase-orders/{po.id}")
    return success(_out(db, po), "Đã từ chối")


@router.post("/{pid}/cancel")
def cancel_po(pid: int, data: RejectIn, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "write"))):
    return success(_out(db, service.set_status(db, pid, "cancelled", user.id, data.reason)), "Đã hủy đơn")


@router.post("/{pid}/complete")
def complete_po(pid: int, db: Session = Depends(get_db),
                user=Depends(require("purchase_order", "write"))):
    return success(_out(db, service.set_status(db, pid, "completed", user.id)), "Đã hoàn thành đơn")


@router.post("/{pid}/reopen")
def reopen_po(pid: int, db: Session = Depends(get_db),
              user=Depends(require("purchase_order", "write"))):
    return success(_out(db, service.set_status(db, pid, "draft", user.id)), "Đã mở lại đơn (về nháp)")
