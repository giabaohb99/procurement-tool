from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success
from app.modules.company.model import Company
from app.modules.payable.model import Payable

from . import service
from .model import PaymentRequest
from .schema import PRequestCreate, PRequestUpdate

router = APIRouter(prefix="/api/payment-requests", tags=["payment_request"])

HEADER = ["id", "code", "supplier_code", "supplier_name", "company_id", "source_type",
          "request_date", "total", "note", "status"]


def _line(db, ln) -> dict:
    p = db.get(Payable, ln.payable_id)
    return {"id": ln.id, "payable_id": ln.payable_id, "po_code": ln.po_code,
            "invoice_no": ln.invoice_no, "amount": float(ln.amount or 0),
            "due_date": p.due_date if p else "", "incur_date": p.incur_date if p else "",
            "payable_total": float(p.total or 0) if p else 0,
            "payable_paid": float(p.paid_amount or 0) if p else 0}


def _out(db: Session, req: PaymentRequest) -> dict:
    d = {c: getattr(req, c) for c in HEADER}
    d["total"] = float(req.total or 0)
    d["lines"] = [_line(db, ln) for ln in service.lines_of(db, req.id)]
    return d


@router.get("")
def list_(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
          user=Depends(require("payment_request", "read"))):
    q = apply_filters(db.query(PaymentRequest), PaymentRequest, request, service.FILTERABLE)
    total = q.count()
    items = q.order_by(PaymentRequest.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    out = [{c: getattr(p, c) for c in HEADER} | {"total": float(p.total or 0)} for p in items]
    return success({"total": total, "items": out})


@router.get("/{rid}")
def get_(rid: int, db: Session = Depends(get_db), user=Depends(require("payment_request", "read"))):
    return success(_out(db, service.get_request(db, rid)))


@router.get("/{rid}/print")
def print_(rid: int, db: Session = Depends(get_db), user=Depends(require("payment_request", "print"))):
    req = service.get_request(db, rid)
    data = _out(db, req)
    company = db.get(Company, req.company_id) if req.company_id else None
    data["company"] = {"name": company.name, "address": company.address,
                       "tax_code": company.tax_code} if company else {}
    return success(data)


@router.post("")
def create_(data: PRequestCreate, db: Session = Depends(get_db),
            user=Depends(require("payment_request", "create"))):
    reqs = service.create_requests(db, data, user.id)
    return success([_out(db, r) for r in reqs],
                   f"Đã tạo {len(reqs)} phiếu yêu cầu thanh toán", 201)


@router.patch("/{rid}")
def update_(rid: int, data: PRequestUpdate, db: Session = Depends(get_db),
            user=Depends(require("payment_request", "write"))):
    return success(_out(db, service.update_request(db, rid, data, user.id)), "Đã cập nhật")


@router.delete("/{rid}")
def delete_(rid: int, db: Session = Depends(get_db), user=Depends(require("payment_request", "delete"))):
    service.delete_request(db, rid, user.id)
    return success(None, "Đã xóa")


@router.post("/{rid}/submit")
def submit_(rid: int, db: Session = Depends(get_db), user=Depends(require("payment_request", "write"))):
    return success(_out(db, service.set_status(db, rid, "submitted", user.id)), "Đã gửi duyệt")


@router.post("/{rid}/approve")
def approve_(rid: int, db: Session = Depends(get_db), user=Depends(require("payment_request", "approve"))):
    return success(_out(db, service.set_status(db, rid, "approved", user.id)), "Đã duyệt")


@router.post("/{rid}/pay")
def pay_(rid: int, db: Session = Depends(get_db), user=Depends(require("payment_request", "write"))):
    return success(_out(db, service.set_status(db, rid, "paid", user.id)), "Đã ghi nhận chi")
