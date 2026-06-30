from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success

from sqlalchemy import func
from . import service
from .model import PurchaseRequest, PurchaseRequestItem
from .schema import ApproveIn, PRCreate, PRUpdate, RejectIn

router = APIRouter(prefix="/api/purchase-requests", tags=["purchase_request"])

HEADER_COLS = ["id", "code", "company_id", "requester", "requester_position",
               "department", "head_of_dept", "purpose", "request_date", "need_date",
               "status", "is_urgent", "vat_rate", "assignee_id", "note",
               "show_code_on_print", "suggested_supplier", "suggested_supplier_tax_code",
               "suggested_supplier_contact", "quote_filename", "quote_file_url"]


def _out(db: Session, pr) -> dict:
    d = {c: getattr(pr, c) for c in HEADER_COLS}
    d["vat_rate"] = float(pr.vat_rate or 0)
    items = service.items_of(db, pr.id)
    d["items"] = [
        {"id": i.id, "product_code": i.product_code, "product_name": i.product_name,
         "item_group": i.item_group, "group_desc": i.group_desc, "qty": float(i.qty or 0),
         "unit": i.unit, "price": float(i.price or 0), "amount": float(i.amount or 0),
         "warehouse": i.warehouse, "assignee": i.assignee, "line_status": i.line_status,
         "progress_note": i.progress_note, "note": i.note}
        for i in items
    ]
    subtotal = round(sum(x["amount"] for x in d["items"]), 2)
    vat = round(subtotal * d["vat_rate"], 2)
    d["subtotal"] = subtotal
    d["vat"] = vat
    d["total"] = round(subtotal + vat, 2)
    return d


@router.get("")
def list_pr(
    request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
    user=Depends(require("purchase_request", "read")),
):
    query = apply_filters(db.query(PurchaseRequest), PurchaseRequest, request, service.FILTERABLE)
    total, items = service.list_pr(db, query, pg)
    
    pr_ids = [p.id for p in items]
    subtotals = {}
    if pr_ids:
        subtotals = {
            pr_id: float(amount or 0) for pr_id, amount in db.query(
                PurchaseRequestItem.pr_id,
                func.sum(PurchaseRequestItem.amount)
            ).filter(PurchaseRequestItem.pr_id.in_(pr_ids)).group_by(PurchaseRequestItem.pr_id).all()
        }
        
    out_items = []
    for p in items:
        d = {c: getattr(p, c) for c in HEADER_COLS}
        subtotal = subtotals.get(p.id, 0.0)
        vat = round(subtotal * float(p.vat_rate or 0), 2)
        d["total"] = round(subtotal + vat, 2)
        out_items.append(d)
        
    return success({"total": total, "items": out_items})


@router.get("/{pid}")
def get_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "read"))):
    return success(_out(db, service.get_pr(db, pid)))


@router.post("")
def create_pr(data: PRCreate, db: Session = Depends(get_db), user=Depends(require("purchase_request", "create"))):
    return success(_out(db, service.create_pr(db, data, user.id)), "Đã tạo yêu cầu mua", 201)


@router.patch("/{pid}")
def update_pr(pid: int, data: PRUpdate, db: Session = Depends(get_db), user=Depends(require("purchase_request", "write"))):
    return success(_out(db, service.update_pr(db, pid, data, user.id)), "Đã cập nhật")


@router.delete("/{pid}")
def delete_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "delete"))):
    service.delete_pr(db, pid, user.id)
    return success(None, "Đã xóa")


@router.post("/{pid}/submit")
def submit_pr(pid: int, db: Session = Depends(get_db), user=Depends(require("purchase_request", "write"))):
    return success(_out(db, service.set_status(db, pid, "submitted", user.id)), "Đã gửi duyệt")


@router.post("/{pid}/approve")
def approve_pr(pid: int, data: ApproveIn, db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    pr = service.set_status(db, pid, "approved", user.id)
    if data.assignee_id:
        pr.assignee_id = data.assignee_id
        db.commit()
    return success(_out(db, pr), "Đã duyệt")


@router.post("/{pid}/reject")
def reject_pr(pid: int, data: RejectIn, db: Session = Depends(get_db), user=Depends(require("purchase_request", "approve"))):
    return success(_out(db, service.set_status(db, pid, "rejected", user.id, data.reason)), "Đã từ chối")
