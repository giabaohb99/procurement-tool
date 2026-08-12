from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from app.modules.notification.service import trigger_notification

from app.core.audit import resolve_actor, resolve_actor_profile
from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, apply_range_filters, apply_equals, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.company.model import Company
from app.modules.payable.model import Payable
from app.modules.supplier.model import Supplier

from . import service
from .model import PaymentRequest
from .schema import PRequestCreate, PRequestUpdate

router = APIRouter(prefix="/api/payment-requests", tags=["payment_request"])

HEADER = ["id", "code", "supplier_code", "supplier_name", "company_id", "source_type",
          "request_date", "payment_method", "total", "note", "reject_reason", "status"]


def _line(db, ln) -> dict:
    """Tổng nợ / Đã trả / Hạn trả luôn ĐỌC từ Công nợ (không lưu trên phiếu, tránh lệch số);
    còn mã PO / số hóa đơn / ngày hóa đơn là dữ liệu nhập trên phiếu (CR-066).
    Dòng chưa khớp khoản nợ nào (form trắng, hàng chưa về) thì các cột nợ trả về 0 / rỗng."""
    req = db.get(PaymentRequest, ln.request_id) if ln.request_id else None
    payables = service.matching_payables(db, req.supplier_code, req.source_type,
                                         ln.po_code, ln.invoice_no) if req else []
    if not payables and ln.payable_id:
        p = db.get(Payable, ln.payable_id)
        payables = [p] if p else []

    tot = sum(float(px.total or 0) for px in payables)
    paid = sum(float(px.paid_amount or 0) for px in payables)
    due_date = min((px.due_date for px in payables if px.due_date), default="")
    incur_date = min((px.incur_date for px in payables if px.incur_date), default="")
    # Ngày hóa đơn: giá trị đã nhập trên phiếu > ngày hóa đơn của lần giao hàng
    invoice_date = (ln.invoice_date or "").strip() or service.delivery_invoice_date(db, payables)
    return {"id": ln.id, "payable_id": ln.payable_id, "po_code": ln.po_code,
            "invoice_no": ln.invoice_no, "amount": float(ln.amount or 0),
            "invoice_date": invoice_date, "due_date": due_date, "incur_date": incur_date,
            "payable_total": tot, "payable_paid": paid,
            "matched": bool(payables)}


def _out(db: Session, req: PaymentRequest) -> dict:
    d = {c: getattr(req, c) for c in HEADER}
    d["total"] = float(req.total or 0)
    d["created_by_name"] = resolve_actor(db, req.created_by)
    d["created_at"] = req.created_at
    d["lines"] = [_line(db, ln) for ln in service.lines_of(db, req.id)]
    return d


@router.get("")
def list_(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
          user=Depends(require("payment_request", "read"))):
    q = apply_filters(db.query(PaymentRequest), PaymentRequest, request, service.FILTERABLE)
    q = apply_range_filters(q, PaymentRequest, request, ["request_date"])
    q = apply_equals(q, PaymentRequest, request, ["company_id"])
    po_code = (request.query_params.get("po_code") or "").strip()
    if po_code:
        from sqlalchemy import select
        from .model import PaymentRequestLine
        sub = select(PaymentRequestLine.request_id).where(PaymentRequestLine.po_code.like(f"%{po_code}%"))
        q = q.filter(PaymentRequest.id.in_(sub))
    q = apply_scope(q, PaymentRequest, "payment_request", user, get_perm_profile(db, user))
    total = q.count()
    q = apply_sort_from_request(q, PaymentRequest, request, default=PaymentRequest.id.desc())
    items = q.offset(pg["offset"]).limit(pg["limit"]).all()
    out = [{c: getattr(p, c) for c in HEADER}
           | {"total": float(p.total or 0), "created_by_name": resolve_actor(db, p.created_by)}
           for p in items]
    return success({"total": total, "items": out})


@router.get("/{rid}")
def get_(rid: int, db: Session = Depends(get_db), user=Depends(require("payment_request", "read"))):
    from fastapi import HTTPException
    req = apply_scope(db.query(PaymentRequest).filter(PaymentRequest.id == rid),
                      PaymentRequest, "payment_request", user, get_perm_profile(db, user)).first()
    if not req:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, req))


@router.get("/{rid}/print")
def print_(rid: int, db: Session = Depends(get_db), user=Depends(require("payment_request", "print"))):
    req = service.get_request(db, rid)
    data = _out(db, req)
    company = db.get(Company, req.company_id) if req.company_id else None
    data["company"] = {"name": company.name, "address": company.address,
                       "tax_code": company.tax_code} if company else {}
    prof = resolve_actor_profile(db, req.created_by)
    data["created_by_name"] = prof["name"]
    data["created_by_position"] = prof["position"]     # Chức vụ
    data["created_by_dept"] = prof["department"]        # Bộ phận
    data["dept_manager"] = prof["manager"]              # Trưởng phòng ban/bộ phận
    # Thông tin ngân hàng NCC (khớp theo mã NCC) để in mục HÌNH THỨC THANH TOÁN.
    # CR-035: phiếu chi TIỀN MẶT thì cụm chuyển khoản để trống — chặn ngay từ server,
    # không gửi số TK ra bản in.
    method = service.norm_method(req.payment_method)
    data["payment_method"] = method
    sup = db.query(Supplier).filter(Supplier.code == req.supplier_code).first() if req.supplier_code else None
    data["bank_account"] = (sup.bank_account if sup else "") if method == "transfer" else ""
    data["bank_name"] = (sup.bank_name if sup else "") if method == "transfer" else ""
    data["period"] = (req.request_date or "")[:7]  # YYYY-MM
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


@router.delete("")
def bulk_delete_requests(ids: str, db: Session = Depends(get_db), user=Depends(require("payment_request", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    for rid in id_list:
        try:
            service.delete_request(db, rid, user.id)
        except Exception as e:
            raise HTTPException(400, f"Lỗi khi xóa phiếu ID {rid}: {str(e)}")
    return success(None, f"Đã xóa {len(id_list)} bản ghi")


def _notify_pay(db, background_tasks, r, event, reason=""):
    trigger_notification(db=db, event=event, doc_type="payment_request", doc_code=r.code,
                         creator_id=r.created_by or 0, background_tasks=background_tasks,
                         reason=reason, link=f"/payment-requests/{r.id}")


@router.post("/{rid}/submit")
def submit_(rid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("payment_request", "write"))):
    r = service.set_status(db, rid, "submitted", user.id)
    _notify_pay(db, background_tasks, r, "pay_submitted")
    return success(_out(db, r), "Đã gửi duyệt")


@router.post("/{rid}/approve")
def approve_(rid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
             user=Depends(require("payment_request", "approve"))):
    r = service.set_status(db, rid, "approved", user.id)
    _notify_pay(db, background_tasks, r, "pay_approved")
    return success(_out(db, r), "Đã duyệt")


@router.post("/{rid}/reject")
def reject_(rid: int, data: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("payment_request", "approve"))):
    """Từ chối phiếu yêu cầu thanh toán (khóa) — người duyệt thao tác. Body: {reason}."""
    reason = (data.get("reason") or "").strip()
    r = service.set_status(db, rid, "cancelled", user.id, reason)
    _notify_pay(db, background_tasks, r, "pay_rejected", reason)
    return success(_out(db, r), "Đã từ chối")


@router.post("/{rid}/pay")
def pay_(rid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
         user=Depends(require("payment_request", "write"))):
    r = service.set_status(db, rid, "paid", user.id)
    _notify_pay(db, background_tasks, r, "pay_paid")
    return success(_out(db, r), "Đã ghi nhận chi")
