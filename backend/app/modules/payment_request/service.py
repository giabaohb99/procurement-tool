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
        offset = max(0.0, float(ln.offset_amount or 0))
        # CR-260: dòng có phần cấn trừ thì số chi thêm là CHỦ ĐÍCH (kể cả 0 đồng khi
        # treo phủ hết nợ) — không được tự điền lại bằng nợ còn lại như dòng thường.
        if amt <= 0 and p and offset <= 0:
            amt = _remaining(p)

        key = (po_code, invoice_no) if invoice_no else (po_code, "", idx)
        row = groups.get(key)
        if row:
            row["amount"] = round(row["amount"] + amt, 2)
            row["offset_amount"] = round(row["offset_amount"] + offset, 2)
            row["invoice_date"] = row["invoice_date"] or invoice_date
        else:
            groups[key] = {"payable_id": p.id if p else 0, "po_code": po_code,
                           "invoice_no": invoice_no, "invoice_date": invoice_date,
                           "amount": round(amt, 2), "offset_amount": round(offset, 2)}
    return list(groups.values())


def create_requests(db: Session, data: PRequestCreate, user_id: int) -> list[PaymentRequest]:
    """Tạo phiếu; các khoản nợ thuộc nhiều NCC hoặc nhiều CÔNG TY nhận hóa đơn -> tách
    mỗi cặp (NCC, công ty) 1 phiếu (bao-CR-274 — trước đây chỉ tách theo NCC, company_id
    lấy theo khoản nợ đầu tiên nên nợ 2 pháp nhân bị gom chung và phiếu đóng dấu nhầm
    công ty). Gom các khoản nợ cùng (mã PO + Số HĐ) thành 1 dòng duy nhất trên phiếu.

    CR-066: KHÔNG còn chặn thiếu số hóa đơn ở đây — bản nháp được để trống để in trình ký,
    điều kiện đủ chỉ bị bắt lúc GỬI DUYỆT (xem `check_submit`)."""
    if not data.lines:
        raise HTTPException(400, "Chưa có dòng đề nghị thanh toán nào")

    # gom theo (supplier_code, source_type, company_id); dòng gõ tay (không gắn khoản nợ)
    # lấy theo phần đầu phiếu
    groups: dict[tuple, list] = {}
    heads: dict[tuple, str] = {}     # key -> supplier_name
    manual: list = []
    for ln in data.lines:
        p = db.get(Payable, ln.payable_id) if ln.payable_id else None
        if not p:
            manual.append(ln)
            continue
        key = (p.supplier_code, p.source_type, p.company_id or 0)
        groups.setdefault(key, []).append(ln)
        heads.setdefault(key, p.supplier_name)

    if manual:
        supplier_code = (data.supplier_code or "").strip()
        if not supplier_code:
            raise HTTPException(400, "Chưa chọn nhà cung cấp cho phiếu")
        source_type = data.source_type if data.source_type in ("goods", "shipping") else "goods"
        # Form không chọn công ty mà các khoản nợ kèm theo đều thuộc MỘT công ty thì dòng
        # gõ tay đi chung phiếu đó (đúng hành vi cũ); nhiều công ty thì đứng phiếu riêng.
        pay_companies = {k[2] for k in groups}
        company_id = data.company_id or (pay_companies.pop() if len(pay_companies) == 1 else 0)
        key = (supplier_code, source_type, company_id)
        groups.setdefault(key, []).extend(manual)
        if key not in heads:
            sup = db.query(Supplier).filter(Supplier.code == supplier_code).first()
            heads[key] = sup.name if sup else supplier_code

    created = []
    for (supplier_code, source_type, company_id), items in groups.items():
        rows = _line_rows(db, items, supplier_code, fill_from_payable=True)
        if not rows:
            continue
        supplier_name = heads[(supplier_code, source_type, company_id)]
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
                                      amount=r["amount"], offset_amount=r["offset_amount"],
                                      created_by=user_id, updated_by=user_id))
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
                                      amount=r["amount"], offset_amount=r["offset_amount"],
                                      created_by=user_id, updated_by=user_id))
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
    trừ được vào đâu, công nợ treo và dòng ĐMH không bao giờ lên 'Hoàn thành'.

    CR-268 — NGOẠI LỆ phiếu THANH TOÁN TRƯỚC (prepay=1): chưa có công nợ để khớp là
    đúng bản chất (chi trước khi nhận hàng / tạm ứng NCC), nên miễn điều kiện khớp.
    Tiền chi ra thành TIỀN TREO, đối trừ sau (xem apply_prepay_offsets / offset_supplier_hanging)."""
    lines = lines_of(db, req.id)
    if not lines:
        raise HTTPException(400, "Phiếu chưa có dòng đề nghị nào")
    offset_total = round(sum(float(ln.offset_amount or 0) for ln in lines), 2)
    if req.prepay:
        # CR-260: phiếu TRẢ TRƯỚC là phiếu SINH ra tiền treo — không có chuyện nó
        # lại cấn trừ tiền treo; lọt cả hai là vòng tiền tự nuốt đuôi.
        if offset_total > 0.01:
            raise HTTPException(400, "Phiếu trả trước không có phần cấn trừ tiền treo — "
                                     "bỏ phần cấn trừ hoặc bỏ tick 'Thanh toán trước'")
        bad = [str(i) for i, ln in enumerate(lines, start=1) if float(ln.amount or 0) <= 0]
        if bad:
            raise HTTPException(400, "Phiếu trả trước có dòng số tiền không dương: dòng " + ", ".join(bad))
        return
    # CR-260 — soát SƠ BỘ phần cấn trừ ngay lúc gửi duyệt cho người lập biết sớm;
    # soát CHẶT (kèm thực thi) nằm ở lúc DUYỆT — apply_line_offsets.
    if offset_total > 0.01:
        treo = get_hanging_lines(db, req.supplier_code, req.source_type, "")
        available = round(sum(line_hanging(t) for _r, t in treo), 2)
        if available + 0.01 < offset_total:
            raise HTTPException(400, f"Phần cấn trừ trên phiếu ({offset_total:,.0f} đ) vượt tiền treo "
                                     f"còn lại của NCC ({available:,.0f} đ) — sửa lại phiếu trước khi gửi duyệt")
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
    affected_po_ids: set[int] = set()
    # CR-260 — phần cấn trừ tiền treo ghi trên dòng phiếu THỰC THI đúng lúc DUYỆT
    # (trước đó chỉ là ý định, nháp sửa/xóa vô hại). Soát fail thì raise ngay tại
    # đây -> chưa commit gì, phiếu vẫn ở Chờ duyệt.
    offset_applied = apply_line_offsets(db, req, user_id, affected_po_ids) if status == "approved" else 0.0
    req.status = status
    req.updated_by = user_id
    if status == "cancelled":
        req.reject_reason = reason
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
                rem_to_pay = 0.0

            # CR-268 — ghi lại phần đã trừ được vào công nợ ngay lúc chi. Phiếu trả trước
            # chưa có công nợ thì rem_to_pay còn nguyên -> allocated = 0, toàn bộ số tiền
            # thành TIỀN TREO chờ đối trừ (apply_prepay_offsets lúc nhận hàng, hoặc kế toán
            # bấm tay). Phiếu trả trước chi SAU khi đã nhận hàng thì khớp nợ bình thường ở
            # trên -> allocated = đủ, không sinh treo ảo.
            ln.allocated_amount = round(float(ln.amount or 0) - rem_to_pay, 2)
    db.commit()
    record(db, user_id, ENTITY, rid, status, reason)
    if offset_applied > 0.01:
        record(db, user_id, ENTITY, rid, "update",
               f"Cấn trừ {offset_applied:,.0f} đ tiền treo trả trước vào công nợ khi duyệt (CR-260)")
    # Cấn trừ lúc DUYỆT cũng có thể tất toán khoản nợ -> dòng ĐMH đủ điều kiện
    # tiến trạng thái, nên chạy auto-progress cho cả approved lẫn paid.
    if affected_po_ids:
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


# ============================== CR-268 — TIỀN TREO ==============================
# Phiếu THANH TOÁN TRƯỚC (prepay=1) chi tiền khi CHƯA có công nợ -> số đã chi "treo"
# lại chờ đối trừ. Hai loại treo, phân biệt bằng po_code trên DÒNG phiếu:
#   - Treo GẮN ĐƠN  (po_code = "POxxxxx"): tự động đối trừ vào công nợ HÀNG của đúng
#     đơn đó ngay khi nhận hàng sinh nợ (apply_prepay_offsets, gọi từ recompute_effects).
#   - Treo CẤP NCC  (po_code = ""): KHÔNG tự trừ — ngoài đời có hai đường: (A) cấn trừ
#     vào một đơn sau (kế toán bấm offset_supplier_hanging), hoặc (B) trả full đơn sau
#     rồi NCC hoàn cọc (kế toán ghi record_refund). Máy không đoán được ý người.
# Bất biến CỨNG: mọi lần đối trừ <= min(treo còn lại, nợ còn lại) — không bao giờ đẩy
# công nợ âm (vết xe payment-allocation-bug 82ce6ad).


def line_hanging(ln: PaymentRequestLine) -> float:
    """Tiền treo còn lại của 1 dòng = đã chi - đã đối trừ - NCC đã hoàn."""
    return round(float(ln.amount or 0) - float(ln.allocated_amount or 0)
                 - float(ln.refunded_amount or 0), 2)


def get_hanging_lines(db: Session, supplier_code: str, source_type: str = "goods",
                      po_code: str | None = None) -> list[tuple[PaymentRequest, PaymentRequestLine]]:
    """Các dòng còn TIỀN TREO của 1 NCC: dòng thuộc phiếu prepay=1 ĐÃ CHI, chưa trừ hết.

    po_code=None -> mọi dòng; po_code="" -> chỉ treo CẤP NCC (không gắn đơn);
    po_code="POxxxxx" -> chỉ treo gắn đúng đơn đó. Trả về theo phiếu CŨ trước (FIFO)."""
    if not supplier_code:
        return []
    q = (db.query(PaymentRequest, PaymentRequestLine)
         .join(PaymentRequestLine, PaymentRequestLine.request_id == PaymentRequest.id)
         .filter(PaymentRequest.status == "paid",
                 PaymentRequest.prepay == 1,
                 PaymentRequest.supplier_code == supplier_code,
                 PaymentRequest.source_type == source_type))
    if po_code is not None:
        q = q.filter(PaymentRequestLine.po_code == (po_code or ""))
    rows = q.order_by(PaymentRequest.id.asc(), PaymentRequestLine.id.asc()).all()
    return [(req, ln) for req, ln in rows if line_hanging(ln) > 0.01]


def summarize_hanging(db: Session, supplier_code: str, source_type: str = "goods",
                      po_code: str | None = None) -> dict:
    """Gói dữ liệu tiền treo cho API/AI: tổng còn treo + từng dòng kèm số đã trừ/đã hoàn."""
    rows = get_hanging_lines(db, supplier_code, source_type, po_code)
    items = [{
        "request_id": req.id, "request_code": req.code, "request_date": req.request_date,
        "line_id": ln.id, "po_code": ln.po_code,
        "amount": float(ln.amount or 0),
        "allocated_amount": float(ln.allocated_amount or 0),
        "refunded_amount": float(ln.refunded_amount or 0),
        "hanging": line_hanging(ln),
    } for req, ln in rows]
    return {"total": round(sum(it["hanging"] for it in items), 2), "items": items}


def apply_prepay_offsets(db: Session, po_code: str, supplier_code: str, user_id: int) -> float:
    """TỰ ĐỘNG đối trừ tiền treo GẮN ĐƠN vào công nợ HÀNG của đúng đơn đó.

    Gọi từ purchase_order.service.recompute_effects (sau khi upsert công nợ, trước khi
    tính tiến độ dòng — is_line_paid đọc paid_amount). CHỈ flush, KHÔNG commit, KHÔNG
    record() (audit commit session, gọi ở đây là hỏng transaction đang dở).

    Idempotent: chạy lại không trừ thêm vì treo đã giảm tương ứng. Trả về tổng đã trừ."""
    if not po_code or not supplier_code:
        return 0.0
    treo = get_hanging_lines(db, supplier_code, "goods", po_code)
    if not treo:
        return 0.0
    payables = (db.query(Payable)
                .filter(Payable.supplier_code == supplier_code,
                        Payable.source_type == "goods",
                        Payable.po_code == po_code)
                .order_by(Payable.id.asc()).all())
    total_applied = 0.0
    for p in payables:
        p_rem = _remaining(p)
        if p_rem <= 0.01:
            continue
        touched = False
        for _req, ln in treo:
            hang = line_hanging(ln)
            if hang <= 0.01:
                continue
            part = round(min(hang, p_rem), 2)          # trần cứng min(treo, nợ)
            p.paid_amount = round(float(p.paid_amount or 0) + part, 2)
            ln.allocated_amount = round(float(ln.allocated_amount or 0) + part, 2)
            ln.updated_by = user_id
            p_rem = round(p_rem - part, 2)
            total_applied = round(total_applied + part, 2)
            touched = True
            if p_rem <= 0.01:
                break
        if touched:
            recalc_status(p)
    if total_applied:
        db.flush()
    return total_applied


def offset_supplier_hanging(db: Session, payable: Payable, amount: float, user_id: int) -> float:
    """Kế toán BẤM TAY cấn trừ tiền treo CẤP NCC (không gắn đơn) vào 1 khoản công nợ.

    amount <= 0 nghĩa là "trừ tối đa". Trần cứng: min(treo còn lại, nợ còn lại, số yêu cầu).
    Ăn treo theo phiếu CŨ trước. Hàm này COMMIT + ghi audit (gọi từ endpoint)."""
    p_rem = _remaining(payable)
    if p_rem <= 0.01:
        raise HTTPException(400, "Khoản công nợ này đã tất toán, không còn gì để cấn trừ")
    treo = get_hanging_lines(db, payable.supplier_code, payable.source_type, "")
    available = round(sum(line_hanging(ln) for _r, ln in treo), 2)
    if available <= 0.01:
        raise HTTPException(400, "NCC này không còn tiền treo (không gắn đơn) để cấn trừ")
    want = float(amount or 0)
    take = round(min(p_rem, available) if want <= 0 else min(want, p_rem, available), 2)
    rem = take
    for _req, ln in treo:
        if rem <= 0.01:
            break
        part = round(min(line_hanging(ln), rem), 2)
        if part <= 0:
            continue
        ln.allocated_amount = round(float(ln.allocated_amount or 0) + part, 2)
        ln.updated_by = user_id
        rem = round(rem - part, 2)
    payable.paid_amount = round(float(payable.paid_amount or 0) + take, 2)
    recalc_status(payable)
    db.commit()
    record(db, user_id, "payable", payable.id, "update",
           f"Cấn trừ {take:,.0f} đ tiền treo trả trước của NCC {payable.supplier_code} (CR-268)")
    return take


def apply_line_offsets(db: Session, req: PaymentRequest, user_id: int,
                       affected_po_ids: set[int]) -> float:
    """CR-260 — THỰC THI phần cấn trừ tiền treo ghi trên dòng phiếu, gọi đúng lúc DUYỆT.

    Lúc lập phiếu `offset_amount` chỉ là Ý ĐỊNH (thu mua bấm ở hộp thoại ĐMH, hoặc
    kế toán sửa trên bản nháp) — công nợ chưa bị đụng, xóa nháp là hết chuyện. Người
    DUYỆT nhìn thấy phần cấn trừ trên phiếu rồi mới gật, nên thực thi đặt ở đây.

    Soát CHẶT trước khi trừ, thiếu là CHẶN DUYỆT với thông báo rõ (không tự đổi số):
    - treo cấp NCC còn lại >= tổng cấn trừ (đơn khác có thể đã dùng trong lúc chờ duyệt);
    - khoản nợ của từng dòng còn nợ >= phần cấn trừ của dòng (nợ có thể đã được trả bớt).
    Trần cứng min(treo, nợ) giữ nguyên như CR-268 — không bao giờ đẩy công nợ âm.
    Chỉ flush, KHÔNG commit (chạy trong transaction của set_status); fail -> raise
    trước commit nên không có nửa vời."""
    lines = [ln for ln in lines_of(db, req.id) if float(ln.offset_amount or 0) > 0.01]
    if not lines:
        return 0.0
    if req.prepay:
        raise HTTPException(400, "Phiếu trả trước không có phần cấn trừ tiền treo — từ chối để người lập sửa")

    treo = get_hanging_lines(db, req.supplier_code, req.source_type, "")
    need = round(sum(float(ln.offset_amount or 0) for ln in lines), 2)
    available = round(sum(line_hanging(t) for _r, t in treo), 2)
    if available + 0.01 < need:
        raise HTTPException(400, f"Không duyệt được: phần cấn trừ trên phiếu ({need:,.0f} đ) vượt tiền treo "
                                 f"còn lại của NCC ({available:,.0f} đ) — tiền treo có thể đã dùng cho phiếu/đơn "
                                 "khác trong lúc chờ duyệt. Từ chối phiếu để người lập sửa lại phần cấn trừ.")

    # Gom sẵn khoản nợ đích của từng dòng + soát đủ nợ TRƯỚC khi trừ đồng nào.
    line_targets: list[tuple[PaymentRequestLine, list[Payable], float]] = []
    for i, ln in enumerate(lines, start=1):
        want = round(float(ln.offset_amount or 0), 2)
        pays = matching_payables(db, req.supplier_code, req.source_type, ln.po_code, ln.invoice_no)
        if not pays and ln.payable_id:
            p_single = db.get(Payable, ln.payable_id)
            pays = [p_single] if p_single else []
        label = ln.po_code or ln.invoice_no or f"dòng {i}"
        if not pays:
            raise HTTPException(400, f"Không duyệt được: {label} chưa khớp khoản công nợ nào để cấn trừ")
        rem_debt = round(sum(_remaining(p) for p in pays), 2)
        if rem_debt + 0.01 < want:
            raise HTTPException(400, f"Không duyệt được: {label} chỉ còn nợ {rem_debt:,.0f} đ, nhỏ hơn phần "
                                     f"cấn trừ {want:,.0f} đ (khoản nợ đã được trả/cấn bớt nơi khác) — "
                                     "từ chối phiếu để người lập sửa lại.")
        line_targets.append((ln, pays, want))

    total_applied = 0.0
    for ln, pays, want in line_targets:
        rem = want
        for p in pays:
            if rem <= 0.01:
                break
            p_rem = _remaining(p)
            if p_rem <= 0.01:
                continue
            part = round(min(rem, p_rem), 2)
            for _r, t in treo:                      # ăn treo theo phiếu CŨ trước (FIFO)
                if part <= 0.01:
                    break
                bite = round(min(line_hanging(t), part), 2)
                if bite <= 0:
                    continue
                t.allocated_amount = round(float(t.allocated_amount or 0) + bite, 2)
                t.updated_by = user_id
                p.paid_amount = round(float(p.paid_amount or 0) + bite, 2)
                part = round(part - bite, 2)
                rem = round(rem - bite, 2)
                total_applied = round(total_applied + bite, 2)
            recalc_status(p)
            if p.source_type == "goods" and p.ref_type == "delivery":
                from app.modules.purchase_order.model import PODelivery
                d = db.get(PODelivery, p.ref_id)
                if d:
                    affected_po_ids.add(d.po_id)
        # Hai dòng cùng trỏ một khoản nợ có thể qua được vòng soát từng-dòng ở trên
        # nhưng cộng lại vẫn vượt nợ — bắt nốt ở đây, tuyệt đối không nửa vời.
        if rem > 0.01:
            raise HTTPException(400, "Không duyệt được: các dòng cấn trừ cộng lại vượt nợ còn lại "
                                     "của cùng một khoản công nợ — từ chối phiếu để người lập sửa lại.")
    db.flush()
    return total_applied


def check_line_offsets(db: Session, req: PaymentRequest) -> list[str]:
    """CR-260 — soát KHÔ phần cấn trừ trên phiếu: cùng bộ luật với apply_line_offsets
    lúc DUYỆT nhưng không trừ đồng nào, không đụng DB. Trả danh sách vướng mắc, rỗng =
    hiện tại bấm Duyệt sẽ qua vòng soát cấn trừ.

    Dùng cho trợ lý AI trả lời "phiếu này duyệt được chưa / vì sao bị chặn". Kết quả
    chỉ đúng TẠI THỜI ĐIỂM soát — treo/nợ vẫn có thể bị phiếu/đơn khác dùng trước khi
    duyệt thật, nên đây là chẩn đoán chứ không phải cam kết."""
    lines = [ln for ln in lines_of(db, req.id) if float(ln.offset_amount or 0) > 0.01]
    if not lines:
        return []
    if req.prepay:
        return ["Phiếu trả trước không được có phần cấn trừ tiền treo — bỏ phần cấn trừ "
                "hoặc bỏ tick 'Thanh toán trước'"]
    problems: list[str] = []
    treo = get_hanging_lines(db, req.supplier_code, req.source_type, "")
    need = round(sum(float(ln.offset_amount or 0) for ln in lines), 2)
    available = round(sum(line_hanging(t) for _r, t in treo), 2)
    if available + 0.01 < need:
        problems.append(f"Tổng cấn trừ trên phiếu ({need:,.0f} đ) vượt tiền treo còn lại "
                        f"của NCC ({available:,.0f} đ)")
    # Trừ MÔ PHỎNG trên bản sao nợ còn lại — bắt được cả trường hợp hai dòng cùng trỏ
    # một khoản nợ mà cộng lại vượt nợ (vòng chốt cuối của apply_line_offsets).
    sim_remaining: dict[int, float] = {}
    for i, ln in enumerate(lines, start=1):
        want = round(float(ln.offset_amount or 0), 2)
        pays = matching_payables(db, req.supplier_code, req.source_type, ln.po_code, ln.invoice_no)
        if not pays and ln.payable_id:
            p_single = db.get(Payable, ln.payable_id)
            pays = [p_single] if p_single else []
        label = ln.po_code or ln.invoice_no or f"dòng {i}"
        if not pays:
            problems.append(f"{label}: chưa khớp khoản công nợ nào để cấn trừ")
            continue
        for p in pays:
            sim_remaining.setdefault(p.id, _remaining(p))
        rem = want
        for p in pays:
            if rem <= 0.01:
                break
            part = round(min(rem, sim_remaining[p.id]), 2)
            if part <= 0:
                continue
            sim_remaining[p.id] = round(sim_remaining[p.id] - part, 2)
            rem = round(rem - part, 2)
        if rem > 0.01:
            problems.append(f"{label}: nợ còn lại nhỏ hơn phần cấn trừ {want:,.0f} đ "
                            "(khoản nợ đã được trả/cấn bớt nơi khác, hoặc trùng khoản nợ "
                            "với dòng khác trên phiếu)")
    return problems


def record_refund(db: Session, rid: int, amount: float, note: str, user_id: int) -> float:
    """Ghi nhận NCC HOÀN TIỀN cho phiếu trả trước (đường B: trả full đơn sau, NCC trả cọc).

    Chỉ áp cho phiếu prepay=1 ĐÃ CHI còn treo. amount <= 0 nghĩa là hoàn toàn bộ phần treo.
    Trần cứng: không vượt tiền treo còn lại. Hàm này COMMIT + ghi audit."""
    req = get_request(db, rid)
    if req.status != "paid" or not req.prepay:
        raise HTTPException(400, "Chỉ ghi nhận hoàn tiền trên phiếu THANH TOÁN TRƯỚC đã chi")
    lines = [ln for ln in lines_of(db, rid) if line_hanging(ln) > 0.01]
    available = round(sum(line_hanging(ln) for ln in lines), 2)
    if available <= 0.01:
        raise HTTPException(400, "Phiếu này không còn tiền treo để ghi nhận hoàn")
    take = float(amount or 0)
    if take <= 0:
        take = available
    if take > available + 0.01:
        raise HTTPException(400, f"Số hoàn ({take:,.0f}) vượt tiền treo còn lại ({available:,.0f})")
    take = round(take, 2)
    rem = take
    for ln in lines:
        if rem <= 0.01:
            break
        part = round(min(line_hanging(ln), rem), 2)
        ln.refunded_amount = round(float(ln.refunded_amount or 0) + part, 2)
        ln.updated_by = user_id
        rem = round(rem - part, 2)
    req.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, rid, "update",
           f"NCC hoàn lại {take:,.0f} đ tiền trả trước" + (f" — {note}" if (note or "").strip() else ""))
    return take
