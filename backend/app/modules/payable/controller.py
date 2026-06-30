from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .model import Payable

router = APIRouter(prefix="/api/payables", tags=["payable"])


def _out(p: Payable) -> dict:
    return {
        "id": p.id, "company_id": p.company_id, "supplier_code": p.supplier_code,
        "supplier_name": p.supplier_name, "source_type": p.source_type,
        "po_id": p.po_id, "po_code": p.po_code, "invoice_no": p.invoice_no,
        "incur_date": p.incur_date, "due_date": p.due_date,
        "amount": float(p.amount or 0), "vat": float(p.vat or 0), "total": float(p.total or 0),
        "paid_amount": float(p.paid_amount or 0), "remaining": float(p.remaining or 0),
        "status": p.status, "aging": service.aging_bucket(p.due_date),
    }


def _today():
    return datetime.now().date()


def _filtered(db: Session, request: Request):
    """Lọc ở DB (không nạp toàn bộ). Mặc định theo năm hiện tại để giới hạn dữ liệu."""
    q = apply_filters(db.query(Payable), Payable, request, service.FILTERABLE)
    company_id = request.query_params.get("company_id")
    if company_id:
        q = q.filter(Payable.company_id == int(company_id))
    year = request.query_params.get("year")
    if year is None:
        year = str(_today().year)
    if year and year != "all":
        q = q.filter(Payable.period == year)

    aging = request.query_params.get("aging")
    if aging:
        t = _today()
        def s(days): return (t - timedelta(days=days)).strftime("%Y-%m-%d")
        today = t.strftime("%Y-%m-%d")
        if aging == "Chưa đến hạn":
            q = q.filter((Payable.due_date == "") | (Payable.due_date >= today))
        elif aging == "1-30":
            q = q.filter(Payable.due_date >= s(30), Payable.due_date <= s(1))
        elif aging == "31-60":
            q = q.filter(Payable.due_date >= s(60), Payable.due_date <= s(31))
        elif aging == "61-90":
            q = q.filter(Payable.due_date >= s(90), Payable.due_date <= s(61))
        elif aging == ">90":
            q = q.filter(Payable.due_date != "", Payable.due_date <= s(91))
    return q


@router.get("")
def list_payables(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
                  user=Depends(require("payable", "read"))):
    q = _filtered(db, request)
    total = q.count()
    rows = (q.order_by(Payable.due_date.asc(), Payable.id.desc())
            .offset(pg["offset"]).limit(pg["limit"]).all())
    return success({"total": total, "items": [_out(p) for p in rows]})


@router.get("/summary")
def summary(request: Request, db: Session = Depends(get_db), user=Depends(require("payable", "read"))):
    today = _today().strftime("%Y-%m-%d")
    q = _filtered(db, request)
    overdue_case = case(
        (((Payable.status != "Đã TT") & (Payable.due_date != "") & (Payable.due_date < today)), Payable.remaining),
        else_=0,
    )
    row = q.with_entities(
        func.coalesce(func.sum(Payable.total), 0),
        func.coalesce(func.sum(Payable.paid_amount), 0),
        func.coalesce(func.sum(Payable.remaining), 0),
        func.coalesce(func.sum(overdue_case), 0),
    ).one()
    return success({"total": float(row[0]), "paid": float(row[1]),
                    "remaining": float(row[2]), "overdue": float(row[3])})
