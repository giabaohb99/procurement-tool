"""Tool RECAP CHỨNG TỪ THU MUA + PHIẾU CHỜ DUYỆT cho Trợ lý AI — chỉ đọc, không ghi.

- `procurement_doc_read`: recap MỘT chứng từ theo mã/id (ĐMH / YCMH / YCKS) — đầu phiếu,
  dòng hàng, tiến độ giao nhận, công nợ phát sinh (ĐMH). Trả lời "đơn PO00123 tới đâu rồi",
  "ai mua, mua gì, giá bao nhiêu". Một tool GENERIC cho cả ba loại, không đẻ tool theo màn.
- `pending_procurement_approvals`: đếm + liệt kê phiếu thu mua ĐANG CHỜ DUYỆT (`submitted`)
  mà chính người hỏi CÓ QUYỀN duyệt và NHÌN THẤY trong phạm vi dữ liệu. Trả lời "tôi cần
  duyệt bao nhiêu phiếu khảo sát". Khác `my_approval_tasks`: tool kia đọc BỘ MÁY PHÊ DUYỆT
  (hiện chỉ Văn bản chạy); chứng từ thu mua duyệt bằng nút trạng thái trên từng màn nên phải
  đếm thẳng theo cột `status`.

Nguyên tắc cứng: trợ lý KHÔNG duyệt hộ. Mọi kết quả chỉ kèm `url` mở màn chi tiết —
con người tự bấm Duyệt ở đó (giữ đúng thuyết chỉ-đọc của tài liệu 04).

Gác quyền y các tool cũ: `ctx.can(entity)` (+`approve` với tool chờ duyệt) + `apply_scope`;
thiếu `supplier.read` thì ẩn tên/mã NCC kèm ghi chú, thiếu `payable.read` thì recap ĐMH
không kèm khối công nợ.
"""
from sqlalchemy import case, func, or_

from app.core.scoping import apply_scope
from app.core.status_codes import (PO_DOCUMENT_STATUS, PO_ITEM_LINE_STATUS,
                                   PO_PROGRESS_STATUS, PR_LINE_STATUS)
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.survey.model import Survey
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption)

#  Một nguồn đường dẫn chi tiết duy nhất cho cả gói tool — xem chú thích tại chỗ khai báo.
from .approval_tool import _duong_dan
from .base import ToolContext, ToolSpec, denied

MAX_LINES = 30        # trần số dòng hàng trả về trong một recap
MAX_ROWS = 30         # trần số phiếu liệt kê mỗi loại ở tool chờ duyệt

_ENTITY_LABELS = {
    "purchase_order": "Đơn mua hàng (ĐMH)",
    "purchase_request": "Yêu cầu mua hàng (YCMH)",
    "survey_request": "Yêu cầu báo giá (YCKS)",
    "survey": "Phiếu khảo sát",
    "payment_request": "Yêu cầu thanh toán (YCTT)",
}

#  Nhãn trạng thái ĐẦU PHIẾU — chép ĐÚNG chữ từ frontend-v2 (`purchase-document.ts`,
#  `payment-request.ts`) để chat và màn hình nói cùng một chữ. Các cột này là mã chuỗi
#  QĐ-9, KHÔNG có trong `status_codes.py` nên không tra bộ mã được.
_STATUS_LABELS: dict[str, dict[str, str]] = {
    "purchase_request": {
        "draft": "Nháp", "submitted": "Chờ duyệt", "approved": "Đã duyệt",
        "dispatched": "Đã điều phối", "rejected": "Bị trả lại", "cancelled": "Đã từ chối",
        "processing": "Đang xử lý", "completed": "Hoàn thành",
    },
    "survey_request": {
        "draft": "Nháp", "submitted": "Chờ duyệt", "approved": "Đã duyệt",
        "processing": "Đang xử lý", "survey_done": "Đã khảo sát", "pr_created": "Đã tạo YCMH",
        "done": "Hoàn thành", "rejected": "Bị trả lại", "cancelled": "Đã từ chối",
    },
    "purchase_order": {
        "draft": "Nháp", "submitted": "Chờ duyệt", "approved": "Đã duyệt",
        "partial": "Đã nhận một phần", "received": "Đã nhận đủ", "completed": "Hoàn thành",
        "rejected": "Bị trả lại", "cancelled": "Đã từ chối",
    },
    "survey": {
        "draft": "Nháp", "submitted": "Chờ duyệt", "approved": "Đã duyệt",
        "rejected": "Bị trả lại", "cancelled": "Đã từ chối",
    },
    "payment_request": {
        "draft": "Nháp", "submitted": "Chờ duyệt", "approved": "Đã duyệt",
        "paid": "Đã thanh toán", "cancelled": "Đã từ chối",
    },
}

#  Trạng thái DÒNG của YCKS do người yêu cầu tự đánh (xem survey_request/model.py).
_SR_LINE_LABELS = {"": "Chưa xác định", "resurvey": "Cần khảo sát lại", "completed": "Hoàn thành"}

_AN_NCC = "Ẩn thông tin nhà cung cấp vì người hỏi không có quyền xem NCC."


def _num(v) -> float:
    return float(v) if v is not None else 0.0


def _label(entity: str, status: str) -> str:
    return _STATUS_LABELS.get(entity, {}).get(status, status)


def _cat(text: str, n: int = 200) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def _gioi_han(args: dict, mac_dinh: int) -> int:
    limit = args.get("limit")
    return max(1, min(int(limit), MAX_ROWS)) if isinstance(limit, (int, float)) else mac_dinh


def _fetch_scoped(ctx: ToolContext, model, entity: str, code: str, doc_id):
    """Lấy MỘT phiếu trong phạm vi dữ liệu người hỏi — tuyệt đối không `db.get` trần."""
    q = apply_scope(ctx.db.query(model), model, entity, ctx.user, ctx.profile)
    if entity == "purchase_request":
        q = q.filter(model.is_deleted == False)  # noqa: E712 - SQLAlchemy cần so sánh ==
    if code:
        q = q.filter(model.code == code)
    if doc_id:
        try:
            q = q.filter(model.id == int(doc_id))
        except (TypeError, ValueError):
            return None
    return q.first()


def _khong_thay(entity: str, code: str, doc_id) -> dict:
    ten = code or (f"id {doc_id}" if doc_id else "")
    return {"error": (f"Không tìm thấy {_ENTITY_LABELS[entity]} '{ten}' trong phạm vi dữ "
                      "liệu của bạn — mã sai, hoặc phiếu nằm ngoài quyền xem.")}


# ── procurement_doc_read ────────────────────────────────────────────────────────────────

def _read_po(ctx: ToolContext, code: str, doc_id) -> dict:
    po = _fetch_scoped(ctx, PurchaseOrder, "purchase_order", code, doc_id)
    if po is None:
        return _khong_thay("purchase_order", code, doc_id)
    see_supplier = ctx.can("supplier")

    header = {
        "code": po.code,
        "misa_code": po.misa_code,
        "pr_code": po.pr_code,          # YCMH nguồn — tra tiếp được bằng chính tool này
        "order_date": po.order_date,
        "status": po.status,
        "status_label": _label("purchase_order", po.status),
        "document_status_label": PO_DOCUMENT_STATUS.label_of(po.document_status,
                                                             po.document_status),
        "buyer": po.nspt,               # NSPT phụ trách mua
        "department": po.department,
        "is_urgent": bool(po.is_urgent),
        "note": _cat(po.note),
        "approve_note": _cat(po.approve_note),
        "url": _duong_dan("purchase_order", po.id),
    }
    if see_supplier:
        header["supplier_code"] = po.supplier_code
        header["supplier_name"] = po.supplier_name

    items = (ctx.db.query(POItem).filter(POItem.po_id == po.id)
             .order_by(POItem.id.asc()).all())
    lines = [{
        "product_code": it.product_code,
        "product_name": it.product_name,
        "unit": it.unit,
        "qty_order": _num(it.qty_order),
        "qty_received": _num(it.qty_received),
        "qty_remaining": _num(it.qty_remaining),
        "price": _num(it.price),
        "vat": _num(it.vat),
        "amount": _num(it.amount),
        "progress": PO_PROGRESS_STATUS.label_of(it.progress_status, it.progress_status),
        "delivery": PO_ITEM_LINE_STATUS.label_of(it.line_status, "Chưa tính"),
        "expected_date": it.expected_date,
        "required_date": it.required_date,
    } for it in items[:MAX_LINES]]

    #  Đếm tiến độ trên TOÀN BỘ dòng (kể cả phần bị cắt) để recap không nói dối.
    progress: dict[str, int] = {}
    for it in items:
        nhan = PO_PROGRESS_STATUS.label_of(it.progress_status, it.progress_status)
        progress[nhan] = progress.get(nhan, 0) + 1

    out = {
        "entity": "purchase_order",
        "entity_label": _ENTITY_LABELS["purchase_order"],
        "header": header,
        "lines": lines,
        "total": len(items),
        "totals": {
            "amount": round(sum(_num(it.amount) for it in items), 2),
            "qty_order": round(sum(_num(it.qty_order) for it in items), 3),
            "qty_received": round(sum(_num(it.qty_received) for it in items), 3),
        },
        "progress_summary": progress,
    }
    if len(items) > MAX_LINES:
        out["note"] = f"Chỉ liệt kê {MAX_LINES}/{len(items)} dòng; tổng hợp tính trên đủ."
    if not see_supplier:
        out["supplier_note"] = _AN_NCC

    #  Công nợ phát sinh từ đơn — chỉ khi người hỏi vốn được xem công nợ, và vẫn qua scope.
    if ctx.can("payable"):
        so_khoan, tong, da_tra, con_lai = (
            apply_scope(ctx.db.query(func.count(Payable.id), func.sum(Payable.total),
                                     func.sum(Payable.paid_amount),
                                     func.sum(Payable.remaining)),
                        Payable, "payable", ctx.user, ctx.profile)
            .filter(Payable.po_code == po.code).one()
        )
        out["payables"] = {
            "count": int(so_khoan or 0),
            "total": round(_num(tong), 2),
            "paid": round(_num(da_tra), 2),
            "remaining": round(_num(con_lai), 2),
        }
    else:
        out["payable_note"] = "Không kèm công nợ của đơn vì người hỏi không có quyền xem công nợ."
    return out


def _read_pr(ctx: ToolContext, code: str, doc_id) -> dict:
    pr = _fetch_scoped(ctx, PurchaseRequest, "purchase_request", code, doc_id)
    if pr is None:
        return _khong_thay("purchase_request", code, doc_id)
    see_supplier = ctx.can("supplier")

    header = {
        "code": pr.code,
        "requester": pr.requester,
        "requester_position": pr.requester_position,
        "department": pr.department,
        "purpose": pr.purpose,
        "request_date": pr.request_date,
        "need_date": pr.need_date,
        "status": pr.status,
        "status_label": _label("purchase_request", pr.status),
        "is_urgent": bool(pr.is_urgent),
        "note": _cat(pr.note),
        "url": _duong_dan("purchase_request", pr.id),
    }
    #  `suggested_supplier` là "NCC hiệu lực" — có thể chứa NCC từ khảo sát (cụm pur, Task 4)
    #  nên chỉ trả khi có supplier.read; cẩn thận hơn màn hình cũng không sai luật ẩn NCC.
    if see_supplier and pr.suggested_supplier:
        header["suggested_supplier"] = pr.suggested_supplier

    items = (ctx.db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id)
             .order_by(PurchaseRequestItem.id.asc()).all())
    lines = [{
        "product_code": it.product_code,
        "product_name": it.product_name,
        "item_group": it.item_group,
        "qty": _num(it.qty),
        "unit": it.unit,
        "price": _num(it.price),
        "amount": _num(it.amount),
        "warehouse": it.warehouse,
        "required_date": it.required_date,
        "expected_date": it.expected_date,
        "assignee": it.assignee,        # mã NSTM phụ trách dòng
        "line_status": PR_LINE_STATUS.label_of(it.line_status, it.line_status),
        "qty_ordered": _num(it.qty_ordered),
        "qty_received": _num(it.qty_received),
    } for it in items[:MAX_LINES]]

    out = {
        "entity": "purchase_request",
        "entity_label": _ENTITY_LABELS["purchase_request"],
        "header": header,
        "lines": lines,
        "total": len(items),
        "totals": {"amount": round(sum(_num(it.amount) for it in items), 2)},
    }
    if len(items) > MAX_LINES:
        out["note"] = f"Chỉ liệt kê {MAX_LINES}/{len(items)} dòng; tổng hợp tính trên đủ."
    if not see_supplier:
        out["supplier_note"] = _AN_NCC
    return out


def _read_sr(ctx: ToolContext, code: str, doc_id) -> dict:
    sr = _fetch_scoped(ctx, SurveyRequest, "survey_request", code, doc_id)
    if sr is None:
        return _khong_thay("survey_request", code, doc_id)

    header = {
        "code": sr.code,
        "requester": sr.requester,
        "department": sr.department,
        "purpose": sr.purpose,
        "request_date": sr.request_date,
        "status": sr.status,
        "status_label": _label("survey_request", sr.status),
        "note": _cat(sr.note),
        "reject_reason": _cat(sr.reject_reason),
        "url": _duong_dan("survey_request", sr.id),
    }

    rows = (ctx.db.query(SurveyRequestLine)
            .filter(SurveyRequestLine.survey_request_id == sr.id)
            .order_by(SurveyRequestLine.id.asc()).all())

    #  Số PHƯƠNG ÁN đã gắn / đã chọn theo dòng — chỉ ĐẾM, tuyệt đối không trả chi tiết
    #  option (bảng option chứa supplier_* thuộc cơ chế ẩn NCC).
    dem: dict[int, list[int]] = {}
    if rows:
        for line_id, tong, da_chon in (
            ctx.db.query(SurveyRequestOption.survey_request_line_id,
                         func.count(SurveyRequestOption.id),
                         func.sum(func.coalesce(SurveyRequestOption.is_chosen, 0)))
            .filter(SurveyRequestOption.survey_request_line_id.in_([r.id for r in rows]))
            .group_by(SurveyRequestOption.survey_request_line_id).all()
        ):
            dem[line_id] = [int(tong or 0), int(da_chon or 0)]

    lines = []
    for r in rows[:MAX_LINES]:
        tong, da_chon = dem.get(r.id, [0, 0])
        lines.append({
            "item_group": r.item_group,
            "requirement_detail": _cat(r.requirement_detail),
            "request_qty": _num(r.request_qty),
            "uom": r.uom,
            "proposed_price": _num(r.proposed_price),
            "assignee": r.assignee,     # mã NSTM khảo sát dòng
            "result_due_date": r.result_due_date,
            "result_date": r.result_date,
            "line_status": _SR_LINE_LABELS.get(r.line_status, r.line_status),
            "no_option": bool(r.no_option),
            "options": tong,
            "options_chosen": da_chon,
            "pr_code": r.pr_code,       # YCMH đã sinh từ dòng (nếu có)
        })

    out = {
        "entity": "survey_request",
        "entity_label": _ENTITY_LABELS["survey_request"],
        "header": header,
        "lines": lines,
        "total": len(rows),
        "totals": {
            "completed": sum(1 for r in rows if r.is_completed),
            "with_options": sum(1 for lid in dem if dem[lid][0] > 0),
        },
    }
    if len(rows) > MAX_LINES:
        out["note"] = f"Chỉ liệt kê {MAX_LINES}/{len(rows)} dòng; tổng hợp tính trên đủ."
    return out


_READERS = {
    "purchase_order": _read_po,
    "purchase_request": _read_pr,
    "survey_request": _read_sr,
}


def _run_doc_read(ctx: ToolContext, args: dict) -> dict:
    entity = str(args.get("entity") or "").strip()
    if entity not in _READERS:
        return {"error": f"entity phải là một trong: {', '.join(_READERS)}."}
    if not ctx.can(entity):
        return denied(_ENTITY_LABELS[entity])
    code = str(args.get("code") or "").strip()
    doc_id = args.get("id")
    if not code and not doc_id:
        return {"error": "Cần mã phiếu (code) hoặc id để đọc chi tiết."}
    return _READERS[entity](ctx, code, doc_id)


PROCUREMENT_DOC_READ_SPEC = ToolSpec(
    name="procurement_doc_read",
    description=(
        "Đọc CHI TIẾT một chứng từ thu mua theo mã phiếu: Đơn mua hàng (purchase_order, mã "
        "PO...), Yêu cầu mua hàng (purchase_request, mã PYC...), Yêu cầu báo giá "
        "(survey_request, mã YCKS...). Trả đầu phiếu (trạng thái, người phụ trách), từng "
        "dòng hàng (mã hàng, SL đặt/đã nhận, giá, tiến độ giao), tổng giá trị; ĐMH kèm khối "
        "công nợ phát sinh, YCKS kèm số phương án khảo sát mỗi dòng. Dùng cho 'đơn PO00123 "
        "tới đâu rồi', 'recap đơn hàng X', 'ai mua gì giá bao nhiêu trong đơn Y'. Muốn SO "
        "GIÁ với NCC khác: lấy product_code từng dòng trong kết quả rồi gọi tiếp "
        "product_best_price / suppliers_for_product. Kết quả có `url` mở màn chi tiết."
    ),
    parameters={
        "type": "object",
        "properties": {
            "entity": {
                "type": "string",
                "enum": ["purchase_order", "purchase_request", "survey_request"],
                "description": ("Loại chứng từ: purchase_order=Đơn mua hàng (ĐMH/PO), "
                                "purchase_request=Yêu cầu mua hàng (YCMH/PYC), "
                                "survey_request=Yêu cầu báo giá (YCKS/YCBG)."),
            },
            "code": {"type": "string",
                     "description": "Mã phiếu chính xác, vd PO00045 / PYC00012 / YCKS250801-1."},
            "id": {"type": "integer", "description": "ID phiếu (dùng khi đã có id từ tool khác)."},
        },
        "required": ["entity"],
    },
    handler=_run_doc_read,
)


# ── pending_procurement_approvals ───────────────────────────────────────────────────────

def _pend_pr(r: PurchaseRequest, see_supplier: bool) -> dict:
    return {"code": r.code, "requester": r.requester, "department": r.department,
            "request_date": r.request_date, "need_date": r.need_date,
            "is_urgent": bool(r.is_urgent)}


def _pend_sr(r: SurveyRequest, see_supplier: bool) -> dict:
    return {"code": r.code, "requester": r.requester, "department": r.department,
            "request_date": r.request_date, "purpose": _cat(r.purpose, 100)}


def _pend_survey(r: Survey, see_supplier: bool) -> dict:
    return {"code": r.code,
            "survey_type": "Khảo sát NCC" if r.survey_type == "supplier" else "Khảo sát SP",
            "item_group": r.item_group, "item_name": r.item_name, "nspt": r.nspt,
            "received_date": r.received_date}


def _pend_po(r: PurchaseOrder, see_supplier: bool) -> dict:
    item = {"code": r.code, "order_date": r.order_date, "buyer": r.nspt,
            "department": r.department, "is_urgent": bool(r.is_urgent)}
    if see_supplier:
        item["supplier_name"] = r.supplier_name
    return item


def _pend_pttt(r: PaymentRequest, see_supplier: bool) -> dict:
    item = {"code": r.code, "request_date": r.request_date, "total": _num(r.total)}
    if see_supplier:
        item["supplier_name"] = r.supplier_name
    return item


#  Thứ tự liệt kê = thứ tự luồng nghiệp vụ: báo giá -> khảo sát -> mua -> đơn -> thanh toán.
_PENDING = [
    ("survey_request", SurveyRequest, _pend_sr),
    ("survey", Survey, _pend_survey),
    ("purchase_request", PurchaseRequest, _pend_pr),
    ("purchase_order", PurchaseOrder, _pend_po),
    ("payment_request", PaymentRequest, _pend_pttt),
]

_NHAC_KHONG_DUYET_HO = ("Trợ lý không duyệt hộ — mở `url` từng phiếu để xem và bấm Duyệt "
                        "trên màn hình.")


def _run_pending(ctx: ToolContext, args: dict) -> dict:
    entity_filter = str(args.get("entity") or "").strip()
    hop_le = [e for e, _, _ in _PENDING]
    if entity_filter and entity_filter not in hop_le:
        return {"error": f"entity phải là một trong: {', '.join(hop_le)}."}
    limit = _gioi_han(args, mac_dinh=10)
    see_supplier = ctx.can("supplier")

    groups, khong_quyen = [], []
    for entity, model, builder in _PENDING:
        if entity_filter and entity != entity_filter:
            continue
        if not ctx.can(entity, "approve"):
            khong_quyen.append(_ENTITY_LABELS[entity])
            continue
        q = apply_scope(ctx.db.query(model), model, entity, ctx.user, ctx.profile) \
            .filter(model.status == "submitted")
        if entity == "purchase_request":
            q = q.filter(model.is_deleted == False)  # noqa: E712
        pending = q.count()
        #  Phiếu trình SỚM NHẤT lên đầu — người chờ lâu nhất được duyệt trước.
        rows = q.order_by(model.id.asc()).limit(limit).all()
        group = {
            "entity": entity,
            "entity_label": _ENTITY_LABELS[entity],
            "pending": pending,
            "items": [{**builder(r, see_supplier),
                       "url": _duong_dan(entity, r.id)} for r in rows],
        }
        if pending > limit:
            group["note"] = f"Chỉ liệt kê {limit}/{pending} phiếu trình sớm nhất."
        groups.append(group)

    out: dict = {
        "total": sum(g["pending"] for g in groups),
        "groups": groups,
        "reminder": _NHAC_KHONG_DUYET_HO,
    }
    if entity_filter and khong_quyen:
        #  Hỏi đích danh một loại mà không có quyền duyệt loại đó -> nói thẳng, đừng trả 0.
        return {"denied": True,
                "reason": f"Bạn không có quyền duyệt {khong_quyen[0]}."}
    if not groups:
        out["note"] = "Bạn không có quyền duyệt loại phiếu thu mua nào."
    elif khong_quyen:
        out["note"] = "Bỏ qua các loại phiếu bạn không có quyền duyệt: " + ", ".join(khong_quyen) + "."
    if groups and not see_supplier:
        out["supplier_note"] = _AN_NCC
    return out


PENDING_PROCUREMENT_APPROVALS_SPEC = ToolSpec(
    name="pending_procurement_approvals",
    description=(
        "Đếm + liệt kê PHIẾU THU MUA ĐANG CHỜ DUYỆT mà chính người hỏi có quyền duyệt, "
        "trong phạm vi dữ liệu của họ: Yêu cầu báo giá, Phiếu khảo sát, Yêu cầu mua hàng, "
        "Đơn mua hàng, Yêu cầu thanh toán. Dùng cho 'tôi cần duyệt bao nhiêu phiếu khảo "
        "sát', 'có đơn hàng nào chờ tôi duyệt không', 'hôm nay tôi phải duyệt gì bên thu "
        "mua'. Mỗi phiếu kèm `url` mở màn chi tiết để NGƯỜI DÙNG tự bấm Duyệt — trợ lý "
        "không duyệt hộ. Khác my_approval_tasks: tool kia là bộ máy phê duyệt (Văn bản); "
        "chứng từ thu mua duyệt bằng nút trên màn nên phải dùng tool này. Muốn recap sâu "
        "một phiếu trước khi duyệt -> gọi tiếp procurement_doc_read với mã phiếu đó."
    ),
    parameters={
        "type": "object",
        "properties": {
            "entity": {
                "type": "string",
                "enum": ["survey_request", "survey", "purchase_request",
                         "purchase_order", "payment_request"],
                "description": ("Chỉ đếm một loại phiếu (tùy chọn): survey_request=Yêu cầu "
                                "báo giá, survey=Phiếu khảo sát, purchase_request=Yêu cầu "
                                "mua hàng, purchase_order=Đơn mua hàng, payment_request="
                                "Yêu cầu thanh toán. Bỏ trống = mọi loại."),
            },
            "limit": {"type": "integer",
                      "description": f"Số phiếu liệt kê mỗi loại, mặc định 10, trần {MAX_ROWS}."},
        },
    },
    handler=_run_pending,
)


# ── my_procurement_requests ─────────────────────────────────────────────────────────────

def _cua_toi(q, model, user):
    """Ép về phiếu CỦA CHÍNH người hỏi — kể cả khi scope của họ là all (quản lý hỏi
    "phiếu của tôi" thì vẫn chỉ trả phiếu họ đứng tên, không đổ cả công ty)."""
    dieu_kien = [model.created_by == user.id]
    emp_id = getattr(user, "employee_id", None)
    if emp_id:
        # requester_id là ID NHÂN SỰ (không phải id tài khoản) — phiếu người khác nhập hộ
        # nhưng đứng tên mình vẫn phải hiện ra.
        dieu_kien.append(model.requester_id == emp_id)
    return q.filter(or_(*dieu_kien))


def _run_my_requests(ctx: ToolContext, args: dict) -> dict:
    entity_filter = str(args.get("entity") or "").strip()
    hop_le = ["survey_request", "purchase_request"]
    if entity_filter and entity_filter not in hop_le:
        return {"error": f"entity phải là một trong: {', '.join(hop_le)}."}
    limit = _gioi_han(args, mac_dinh=10)

    groups, khong_quyen = [], []
    for entity, model in (("survey_request", SurveyRequest),
                          ("purchase_request", PurchaseRequest)):
        if entity_filter and entity != entity_filter:
            continue
        if not ctx.can(entity):
            khong_quyen.append(_ENTITY_LABELS[entity])
            continue
        q = _cua_toi(apply_scope(ctx.db.query(model), model, entity, ctx.user, ctx.profile),
                     model, ctx.user)
        if entity == "purchase_request":
            q = q.filter(model.is_deleted == False)  # noqa: E712
        total = q.count()
        rows = q.order_by(model.id.desc()).limit(limit).all()  # phiếu mới nhất trước
        ids = [r.id for r in rows]

        if entity == "purchase_request":
            #  Tiến độ mua gộp theo dòng: một truy vấn group-by cho cả trang, không N+1.
            gom: dict[int, dict] = {}
            if ids:
                for pr_id, ls, so_dong, sl, sl_dat, sl_nhan in (
                    ctx.db.query(PurchaseRequestItem.pr_id,
                                 PurchaseRequestItem.line_status,
                                 func.count(PurchaseRequestItem.id),
                                 func.sum(PurchaseRequestItem.qty),
                                 func.sum(PurchaseRequestItem.qty_ordered),
                                 func.sum(PurchaseRequestItem.qty_received))
                    .filter(PurchaseRequestItem.pr_id.in_(ids))
                    .group_by(PurchaseRequestItem.pr_id, PurchaseRequestItem.line_status)
                ):
                    g = gom.setdefault(pr_id, {"lines": 0, "progress": {},
                                               "qty": 0.0, "qty_ordered": 0.0,
                                               "qty_received": 0.0})
                    nhan = PR_LINE_STATUS.label_of(ls, ls or "Chưa xác định")
                    g["lines"] += int(so_dong or 0)
                    g["progress"][nhan] = g["progress"].get(nhan, 0) + int(so_dong or 0)
                    g["qty"] += _num(sl)
                    g["qty_ordered"] += _num(sl_dat)
                    g["qty_received"] += _num(sl_nhan)
            items = [{
                "code": r.code,
                "request_date": r.request_date,
                "need_date": r.need_date,
                "status": r.status,
                "status_label": _label("purchase_request", r.status),
                "is_urgent": bool(r.is_urgent),
                "purpose": _cat(r.purpose, 100),
                "url": _duong_dan("purchase_request", r.id),
                **gom.get(r.id, {"lines": 0, "progress": {}, "qty": 0.0,
                                 "qty_ordered": 0.0, "qty_received": 0.0}),
            } for r in rows]
        else:
            #  YCKS: đếm dòng đã khảo sát xong + dòng đã sinh YCMH — đủ để nói "tới đâu".
            gom = {}
            if ids:
                for sr_id, so_dong, xong, da_tao_pr in (
                    ctx.db.query(SurveyRequestLine.survey_request_id,
                                 func.count(SurveyRequestLine.id),
                                 func.sum(case((SurveyRequestLine.is_completed == True, 1),  # noqa: E712
                                               else_=0)),
                                 func.sum(case((func.coalesce(SurveyRequestLine.pr_code, "")
                                                != "", 1), else_=0)))
                    .filter(SurveyRequestLine.survey_request_id.in_(ids))
                    .group_by(SurveyRequestLine.survey_request_id)
                ):
                    gom[sr_id] = {"lines": int(so_dong or 0),
                                  "lines_completed": int(xong or 0),
                                  "lines_pr_created": int(da_tao_pr or 0)}
            items = [{
                "code": r.code,
                "request_date": r.request_date,
                "status": r.status,
                "status_label": _label("survey_request", r.status),
                "purpose": _cat(r.purpose, 100),
                "url": _duong_dan("survey_request", r.id),
                **gom.get(r.id, {"lines": 0, "lines_completed": 0, "lines_pr_created": 0}),
            } for r in rows]

        group = {"entity": entity, "entity_label": _ENTITY_LABELS[entity],
                 "total": total, "items": items}
        if total > limit:
            group["note"] = f"Chỉ liệt kê {limit}/{total} phiếu mới nhất."
        groups.append(group)

    if entity_filter and khong_quyen:
        return {"denied": True, "reason": f"Bạn không có quyền xem {khong_quyen[0]}."}
    out: dict = {"total": sum(g["total"] for g in groups), "groups": groups}
    if not groups:
        out["note"] = "Bạn không có quyền xem Yêu cầu báo giá lẫn Yêu cầu mua hàng."
    elif khong_quyen:
        out["note"] = "Bỏ qua loại phiếu bạn không có quyền xem: " + ", ".join(khong_quyen) + "."
    return out


MY_PROCUREMENT_REQUESTS_SPEC = ToolSpec(
    name="my_procurement_requests",
    description=(
        "Liệt kê phiếu thu mua CỦA CHÍNH người hỏi (họ tạo hoặc đứng tên người yêu cầu), "
        "mới nhất trước: Yêu cầu báo giá (survey_request) và Yêu cầu mua hàng "
        "(purchase_request), kèm RECAP TIẾN ĐỘ - YCMH có số dòng theo từng bước mua (chưa "
        "tạo đơn / đã đặt / đã nhận...) + tổng SL yêu cầu/đã đặt/đã nhận; YCKS có số dòng "
        "đã khảo sát xong và đã sinh YCMH. Dùng cho 'phiếu của tôi tới đâu rồi', 'yêu cầu "
        "mua hàng mới nhất của tôi', 'hàng tôi đặt mua đã về chưa'. Muốn xem SÂU một phiếu "
        "trong kết quả -> gọi tiếp procurement_doc_read với mã phiếu đó. Khác "
        "my_requests_status: tool kia đọc bộ máy phê duyệt (Văn bản); phiếu thu mua phải "
        "dùng tool này."
    ),
    parameters={
        "type": "object",
        "properties": {
            "entity": {
                "type": "string",
                "enum": ["survey_request", "purchase_request"],
                "description": ("Chỉ một loại phiếu (tùy chọn): survey_request=Yêu cầu "
                                "báo giá, purchase_request=Yêu cầu mua hàng. "
                                "Bỏ trống = cả hai."),
            },
            "limit": {"type": "integer",
                      "description": f"Số phiếu mỗi loại, mặc định 10, trần {MAX_ROWS}."},
        },
    },
    handler=_run_my_requests,
)
