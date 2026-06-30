"""Công nợ: sinh ngầm khi nhận hàng (2 luồng goods/shipping) + tính lại trạng thái trả."""
import re
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .model import Payable

FILTERABLE = ["supplier_code", "po_code", "source_type", "status"]


def debt_days(payment_terms: str) -> int:
    """Suy ra số ngày công nợ từ hình thức thanh toán của NCC (vd 'Công nợ 30 ngày')."""
    m = re.search(r"(\d+)\s*ng[aà]y", payment_terms or "", re.IGNORECASE)
    return int(m.group(1)) if m else 0


def calc_due(incur_date: str, days: int) -> str:
    if not incur_date:
        incur_date = datetime.now().strftime("%Y-%m-%d")
    try:
        d = datetime.strptime(incur_date, "%Y-%m-%d")
    except ValueError:
        return incur_date
    return (d + timedelta(days=days or 0)).strftime("%Y-%m-%d")


def recalc_status(p: Payable):
    paid = float(p.paid_amount or 0)
    total = float(p.total or 0)
    p.remaining = round(total - paid, 2)   # tính sẵn, không sum lúc đọc
    if paid <= 0:
        p.status = "Chờ TT"
    elif paid + 0.01 < total:
        p.status = "Trả một phần"
    else:
        p.status = "Đã TT"


def upsert(db: Session, *, source_type: str, ref_id: int, company_id: int, supplier_code: str,
           supplier_name: str, po_id: int, po_code: str, invoice_no: str, incur_date: str,
           amount: float, vat: float, due_days: int, user_id: int):
    """Tạo/cập nhật 1 khoản nợ (idempotent theo source_type + ref_id = delivery_id)."""
    p = db.query(Payable).filter(
        Payable.source_type == source_type, Payable.ref_type == "delivery", Payable.ref_id == ref_id
    ).first()
    if not p:
        p = Payable(source_type=source_type, ref_type="delivery", ref_id=ref_id, created_by=user_id)
        db.add(p)
    p.company_id = company_id
    p.supplier_code = supplier_code
    p.supplier_name = supplier_name
    p.po_id = po_id
    p.po_code = po_code
    p.invoice_no = invoice_no
    p.incur_date = incur_date
    p.period = (incur_date or "")[:4]
    p.due_date = calc_due(incur_date, due_days)
    p.amount = round(amount, 2)
    p.vat = round(vat, 2)
    p.total = round(amount + vat, 2)
    p.updated_by = user_id
    recalc_status(p)
    db.flush()
    return p


def remove(db: Session, source_type: str, ref_id: int):
    p = db.query(Payable).filter(
        Payable.source_type == source_type, Payable.ref_type == "delivery", Payable.ref_id == ref_id
    ).first()
    if p:
        db.delete(p)
        db.flush()


def aging_bucket(due_date: str) -> str:
    if not due_date:
        return "Chưa đến hạn"
    try:
        d = datetime.strptime(due_date, "%Y-%m-%d").date()
    except ValueError:
        return "Chưa đến hạn"
    overdue = (datetime.now().date() - d).days
    if overdue <= 0:
        return "Chưa đến hạn"
    if overdue <= 30:
        return "1-30"
    if overdue <= 60:
        return "31-60"
    if overdue <= 90:
        return "61-90"
    return ">90"
