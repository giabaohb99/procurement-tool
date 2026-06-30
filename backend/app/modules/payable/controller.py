from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .model import Payable

router = APIRouter(prefix="/api/payables", tags=["payable"])


def _out(p: Payable) -> dict:
    total = float(p.total or 0)
    paid = float(p.paid_amount or 0)
    return {
        "id": p.id, "company_id": p.company_id, "supplier_code": p.supplier_code,
        "supplier_name": p.supplier_name, "source_type": p.source_type,
        "po_id": p.po_id, "po_code": p.po_code, "invoice_no": p.invoice_no,
        "incur_date": p.incur_date, "due_date": p.due_date,
        "amount": float(p.amount or 0), "vat": float(p.vat or 0), "total": total,
        "paid_amount": paid, "remaining": round(total - paid, 2),
        "status": p.status, "aging": service.aging_bucket(p.due_date),
    }


def _filtered(db: Session, request: Request):
    q = apply_filters(db.query(Payable), Payable, request, service.FILTERABLE)
    company_id = request.query_params.get("company_id")
    if company_id:
        q = q.filter(Payable.company_id == int(company_id))
    return q


@router.get("")
def list_payables(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
                  user=Depends(require("payable", "read"))):
    q = _filtered(db, request)
    aging = request.query_params.get("aging")
    rows = q.order_by(Payable.due_date.asc(), Payable.id.desc()).all()
    items = [_out(p) for p in rows]
    if aging:
        items = [i for i in items if i["aging"] == aging]
    total = len(items)
    items = items[pg["offset"]: pg["offset"] + pg["limit"]]
    return success({"total": total, "items": items})


@router.get("/summary")
def summary(request: Request, db: Session = Depends(get_db), user=Depends(require("payable", "read"))):
    rows = _filtered(db, request).all()
    tot = sum(float(p.total or 0) for p in rows)
    paid = sum(float(p.paid_amount or 0) for p in rows)
    overdue = sum(
        round(float(p.total or 0) - float(p.paid_amount or 0), 2)
        for p in rows if service.aging_bucket(p.due_date) != "Chưa đến hạn" and p.status != "Đã TT"
    )
    return success({"total": round(tot, 2), "paid": round(paid, 2),
                    "remaining": round(tot - paid, 2), "overdue": round(overdue, 2)})
