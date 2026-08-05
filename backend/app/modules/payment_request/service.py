"""Yêu cầu thanh toán: gom khoản nợ theo NCC (mỗi NCC 1 phiếu); khi 'Đã chi' cập nhật payable."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.payable.model import Payable
from app.modules.payable.service import recalc_status

from .model import PaymentRequest, PaymentRequestLine
from .schema import PRequestCreate, PRequestUpdate

# request_date: cho bộ lọc điều kiện lọc theo ngày (apply_range_filters vẫn lo _from/_to)
FILTERABLE = ["code", "supplier_code", "status", "source_type", "request_date"]
ENTITY = "payment_request"


def get_request(db: Session, rid: int) -> PaymentRequest:
    obj = db.get(PaymentRequest, rid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy phiếu yêu cầu thanh toán")
    return obj


def lines_of(db: Session, rid: int):
    return db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == rid).all()


def create_requests(db: Session, data: PRequestCreate, user_id: int) -> list[PaymentRequest]:
    """Tạo phiếu; nếu các khoản nợ thuộc nhiều NCC -> tách mỗi NCC 1 phiếu;
    Gom các khoản nợ cùng (mã PO + Số HĐ) thành 1 dòng duy nhất trên phiếu thanh toán."""
    if not data.lines:
        raise HTTPException(400, "Chưa chọn khoản công nợ nào")

    # gom theo (supplier_code, source_type)
    groups: dict[tuple, list] = {}
    missing = []
    for ln in data.lines:
        p = db.get(Payable, ln.payable_id)
        if not p:
            continue
        if not (p.invoice_no or "").strip():
            missing.append(p.po_code or str(p.id))
            continue
        amt = ln.amount if ln.amount > 0 else round(float(p.total or 0) - float(p.paid_amount or 0), 2)
        groups.setdefault((p.supplier_code, p.source_type), []).append((p, amt))

    if missing:
        raise HTTPException(400, f"Các khoản nợ chưa có Số hóa đơn, không thể tạo đề nghị thanh toán: {', '.join(missing)}")

    if not groups:
        raise HTTPException(400, "Khoản công nợ không hợp lệ")

    created = []
    for (supplier_code, source_type), items in groups.items():
        first = items[0][0]
        # Gom các item có cùng (po_code, invoice_no) thành 1 dòng
        sub_groups: dict[tuple, list] = {}
        for p, amt in items:
            key = (p.po_code or "", (p.invoice_no or "").strip())
            sub_groups.setdefault(key, []).append((p, amt))

        req = PaymentRequest(
            supplier_code=supplier_code, supplier_name=first.supplier_name,
            company_id=first.company_id, source_type=source_type,
            request_date=data.request_date, note=data.note, status="draft",
            total=round(sum(a for _, a in items), 2), created_by=user_id, updated_by=user_id)
        db.add(req)
        db.flush()
        req.code = f"YCTT{req.id:05d}"

        for (po_code, inv_no), sub_items in sub_groups.items():
            lead_p = sub_items[0][0]
            line_amt = round(sum(a for _, a in sub_items), 2)
            db.add(PaymentRequestLine(request_id=req.id, payable_id=lead_p.id, po_code=po_code,
                                      invoice_no=inv_no, amount=line_amt,
                                      created_by=user_id, updated_by=user_id))
        db.flush()
        created.append(req)
    db.commit()
    for req in created:
        record(db, user_id, ENTITY, req.id, "create")
    return created


def update_request(db: Session, rid: int, data: PRequestUpdate, user_id: int) -> PaymentRequest:
    req = get_request(db, rid)
    if req.status == "paid":
        raise HTTPException(400, "Phiếu đã chi, không sửa được")
    for k, v in data.model_dump(exclude_unset=True, exclude={"lines"}).items():
        setattr(req, k, v)
    if data.lines is not None:
        db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == rid).delete()
        raw_items = []
        for ln in data.lines:
            p = db.get(Payable, ln.payable_id)
            if not p or p.supplier_code != req.supplier_code:
                continue
            amt = ln.amount if ln.amount > 0 else round(float(p.total or 0) - float(p.paid_amount or 0), 2)
            raw_items.append((p, amt))

        sub_groups: dict[tuple, list] = {}
        for p, amt in raw_items:
            key = (p.po_code or "", (p.invoice_no or "").strip())
            sub_groups.setdefault(key, []).append((p, amt))

        total = 0.0
        for (po_code, inv_no), sub_items in sub_groups.items():
            lead_p = sub_items[0][0]
            line_amt = round(sum(a for _, a in sub_items), 2)
            total += line_amt
            db.add(PaymentRequestLine(request_id=rid, payable_id=lead_p.id, po_code=po_code,
                                      invoice_no=inv_no, amount=line_amt,
                                      created_by=user_id, updated_by=user_id))
        req.total = round(total, 2)
    req.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, rid, "update")
    db.refresh(req)
    return req


def delete_request(db: Session, rid: int, user_id: int):
    req = get_request(db, rid)
    if req.status == "paid":
        raise HTTPException(400, "Phiếu đã chi, không xóa được")
    from app.modules.attachment.service import delete_attachments_for
    delete_attachments_for(db, [("payment_request", rid)])
    db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == rid).delete()
    db.delete(req)
    db.commit()
    record(db, user_id, ENTITY, rid, "delete")


def set_status(db: Session, rid: int, status: str, user_id: int, reason: str = "") -> PaymentRequest:
    req = get_request(db, rid)
    req.status = status
    req.updated_by = user_id
    if status == "cancelled":
        req.reject_reason = reason
    affected_po_ids: set[int] = set()
    if status == "paid":
        # cộng tiền đã trả vào các khoản nợ (phân bổ theo po_code + invoice_no)
        for ln in lines_of(db, rid):
            rem_to_pay = float(ln.amount or 0)
            if rem_to_pay <= 0:
                continue
            matched_payables = db.query(Payable).filter(
                Payable.supplier_code == req.supplier_code,
                Payable.source_type == req.source_type,
                Payable.po_code == ln.po_code,
                Payable.invoice_no == ln.invoice_no
            ).all()
            if not matched_payables and ln.payable_id:
                p_single = db.get(Payable, ln.payable_id)
                if p_single:
                    matched_payables = [p_single]

            for p in matched_payables:
                if rem_to_pay <= 0:
                    break
                p_rem = max(0.0, float(p.total or 0) - float(p.paid_amount or 0))
                pay_part = min(rem_to_pay, p_rem) if p_rem > 0 else rem_to_pay
                p.paid_amount = round(float(p.paid_amount or 0) + pay_part, 2)
                recalc_status(p)
                rem_to_pay = round(rem_to_pay - pay_part, 2)

                if p.source_type == "goods" and p.ref_type == "delivery":
                    from app.modules.purchase_order.model import PODelivery
                    d = db.get(PODelivery, p.ref_id)
                    if d:
                        affected_po_ids.add(d.po_id)
    db.commit()
    record(db, user_id, ENTITY, rid, status, reason)
    if status == "paid" and affected_po_ids:
        # tự tiến trạng thái dòng ĐMH; KHÔNG được làm hỏng thao tác chi tiền (đã commit)
        try:
            # LAZY import tránh circular (purchase_order ↔ payment/payable)
            from app.modules.purchase_order import service as po_service
            from app.modules.purchase_order.model import PurchaseOrder
            for po_id in affected_po_ids:
                po = db.get(PurchaseOrder, po_id)
                if po:
                    po_service.apply_auto_progress(db, po, user_id)
        except Exception:
            db.rollback()
    db.refresh(req)
    return req
