"""Tool CÔNG NỢ PHẢI TRẢ + soạn nháp Yêu cầu thanh toán (YCTT) — chỉ đọc, không ghi.

- `payable_lookup`: "công nợ NCC X tháng này bao nhiêu, còn lại bao nhiêu" — tra khoản nợ
  theo đúng phạm vi quyền `payable` của người hỏi (cùng `apply_scope` với màn Công nợ).
- `draft_payment_request`: "làm yêu cầu thanh toán cho tôi" — CHỌN các khoản nợ còn phải
  trả rồi trả bản đề xuất; giao diện hiện nút mở form tạo YCTT với các khoản đã tick sẵn
  (đi đúng đường `?payables=<ids>` của màn Công nợ), người dùng rà lại và tự bấm Lưu.
  Chỉ chọn khoản `remaining > 0`: bài học từ lỗi phân bổ thanh toán (fix 82ce6ad) — dồn
  tiền vào khoản đã tất toán là công nợ âm.
"""
from datetime import datetime

from sqlalchemy import case, func, or_

from app.core.scoping import apply_scope
from app.modules.payable.model import Payable
from app.modules.payable.service import ST_PAID, status_label

from .base import ToolContext, ToolSpec, denied
from .draft_tool import _clean_text

MAX_ROWS = 30          # trần dòng liệt kê của payable_lookup
MAX_DRAFT_LINES = 50   # trần khoản nợ đưa vào một bản nháp YCTT — nhiều hơn thì lập tay

_SOURCE_LABELS = {"goods": "Tiền hàng", "shipping": "Tiền vận chuyển"}


def _match_company(db, raw: str):
    """Khớp tên/tên tắt/mã công ty (không phân biệt hoa thường) với danh mục đang hoạt động.

    Trả (company, danh_sách_tên_hợp_lệ). Khác `_apply_company` của draft_tool: ở đây company
    là BỘ LỌC dữ liệu — khớp sai là lọc nhầm nợ của pháp nhân khác, nên không khớp thì phải
    chặn lại chứ không lặng lẽ bỏ qua.
    """
    from app.modules.company.model import Company

    rows = db.query(Company).filter(Company.is_active.is_(True)).all()
    q = raw.strip().lower()
    hit = next((c for c in rows
                if q in {(c.name or "").strip().lower(), (c.short_name or "").strip().lower(),
                         (c.code or "").strip().lower()}), None)
    return hit, sorted(c.name for c in rows if c.name)


def _scoped_payables(ctx: ToolContext, args: dict):
    """Query khoản nợ đã gác phạm vi + các bộ lọc chung của cả hai tool.

    Trả (query, company_hit, loi) — `loi` khác None nghĩa là tham số sai, trả thẳng cho model.
    """
    q = apply_scope(ctx.db.query(Payable), Payable, "payable", ctx.user, ctx.profile)

    company = _clean_text(args.get("company"), 255)
    company_hit = None
    if company:
        company_hit, matched_name = _match_company(ctx.db, company)
        if company_hit is None:
            return None, None, {"error": f"Không có công ty '{company}' trong danh mục — "
                                         "nêu danh sách hợp lệ (companies) để người dùng chọn.",
                                "companies": matched_name}
        q = q.filter(Payable.company_id == company_hit.id)

    supplier = _clean_text(args.get("supplier"), 255)
    if supplier:
        like = f"%{supplier}%"
        q = q.filter(or_(Payable.supplier_code.like(like), Payable.supplier_name.like(like)))

    date_from = _clean_text(args.get("date_from"), 10)
    if date_from:
        q = q.filter(Payable.incur_date != "", Payable.incur_date >= date_from)
    date_to = _clean_text(args.get("date_to"), 10)
    if date_to:
        q = q.filter(Payable.incur_date != "", Payable.incur_date <= date_to)
    return q, company_hit, None


def _payable_out(p: Payable) -> dict:
    return {
        "payable_id": p.id,
        "supplier_code": p.supplier_code,
        "supplier_name": p.supplier_name,
        "source_type": _SOURCE_LABELS.get(p.source_type, p.source_type),
        "po_code": p.po_code,
        "invoice_no": p.invoice_no,
        "incur_date": p.incur_date,
        "due_date": p.due_date,
        "total": float(p.total or 0),
        "paid_amount": float(p.paid_amount or 0),
        "remaining": float(p.remaining or 0),
        "status": status_label(p.status),
    }


# ── payable_lookup ──────────────────────────────────────────────────────────────────────

def _run_lookup(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("payable"):
        return denied("công nợ phải trả (payable)")

    q, _, error = _scoped_payables(ctx, args)
    if error:
        return error

    status = _clean_text(args.get("status"), 20) or "outstanding"
    if status == "outstanding":
        q = q.filter(Payable.status != ST_PAID)
    elif status == "paid":
        q = q.filter(Payable.status == ST_PAID)

    # Tổng hợp trên TOÀN BỘ kết quả lọc (không chỉ trang liệt kê) — câu "còn lại bao nhiêu"
    # trả lời bằng con số này. Quá hạn = còn nợ mà hạn trả đã qua (cùng công thức /summary).
    today = datetime.now().date().strftime("%Y-%m-%d")
    overdue = case(
        (((Payable.status != ST_PAID) & (Payable.due_date != "") & (Payable.due_date < today)),
         Payable.remaining),
        else_=0,
    )
    total = q.with_entities(
        func.count(Payable.id),
        func.coalesce(func.sum(Payable.total), 0),
        func.coalesce(func.sum(Payable.paid_amount), 0),
        func.coalesce(func.sum(Payable.remaining), 0),
        func.coalesce(func.sum(overdue), 0),
    ).one()

    limit = args.get("limit")
    limit = max(1, min(int(limit), MAX_ROWS)) if isinstance(limit, (int, float)) else 20
    rows = q.order_by(Payable.due_date.asc(), Payable.id.desc()).limit(limit).all()

    out = {
        "total": int(total[0]),
        "summary": {"total": float(total[1]), "paid": float(total[2]),
                    "remaining": float(total[3]), "overdue": float(total[4])},
        "items": [_payable_out(p) for p in rows],
    }
    if total[0] > limit:
        out["note"] = (f"Chỉ liệt kê {limit}/{total[0]} khoản tới hạn sớm nhất — summary vẫn "
                       "tính trên toàn bộ.")
    if not total[0]:
        out["note"] = ("Không có khoản nợ nào khớp điều kiện trong phạm vi người hỏi được "
                       "xem — nói thẳng, đừng bịa số.")
    return out


PAYABLE_LOOKUP_SPEC = ToolSpec(
    name="payable_lookup",
    description=(
        "Tra CÔNG NỢ PHẢI TRẢ cho nhà cung cấp (khoản nợ sinh ra khi nhận hàng) — dùng cho "
        "câu 'công nợ NCC X tháng này bao nhiêu', 'còn nợ NCC nào bao nhiêu tiền', 'khoản "
        "nào quá hạn chưa trả'. Kết quả có summary (tổng nợ / đã trả / CÒN LẠI / quá hạn) "
        "tính trên toàn bộ kết quả lọc, kèm từng khoản nợ với payable_id — muốn lập Yêu cầu "
        "thanh toán từ các khoản này thì gọi tiếp draft_payment_request và truyền đúng các "
        "payable_id đó. Mặc định chỉ lấy khoản CÒN PHẢI TRẢ."
    ),
    parameters={
        "type": "object",
        "properties": {
            "supplier": {
                "type": "string",
                "description": "Mã hoặc tên (một phần) nhà cung cấp để lọc. Bỏ trống = mọi NCC.",
            },
            "company": {
                "type": "string",
                "description": "Pháp nhân/công ty NỢ TIỀN — điền đúng tên/mã trong danh mục "
                               "khi người dùng nêu; bỏ trống = mọi công ty được xem.",
            },
            "status": {
                "type": "string",
                "enum": ["outstanding", "paid", "all"],
                "description": "outstanding = còn phải trả (mặc định) | paid = đã tất toán "
                               "| all = tất cả.",
            },
            "date_from": {"type": "string",
                          "description": "Ngày phát sinh nợ từ, YYYY-MM-DD (tùy chọn)."},
            "date_to": {"type": "string",
                        "description": "Ngày phát sinh nợ đến, YYYY-MM-DD (tùy chọn)."},
            "limit": {"type": "integer",
                      "description": f"Số khoản liệt kê tối đa, mặc định 20, trần {MAX_ROWS}."},
        },
    },
    handler=_run_lookup,
)


# ── draft_payment_request ───────────────────────────────────────────────────────────────

_DRAFT_DESC = (
    "SOẠN SẴN dữ liệu cho phiếu Yêu cầu thanh toán (YCTT) từ các khoản CÔNG NỢ CÒN PHẢI TRẢ. "
    "KHÔNG tạo phiếu — chỉ chọn khoản nợ và trả bản đề xuất; giao diện sẽ hiện nút mở form "
    "tạo YCTT với các khoản đã tick sẵn để người dùng rà lại và tự bấm Lưu. Gọi khi người "
    "dùng muốn lập yêu cầu/đề nghị thanh toán công nợ cho NCC. Cách chọn khoản nợ, ưu tiên "
    "theo thứ tự: (1) đã gọi payable_lookup trong hội thoại thì truyền đúng danh sách "
    "payable_ids người dùng muốn trả; (2) chưa tra thì truyền supplier (bắt buộc nếu không "
    "có payable_ids) + company/date_from/date_to nếu người dùng nêu — tool tự lấy các khoản "
    "còn phải trả khớp điều kiện. Khoản đã tất toán bị loại tự động. Sau khi gọi, báo người "
    "dùng bấm nút 'Tạo đề nghị thanh toán' dưới câu trả lời — nhấn mạnh phiếu CHƯA được tạo, "
    "số tiền đề nghị mặc định bằng số còn lại từng khoản và sửa được trên form."
)


def _run_draft(ctx: ToolContext, args: dict) -> dict:
    # Cần cả hai: quyền tạo YCTT (không có thì soạn hộ cũng vô ích) và quyền xem công nợ
    # (bản nháp lộ số nợ + tên NCC — không được vòng qua hàng rào của payable_lookup).
    if not ctx.can("payment_request", "create"):
        return {"denied": True,
                "error": "Người dùng không có quyền tạo Yêu cầu thanh toán "
                         "(payment_request.create)."}
    if not ctx.can("payable"):
        return {"denied": True,
                "error": "Người dùng không có quyền xem công nợ phải trả (payable) nên "
                         "không chọn được khoản nợ để lập phiếu."}

    raw_ids = args.get("payable_ids")
    ids = [int(x) for x in raw_ids if isinstance(x, (int, float))] if isinstance(raw_ids, list) else []
    if not ids and not _clean_text(args.get("supplier"), 255):
        return {"error": "Cần payable_ids (từ payable_lookup) hoặc tối thiểu supplier để "
                         "biết trả nợ cho NCC nào — hỏi người dùng rồi gọi lại."}

    q, _, error = _scoped_payables(ctx, args)
    if error:
        return error
    if ids:
        q = q.filter(Payable.id.in_(ids[:MAX_DRAFT_LINES]))
    # Chỉ khoản còn phải trả — tiền dồn vào khoản đã tất toán là công nợ âm (lỗi 82ce6ad).
    q = q.filter(Payable.status != ST_PAID, Payable.remaining > 0)

    total_matched = q.count()
    rows = q.order_by(Payable.due_date.asc(), Payable.id.desc()).limit(MAX_DRAFT_LINES).all()
    if not rows:
        return {"error": "Không có khoản nợ CÒN PHẢI TRẢ nào khớp điều kiện trong phạm vi "
                         "người hỏi được xem — nói thẳng với người dùng, đừng tự nới điều "
                         "kiện. Có thể gọi payable_lookup (status=all) để xem vì sao."}

    # Gom theo NCC để model tóm tắt — và vì backend tự TÁCH mỗi NCC một phiếu khi lưu.
    by_supplier: dict[str, dict] = {}
    for p in rows:
        g = by_supplier.setdefault(p.supplier_code or "?", {
            "supplier_code": p.supplier_code, "supplier_name": p.supplier_name,
            "lines": 0, "remaining": 0.0,
        })
        g["lines"] += 1
        g["remaining"] += float(p.remaining or 0)

    result = {
        "status": "ready",
        "draft": {
            #  `kind` để giao diện chat phân biệt với bản nháp YCBG/YCMH/nghỉ phép.
            "kind": "payment_request",
            "payable_ids": [p.id for p in rows],
            "suppliers": list(by_supplier.values()),
            "total_remaining": round(sum(float(p.remaining or 0) for p in rows), 2),
        },
        "total": len(rows),
        "reminder": "Phiếu CHƯA được tạo. Hãy tóm tắt các khoản nợ đã chọn (NCC, số khoản, "
                    "tổng còn lại) và mời người dùng bấm nút 'Tạo đề nghị thanh toán' dưới "
                    "câu trả lời — form mở ra đã tick sẵn các khoản này, số tiền đề nghị "
                    "mặc định bằng số CÒN LẠI từng khoản, sửa được trước khi Lưu.",
    }
    if ids:
        missing = sorted(set(ids) - {p.id for p in rows})
        if missing:
            result["skipped_ids"] = missing
            result["reminder"] += (" Một số payable_id bị loại (đã tất toán, ngoài phạm vi "
                                   "được xem hoặc không tồn tại) — nói rõ cho người dùng.")
    elif total_matched > len(rows):
        result["reminder"] += (f" Chỉ đưa vào {len(rows)}/{total_matched} khoản tới hạn sớm "
                               "nhất — phần còn lại người dùng tự tick thêm trên màn Công nợ.")
    if len(by_supplier) > 1:
        result["reminder"] += (" Các khoản thuộc NHIỀU nhà cung cấp — khi lưu hệ thống tự "
                               "tách mỗi NCC một phiếu, báo trước cho người dùng.")
    return result


# ── payment_request_read ────────────────────────────────────────────────────────────────

_PM_LABELS = {"transfer": "Chuyển khoản", "cash": "Tiền mặt"}


def _run_read_request(ctx: ToolContext, args: dict) -> dict:
    """Recap MỘT phiếu Yêu cầu thanh toán theo mã — cùng khuôn với procurement_doc_read."""
    if not ctx.can("payment_request"):
        return denied("Yêu cầu thanh toán (payment_request)")

    code = _clean_text(args.get("code"), 50).upper()
    if not code:
        return {"error": "Thiếu code — hỏi người dùng mã phiếu YCTT cần xem."}

    from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
    from app.modules.payment_request.service import parse_print_texts

    from .procurement_doc_tool import _label

    req = (apply_scope(ctx.db.query(PaymentRequest), PaymentRequest, "payment_request",
                       ctx.user, ctx.profile)
           .filter(PaymentRequest.code == code).first())
    if req is None:
        return {"error": f"Không tìm thấy phiếu {code} trong phạm vi dữ liệu người hỏi "
                         "được xem — nói thẳng, đừng bịa."}

    lines = (ctx.db.query(PaymentRequestLine)
             .filter(PaymentRequestLine.request_id == req.id)
             .order_by(PaymentRequestLine.id.asc()).all())
    return {
        "code": req.code,
        "status": req.status,
        "status_label": _label("payment_request", req.status),
        "supplier_code": req.supplier_code,
        "supplier_name": req.supplier_name,
        "source_type": _SOURCE_LABELS.get(req.source_type, req.source_type),
        "request_date": req.request_date,
        "payment_method": _PM_LABELS.get(req.payment_method, req.payment_method),
        "prepay": bool(req.prepay),
        "total": float(req.total or 0),
        "note": req.note,
        "reject_reason": req.reject_reason,
        "print_texts": parse_print_texts(req.print_texts),
        "lines": [{
            "po_code": ln.po_code,
            "invoice_no": ln.invoice_no,
            "invoice_date": ln.invoice_date,
            "amount": float(ln.amount or 0),
        } for ln in lines],
        "url": f"/finance/payment-requests/{req.id}",
        "total_lines": len(lines),
    }


PAYMENT_REQUEST_READ_SPEC = ToolSpec(
    name="payment_request_read",
    description=(
        "Xem chi tiết MỘT phiếu Yêu cầu thanh toán (YCTT) theo mã phiếu — trạng thái, NCC, "
        "hình thức thanh toán, tổng tiền, các dòng đề nghị chi (mã ĐMH, số hóa đơn, số "
        "tiền) và 3 câu chữ bản in (print_texts). Gọi khi người dùng hỏi về một YCTT cụ "
        "thể ('YCTT00045 tới đâu rồi', 'phiếu thanh toán đó bao nhiêu tiền'). Khi trả "
        "lời, kèm `url` dạng link để người dùng bấm mở phiếu. Trợ lý KHÔNG duyệt/chi hộ "
        "được — việc đó người dùng tự làm trên màn chi tiết."
    ),
    parameters={
        "type": "object",
        "properties": {
            "code": {"type": "string",
                     "description": "Mã phiếu YCTT, ví dụ YCTT00045 — bắt buộc."},
        },
        "required": ["code"],
    },
    handler=_run_read_request,
)


DRAFT_PAYMENT_REQUEST_SPEC = ToolSpec(
    name="draft_payment_request",
    description=_DRAFT_DESC,
    parameters={
        "type": "object",
        "properties": {
            "payable_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Danh sách payable_id lấy từ kết quả payable_lookup — cách "
                               "chính xác nhất, ưu tiên dùng khi đã tra công nợ trong hội thoại.",
            },
            "supplier": {
                "type": "string",
                "description": "Mã hoặc tên (một phần) NCC cần thanh toán — bắt buộc khi "
                               "không truyền payable_ids.",
            },
            "company": {
                "type": "string",
                "description": "Pháp nhân/công ty nợ tiền — điền đúng tên/mã trong danh mục "
                               "khi người dùng nêu; bỏ trống = mọi công ty được xem.",
            },
            "date_from": {"type": "string",
                          "description": "Chỉ lấy khoản phát sinh từ ngày, YYYY-MM-DD (tùy chọn)."},
            "date_to": {"type": "string",
                        "description": "Chỉ lấy khoản phát sinh đến ngày, YYYY-MM-DD (tùy chọn)."},
        },
    },
    handler=_run_draft,
)
