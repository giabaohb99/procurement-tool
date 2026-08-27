"""Yêu cầu thanh toán: gom khoản nợ theo NCC (mỗi NCC 1 phiếu); khi 'Đã chi' cập nhật payable."""
import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.payable.model import Payable
from app.modules.payable.service import recalc_status
from app.modules.supplier.model import Supplier

from .model import PaymentRequest, PaymentRequestLine
from .schema import PRequestCreate, PRequestUpdate

# request_date: cho bộ lọc điều kiện lọc theo ngày (apply_range_filters vẫn lo _from/_to)
FILTERABLE = ["code", "supplier_code", "status", "source_type", "request_date", "payment_method"]
ENTITY = "payment_request"

# CR-035 — hình thức thanh toán. Mặc định 'transfer' để phiếu cũ giữ nguyên bản in (có chuyển khoản).
PAYMENT_METHODS = ("transfer", "cash")


def norm_method(v) -> str:
    """Chuẩn hóa hình thức thanh toán; giá trị lạ -> 'transfer' (không để bản in mất thông tin NCC)."""
    return v if v in PAYMENT_METHODS else "transfer"


# CR-149 (ticket #14) — 3 câu chữ bản in người dùng sửa được: Nội dung thanh toán /
# Diễn giải bảng / Nội dung chuyển khoản. Chỉ nhận đúng 3 khóa này, khóa lạ bị bỏ.
PRINT_TEXT_KEYS = ("content", "line_desc", "transfer")
PRINT_TEXT_MAX = 500   # câu in trên khổ A4, dài hơn là tràn dòng — cắt thẳng tay


def norm_print_texts(v) -> str:
    """Chuẩn hóa dict người dùng gửi -> chuỗi JSON lưu DB; cả 3 khóa rỗng -> lưu ""
    (bản in rơi về câu tự động theo prepay như trước CR-149)."""
    if not isinstance(v, dict):
        return ""
    out = {}
    for k in PRINT_TEXT_KEYS:
        s = str(v.get(k) or "").strip()[:PRINT_TEXT_MAX]
        if s:
            out[k] = s
    return json.dumps(out, ensure_ascii=False) if out else ""


def parse_print_texts(raw) -> dict:
    """Đọc cột print_texts (JSON) -> dict cho API/bản in; rỗng hay hỏng -> {} (câu tự động)."""
    try:
        d = json.loads(raw or "")
    except (ValueError, TypeError):
        return {}
    if not isinstance(d, dict):
        return {}
    return {k: str(d[k]) for k in PRINT_TEXT_KEYS if str(d.get(k) or "").strip()}


def get_request(db: Session, rid: int) -> PaymentRequest:
    obj = db.get(PaymentRequest, rid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy phiếu yêu cầu thanh toán")
    return obj


def lines_of(db: Session, rid: int):
    return db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == rid).all()


def matching_payables(db: Session, supplier_code: str, source_type: str,
                      po_code: str, invoice_no: str) -> list[Payable]:
    """Các khoản công nợ ứng với 1 dòng phiếu — khớp theo (NCC + loại + mã PO + số hóa đơn).

    Một hóa đơn có thể ứng với NHIỀU khoản nợ (mỗi lần giao 1 khoản), nên trả về danh sách.
    Chưa có số hóa đơn thì coi như chưa khớp được khoản nào."""
    if not (invoice_no or "").strip() or not supplier_code:
        return []
    return db.query(Payable).filter(
        Payable.supplier_code == supplier_code,
        Payable.source_type == source_type,
        Payable.po_code == (po_code or ""),
        Payable.invoice_no == invoice_no).all()


def delivery_invoice_date(db: Session, payables: list[Payable]) -> str:
    """Ngày hóa đơn gốc = tab_po_delivery.invoice_date hoặc POItem.invoice_date hoặc incur_date của đợt giao."""
    from app.modules.purchase_order.model import PODelivery, POItem
    for p in payables:
        if not p:
            continue
        if p.ref_type == "delivery" and p.ref_id:
            d = db.get(PODelivery, p.ref_id)
            if d:
                if (d.invoice_date or "").strip():
                    return d.invoice_date
                if d.po_item_id:
                    it = db.get(POItem, d.po_item_id)
                    if it and (it.invoice_date or "").strip():
                        return it.invoice_date
        # Có số hóa đơn mà chưa gõ ngày hóa đơn riêng -> mặc định lấy ngày phát sinh công nợ (ngày nhận hàng)
        if (p.invoice_no or "").strip() and (p.incur_date or "").strip():
            return p.incur_date
    return ""


def _remaining(p: Payable) -> float:
    return round(float(p.total or 0) - float(p.paid_amount or 0), 2)


def _line_rows(db: Session, data_lines, supplier_code: str, fill_from_payable: bool) -> list[dict]:
    """Chuẩn hóa dòng người dùng gửi lên thành các dòng sẽ ghi DB, đã gom nhóm.

    - `fill_from_payable=True` (lúc TẠO): ô nào bỏ trống thì lấy theo khoản nợ.
      Lúc SỬA thì KHÔNG lấy đè — người dùng có quyền xóa trắng số hóa đơn trên bản nháp.
    - Gom các dòng cùng (mã PO + số hóa đơn) thành 1 dòng như trước; dòng CHƯA có số hóa đơn
      thì để riêng, vì chưa biết chúng có thuộc cùng một hóa đơn hay không.
    """
    groups: dict[tuple, dict] = {}
    for idx, ln in enumerate(data_lines):
        p = db.get(Payable, ln.payable_id) if ln.payable_id else None
        if p and supplier_code and p.supplier_code != supplier_code:
            continue
        po_code = ((ln.po_code or "") or (p.po_code if p and fill_from_payable else "")).strip()
        invoice_no = ((ln.invoice_no or "") or (p.invoice_no if p and fill_from_payable else "")).strip()
        invoice_date = (ln.invoice_date or "").strip()
        if not invoice_date and p and fill_from_payable:
            invoice_date = delivery_invoice_date(db, [p])
        amt = float(ln.amount or 0)
        if amt <= 0 and p:
            amt = _remaining(p)

        key = (po_code, invoice_no) if invoice_no else (po_code, "", idx)
        row = groups.get(key)
        if row:
            row["amount"] = round(row["amount"] + amt, 2)
            row["invoice_date"] = row["invoice_date"] or invoice_date
        else:
            groups[key] = {"payable_id": p.id if p else 0, "po_code": po_code,
                           "invoice_no": invoice_no, "invoice_date": invoice_date,
                           "amount": round(amt, 2)}
    return list(groups.values())


def create_requests(db: Session, data: PRequestCreate, user_id: int) -> list[PaymentRequest]:
    """Tạo phiếu; nếu các khoản nợ thuộc nhiều NCC -> tách mỗi NCC 1 phiếu;
    Gom các khoản nợ cùng (mã PO + Số HĐ) thành 1 dòng duy nhất trên phiếu thanh toán.

    CR-066: KHÔNG còn chặn thiếu số hóa đơn ở đây — bản nháp được để trống để in trình ký,
    điều kiện đủ chỉ bị bắt lúc GỬI DUYỆT (xem `check_submit`)."""
    if not data.lines:
        raise HTTPException(400, "Chưa có dòng đề nghị thanh toán nào")

    # gom theo (supplier_code, source_type); dòng gõ tay (không gắn khoản nợ) lấy theo phần đầu phiếu
    groups: dict[tuple, list] = {}
    heads: dict[tuple, tuple] = {}     # (supplier_code, source_type) -> (supplier_name, company_id)
    manual: list = []
    for ln in data.lines:
        p = db.get(Payable, ln.payable_id) if ln.payable_id else None
        if not p:
            manual.append(ln)
            continue
        groups.setdefault((p.supplier_code, p.source_type), []).append(ln)
        heads.setdefault((p.supplier_code, p.source_type), (p.supplier_name, p.company_id))

    if manual:
        supplier_code = (data.supplier_code or "").strip()
        if not supplier_code:
            raise HTTPException(400, "Chưa chọn nhà cung cấp cho phiếu")
        source_type = data.source_type if data.source_type in ("goods", "shipping") else "goods"
        key = (supplier_code, source_type)
        groups.setdefault(key, []).extend(manual)
        if key not in heads:
            sup = db.query(Supplier).filter(Supplier.code == supplier_code).first()
            heads[key] = (sup.name if sup else supplier_code, data.company_id or 0)

    created = []
    for (supplier_code, source_type), items in groups.items():
        rows = _line_rows(db, items, supplier_code, fill_from_payable=True)
        if not rows:
            continue
        supplier_name, company_id = heads[(supplier_code, source_type)]
        req = PaymentRequest(
            supplier_code=supplier_code, supplier_name=supplier_name,
            company_id=company_id, source_type=source_type,
            request_date=data.request_date, note=data.note, status="draft",
            payment_method=norm_method(data.payment_method),
            prepay=1 if data.prepay else 0,
            total=round(sum(r["amount"] for r in rows), 2), created_by=user_id, updated_by=user_id)
        db.add(req)
        db.flush()
        req.code = f"YCTT{req.id:05d}"

        for r in rows:
            db.add(PaymentRequestLine(request_id=req.id, payable_id=r["payable_id"], po_code=r["po_code"],
                                      invoice_no=r["invoice_no"], invoice_date=r["invoice_date"],
                                      amount=r["amount"], created_by=user_id, updated_by=user_id))
        db.flush()
        created.append(req)
    if not created:
        raise HTTPException(400, "Không có dòng hợp lệ để tạo phiếu")
    db.commit()
    for req in created:
        record(db, user_id, ENTITY, req.id, "create")
    return created


# CR-066: duyệt xong là khóa số tiền / số hóa đơn — chặn ở BACKEND chứ không chỉ ẩn nút trên UI.
EDIT_LOCK_MSG = {
    "submitted": "Phiếu đang chờ duyệt, không sửa được — thu hồi (từ chối) rồi mới sửa",
    "approved": "Phiếu đã duyệt, không sửa được số tiền và số hóa đơn nữa",
    "paid": "Phiếu đã chi, không sửa được",
    "cancelled": "Phiếu đã bị từ chối, không sửa được",
}


def update_request(db: Session, rid: int, data: PRequestUpdate, user_id: int) -> PaymentRequest:
    req = get_request(db, rid)
    # CR-149: người dùng in phiếu SAU khi duyệt, nên câu chữ bản in phải sửa được ở
    # cả submitted/approved — nhưng chỉ khi payload KHÔNG đụng trường nào khác
    # (tiền, hóa đơn, hình thức... vẫn khóa cứng như CR-066). paid/cancelled khóa hẳn.
    fields = data.model_dump(exclude_unset=True)
    only_print_texts = set(fields) == {"print_texts"}
    if req.status != "draft" and not (only_print_texts and req.status in ("submitted", "approved")):
        raise HTTPException(400, EDIT_LOCK_MSG.get(req.status, "Phiếu không còn ở trạng thái nháp, không sửa được"))
    for k, v in data.model_dump(exclude_unset=True, exclude={"lines"}).items():
        if k == "payment_method":
            v = norm_method(v)
        elif k == "prepay":                 # CR-146: chỉ nhận 0/1
            v = 1 if v else 0
        elif k == "print_texts":            # CR-149: dict -> JSON đã lọc khóa + cắt độ dài
            v = norm_print_texts(v)
        setattr(req, k, v)
    if data.lines is not None:
        db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == rid).delete()
        rows = _line_rows(db, data.lines, req.supplier_code, fill_from_payable=False)
        for r in rows:
            db.add(PaymentRequestLine(request_id=rid, payable_id=r["payable_id"], po_code=r["po_code"],
                                      invoice_no=r["invoice_no"], invoice_date=r["invoice_date"],
                                      amount=r["amount"], created_by=user_id, updated_by=user_id))
        req.total = round(sum(r["amount"] for r in rows), 2)
    req.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, rid, "update")
    db.refresh(req)
    return req


def check_submit(db: Session, req: PaymentRequest) -> None:
    """CR-066 — điều kiện GỬI DUYỆT: mỗi dòng phải khớp một khoản công nợ CÒN NỢ.

    Bản nháp được để trống số hóa đơn (in ra trình ký, điền tay), nhưng đã trình duyệt chi thì
    phải có hóa đơn và phải trỏ đúng vào khoản nợ — nếu không, lúc ghi nhận chi tiền sẽ không
    trừ được vào đâu, công nợ treo và dòng ĐMH không bao giờ lên 'Hoàn thành'."""
    lines = lines_of(db, req.id)
    if not lines:
        raise HTTPException(400, "Phiếu chưa có dòng đề nghị nào")
    problems = []
    for i, ln in enumerate(lines, start=1):
        label = ln.po_code or f"dòng {i}"
        if not (ln.invoice_no or "").strip():
            problems.append(f"{label}: chưa có Số hóa đơn")
            continue
        pays = matching_payables(db, req.supplier_code, req.source_type, ln.po_code, ln.invoice_no)
        if not pays:
            problems.append(f"{label}: không có khoản công nợ nào khớp Số HĐ {ln.invoice_no} "
                            f"(sai số hóa đơn / mã PO, hoặc hàng chưa được ghi nhận nhận)")
        elif all(_remaining(p) <= 0.01 for p in pays):
            problems.append(f"{label}: khoản công nợ theo Số HĐ {ln.invoice_no} đã tất toán")
    if problems:
        raise HTTPException(400, "Chưa gửi duyệt được: " + "; ".join(problems))


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
    if status == "submitted":
        check_submit(db, req)
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
            matched_payables = matching_payables(db, req.supplier_code, req.source_type,
                                                 ln.po_code, ln.invoice_no)
            if not matched_payables and ln.payable_id:
                p_single = db.get(Payable, ln.payable_id)
                if p_single:
                    matched_payables = [p_single]

            def _pay(p, amt):
                p.paid_amount = round(float(p.paid_amount or 0) + amt, 2)
                recalc_status(p)
                if p.source_type == "goods" and p.ref_type == "delivery":
                    from app.modules.purchase_order.model import PODelivery
                    d = db.get(PODelivery, p.ref_id)
                    if d:
                        affected_po_ids.add(d.po_id)

            # Một hóa đơn có thể ứng với NHIỀU khoản nợ (mỗi lần giao 1 khoản). Chỉ trả vào
            # khoản CÒN NỢ — khoản đã tất toán phải bỏ qua, nếu không tiền dồn hết vào nó
            # (công nợ âm) còn khoản thật sự còn nợ vẫn treo, dòng ĐMH không bao giờ đủ
            # điều kiện vào `completed`.
            for p in matched_payables:
                if rem_to_pay <= 0:
                    break
                p_rem = max(0.0, float(p.total or 0) - float(p.paid_amount or 0))
                if p_rem <= 0:
                    continue
                pay_part = min(rem_to_pay, p_rem)
                _pay(p, pay_part)
                rem_to_pay = round(rem_to_pay - pay_part, 2)

            if rem_to_pay > 0 and matched_payables:
                # trả DƯ so với nợ (chi thêm, làm tròn...) -> ghi vào đúng khoản của dòng phiếu
                p = (db.get(Payable, ln.payable_id) if ln.payable_id else None) or matched_payables[-1]
                _pay(p, rem_to_pay)
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
