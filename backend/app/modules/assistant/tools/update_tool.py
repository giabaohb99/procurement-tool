"""Tool tầng GHI có xác nhận (CR-218): `propose_document_update` + `propose_document_delete` —
CHỈ trả BẢN ĐỀ XUẤT.

Đây là chỗ duy nhất trợ lý "chạm" vào tầng ghi, và bản thân tool KHÔNG ghi gì cả: nó trả
về bản so sánh cũ → mới + một `confirm_token` (Fernet ký từ JWT_SECRET, hết hạn 15 phút,
buộc vào đúng người hỏi). Giao diện chat vẽ thẻ so sánh + nút Xác nhận; NGƯỜI bấm nút thì
FE mới gọi `POST /api/assistant/confirm-update`, và lúc đó backend kiểm lại TOÀN BỘ từ đầu
(quyền write + phạm vi + trạng thái còn sửa được + whitelist trường) rồi ghi qua đúng
service của form (update_pr / update_sr / update_request) để validate + audit nguyên vẹn.
Token chỉ là "tờ đề xuất có hạn dùng", KHÔNG phải giấy thông hành: mọi điều kiện được
kiểm lại lúc xác nhận, đề phòng phiếu đổi trạng thái / quyền bị thu hồi giữa hai bước.

Đợt 1 (thiết kế ở doc/erp/tai-lieu-ai/02 mục "Đợt CR-218") chỉ mở phần ĐẦU PHIẾU:
- YCMH: purpose / need_date / note        - YCBG: purpose / note
- YCTT: 3 câu chữ bản in (print_texts, CR-149 — sửa được cả khi Chờ duyệt/Đã duyệt)

AI-0006 (đại ca chốt 09/10) mở thêm:
- Dòng hàng YCMH / YCBG: thêm dòng · bỏ dòng · đổi số lượng (`line_ops`). Ghi bằng cách dựng
  lại ĐỦ danh sách dòng từ sổ rồi đưa qua đúng `update_pr` / `update_sr` như form gửi lên.
- Đơn nghỉ phép: từ ngày / đến ngày / loại nghỉ / lý do (ai-CR-151) — qua `leave.request_service.update`.
- XÓA (`propose_document_delete`): chỉ phiếu CHÍNH người hỏi lập, còn Nháp / Bị trả lại, và
  tài khoản đủ quyền `delete` + phạm vi xóa. YCMH · YCBG · đơn nghỉ phép · việc Dự án.
  Đề nghị thanh toán và phiếu hỗ trợ KHÔNG xóa qua trợ lý — tool trả link để người dùng tự
  mở. Cùng một token / một nút / một endpoint `confirm-update` (khóa `a = delete` trong token).
"""
import base64
import hashlib
import json
from datetime import date
from decimal import Decimal

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.auth import get_perm_profile, user_has_permission
from app.core.config import settings as _env
from app.core.scoping import apply_scope, get_scoped
from app.modules.leave.constants import EDITABLE_STATUSES

from .approval_tool import _detail_url
from .base import ToolContext, ToolSpec
from .draft_tool import _clean_text, _iso_date
from .procurement_doc_tool import _label

CONFIRM_TTL_SECONDS = 15 * 60   # đề xuất sửa chỉ sống 15 phút — quá hạn phải hỏi lại

#  Trạng thái còn sửa được — chép ĐÚNG luật của service từng form (update_pr / update_sr /
#  update_request), không nới thêm: YCTT chỉ mở vì payload gói mỗi print_texts (CR-149).
_DRAFT_STATUSES = ("draft", "rejected")
_PRINT_TEXT_STATUSES = ("draft", "submitted", "approved")
#  Đơn nghỉ phép: Nháp / Trả về chỉnh sửa — lấy thẳng từ phân hệ nghỉ phép, đừng chép số (ai-CR-151).
_LEAVE_EDITABLE = EDITABLE_STATUSES

#  Khóa phẳng cho model (dễ điền hơn dict lồng nhau) — 3 khóa print_* map về print_texts.
_PRINT_KEY_MAP = {"print_content": "content", "print_line_desc": "line_desc",
                  "print_transfer": "transfer"}
_DATE_KEYS = ("need_date", "from_date", "to_date")

#  Trần số thao tác dòng trong MỘT đề xuất — nhiều hơn thì mở form cho chắc.
MAX_LINE_OPS = 20
_MAX_QTY = 1_000_000_000

#  Đường chi tiết v2 mà `approval_tool._DETAIL_URLS` chưa có.
_EXTRA_URLS = {
    "leave_request": "/hr/leave-requests/{id}",
    "work_task": "/project/tasks/{id}",
    "ticket": "/support/tickets/{id}",
}

_ENTITY_RULES: dict[str, dict] = {
    "purchase_request": {
        "label": "Yêu cầu mua hàng (YCMH)",
        "fields": {"purpose": "Mục đích mua hàng", "need_date": "Ngày cần hàng",
                   "note": "Ghi chú"},
        "lines": True,
    },
    "survey_request": {
        "label": "Yêu cầu báo giá (YCBG)",
        "fields": {"purpose": "Mục đích khảo sát", "note": "Ghi chú"},
        "lines": True,
    },
    "payment_request": {
        "label": "Yêu cầu thanh toán (YCTT)",
        "fields": {"print_content": "Câu Nội dung (bản in)",
                   "print_line_desc": "Câu Diễn giải bảng (bản in)",
                   "print_transfer": "Nội dung chuyển khoản (bản in)"},
    },
    "leave_request": {
        "label": "Đơn nghỉ phép",
        "fields": {"from_date": "Từ ngày", "to_date": "Đến ngày", "leave_type": "Loại nghỉ",
                   "reason": "Lý do"},
    },
}

_PARAMS = {
    "type": "object",
    "properties": {
        "entity": {
            "type": "string",
            "enum": list(_ENTITY_RULES),
            "description": "Loại phiếu: purchase_request (YCMH) | survey_request (YCBG) | "
                           "payment_request (YCTT) | leave_request (đơn nghỉ phép).",
        },
        "code": {
            "type": "string",
            "description": "Mã phiếu cần sửa, ví dụ YCMH00012 / YCBG00034 / YCTT00045 / mã đơn nghỉ.",
        },
        "changes": {
            "type": "object",
            "description": "CHỈ điền các trường muốn sửa theo yêu cầu người dùng — trường "
                           "không nhắc tới thì BỎ, đừng chép lại giá trị cũ.",
            "properties": {
                "purpose": {"type": "string",
                            "description": "Mục đích mới (YCMH/YCBG)."},
                "need_date": {"type": "string",
                              "description": "Ngày cần hàng mới, YYYY-MM-DD (chỉ YCMH)."},
                "note": {"type": "string", "description": "Ghi chú mới (YCMH/YCBG)."},
                "print_content": {
                    "type": "string",
                    "description": "Câu «Nội dung» mới trên bản in YCTT (chỉ YCTT).",
                },
                "print_line_desc": {
                    "type": "string",
                    "description": "Câu «Diễn giải» mới trong bảng bản in YCTT (chỉ YCTT).",
                },
                "print_transfer": {
                    "type": "string",
                    "description": "«Nội dung chuyển khoản» mới trên bản in YCTT (chỉ YCTT).",
                },
                "from_date": {"type": "string",
                              "description": "Ngày bắt đầu nghỉ mới, YYYY-MM-DD (chỉ đơn nghỉ)."},
                "to_date": {"type": "string",
                            "description": "Ngày kết thúc nghỉ mới, YYYY-MM-DD (chỉ đơn nghỉ)."},
                "leave_type": {"type": "string",
                               "description": "Mã hoặc tên loại nghỉ mới (chỉ đơn nghỉ)."},
                "reason": {"type": "string",
                           "description": "Lý do nghỉ mới, đúng lời người dùng (chỉ đơn nghỉ)."},
            },
        },
        "line_ops": {
            "type": "array",
            "description": "Sửa DÒNG HÀNG (chỉ YCMH/YCBG). Mỗi phần tử một thao tác: "
                           "add (thêm dòng: product_name + qty + unit), remove (bỏ dòng số "
                           "line_no), set_qty (đổi số lượng dòng số line_no thành qty). "
                           "line_no đếm từ 1 theo thứ tự dòng trên phiếu — chưa chắc dòng "
                           "nào thì tra phiếu (procurement_doc_read) trước, CẤM đoán.",
            "items": {
                "type": "object",
                "properties": {
                    "op": {"type": "string", "enum": ["add", "remove", "set_qty"]},
                    "line_no": {"type": "integer", "description": "Số thứ tự dòng (remove/set_qty)."},
                    "product_name": {"type": "string", "description": "Tên hàng (add)."},
                    "qty": {"type": "number", "description": "Số lượng (add/set_qty), > 0."},
                    "unit": {"type": "string", "description": "Đơn vị tính (add)."},
                },
                "required": ["op"],
            },
        },
    },
    "required": ["entity", "code"],
}

_DESC = (
    "ĐỀ XUẤT sửa một phiếu ĐÃ CÓ theo yêu cầu người dùng — KHÔNG ghi gì vào phiếu. Tool trả "
    "về bản so sánh cũ → mới; giao diện hiện thẻ xác nhận và CHÍNH NGƯỜI DÙNG bấm nút "
    "'Xác nhận sửa' thì hệ thống mới ghi. Sửa được: YCMH mục đích / ngày cần hàng / ghi chú; "
    "YCBG mục đích / ghi chú; dòng hàng YCMH và YCBG (thêm dòng, bỏ dòng, đổi số lượng — "
    "qua line_ops); đơn nghỉ phép từ ngày / đến ngày / loại nghỉ / lý do (YCMH, YCBG, đơn nghỉ chỉ "
    "khi phiếu Nháp hoặc Bị trả lại); YCTT sửa được 3 câu chữ bản in (kể cả khi phiếu đã "
    "gửi duyệt / đã duyệt). KHÔNG sửa được: giá, nhà cung cấp, số tiền, trạng thái, hạn chi "
    "— các phần đó phải mở form sửa tay, nói rõ cho người dùng. Chỉ điền đúng trường người "
    "dùng yêu cầu đổi với giá trị MỚI họ nêu — thiếu giá trị thì hỏi lại trước, CẤM tự bịa. "
    "Sau khi gọi, tóm tắt thay đổi và mời người dùng bấm nút 'Xác nhận sửa' dưới câu trả "
    "lời — nhấn mạnh phiếu CHƯA bị sửa cho tới khi họ bấm."
)


def _fernet() -> Fernet:
    #  Cùng cách suy khóa với app_settings: sha256(JWT_SECRET) — không thêm secret mới.
    key = base64.urlsafe_b64encode(hashlib.sha256(_env.JWT_SECRET.encode()).digest())
    return Fernet(key)


def _url_of(entity: str, doc_id: int) -> str:
    template = _EXTRA_URLS.get(entity)
    return template.format(id=doc_id) if template else _detail_url(entity, doc_id)


def _model_of(entity: str):
    if entity == "purchase_request":
        from app.modules.purchase_request.model import PurchaseRequest
        return PurchaseRequest
    if entity == "survey_request":
        from app.modules.survey_request.model import SurveyRequest
        return SurveyRequest
    if entity == "leave_request":
        from app.modules.leave.request_model import LeaveRequest
        return LeaveRequest
    if entity == "ticket":
        from app.modules.ticket.model import Ticket
        return Ticket
    from app.modules.payment_request.model import PaymentRequest
    return PaymentRequest


def _soft_deleted(entity: str, doc) -> bool:
    return entity in ("purchase_request", "leave_request") and bool(getattr(doc, "is_deleted", False))


def _fetch_by_code(db, entity: str, code: str, user, profile, action: str = "write"):
    """Tìm phiếu theo mã TRONG phạm vi `action` của người hỏi — ngoài phạm vi coi như không có."""
    model = _model_of(entity)
    q = db.query(model).filter(model.code == code)
    if entity in ("purchase_request", "leave_request"):
        q = q.filter(model.is_deleted.is_(False))
    q = apply_scope(q, model, entity, user, profile, action=action)
    return q.first()


def _status_label(entity: str, doc) -> str:
    if entity == "leave_request":
        from app.modules.leave.constants import LEAVE_REQUEST_STATUS_LABELS, label
        return label(LEAVE_REQUEST_STATUS_LABELS, doc.status, str(doc.status))
    return _label(entity, doc.status)


def _editable_error(entity: str, doc) -> str | None:
    """None nếu phiếu còn sửa được; ngược lại trả câu giải thích cho người dùng."""
    label = _status_label(entity, doc)
    if entity == "payment_request":
        if doc.status in _PRINT_TEXT_STATUSES:
            return None
        return (f"Phiếu {doc.code} đang ở trạng thái {label} — câu chữ bản in chỉ sửa được "
                "khi phiếu Nháp, Chờ duyệt hoặc Đã duyệt.")
    if entity == "leave_request":
        if int(doc.status or 0) in _LEAVE_EDITABLE:
            return None
        return (f"Đơn {doc.code} đang ở trạng thái {label} — chỉ sửa được khi đơn Nháp hoặc "
                "Trả về chỉnh sửa.")
    if doc.status in _DRAFT_STATUSES:
        return None
    return (f"Phiếu {doc.code} đang ở trạng thái {label} — chỉ sửa được khi phiếu ở "
            "trạng thái Nháp hoặc Bị trả lại.")


def _leave_type_name(db, type_id: int) -> str:
    from app.modules.leave.catalog_model import LeaveType
    row = db.get(LeaveType, int(type_id or 0)) if type_id else None
    return row.name if row else ""


def _find_leave_type(db, wanted: str):
    """Loại nghỉ đang BẬT khớp ĐÚNG mã hoặc tên. Khác `_pick_leave_type` của tool soạn
    nháp: ở đây KHÔNG lùi về phép năm — sửa đơn mà đoán loại nghỉ là sửa vào quỹ phép."""
    from app.modules.leave.catalog_model import LeaveType
    key = (wanted or "").strip().lower()
    rows = (db.query(LeaveType).filter(LeaveType.is_active.is_(True))
            .order_by(LeaveType.sort_order, LeaveType.id).all())
    for r in rows:
        if key and key in ((r.code or "").lower(), (r.name or "").lower()):
            return r, rows
    return None, rows


def _old_value(db, entity: str, doc, field: str) -> str:
    if field in _PRINT_KEY_MAP:
        from app.modules.payment_request.service import parse_print_texts
        return parse_print_texts(doc.print_texts).get(_PRINT_KEY_MAP[field], "")
    if field == "leave_type":
        return _leave_type_name(db, doc.leave_type_id)
    value = getattr(doc, field, "")
    if isinstance(value, date):
        return value.isoformat()
    return str(value or "")


def _state_sig(db, entity: str, doc) -> str:
    """Dấu trạng thái phiếu lúc đề xuất (ai-CR-153): giá trị hiện tại của mọi ô sửa được + (id, số lượng) từng dòng.

    Token chỉ có hạn 15 phút, không nhớ đã dùng hay chưa: tải lại trang web rồi bấm lại thẻ «thêm dòng» là thêm trùng
    dòng. Bấm xác nhận thì so dấu này — đã ghi một lần (giá trị đã đổi) hay có người sửa phiếu xen giữa đều lệch dấu,
    trả 409, không ghi. Không cần bảng hay bộ nhớ đệm nào."""
    rules = _ENTITY_RULES[entity]
    state: dict = {f: _old_value(db, entity, doc, f) for f in rules["fields"]}
    if rules.get("lines"):
        state["_lines"] = [[r.id, _line_qty(entity, r)] for r in _current_lines(db, entity, doc.id)]
    raw = json.dumps(state, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _clean_changes(entity: str, raw, allow_empty: bool = False) -> tuple[dict, str | None]:
    """Lọc changes theo whitelist của entity + chuẩn hóa giá trị. Trả (fields, lỗi)."""
    rules = _ENTITY_RULES[entity]
    if raw is None and allow_empty:
        return {}, None
    if not isinstance(raw, dict):
        return {}, "Thiếu changes — hỏi người dùng muốn sửa trường nào, giá trị mới là gì."
    fields: dict[str, str] = {}
    rejected = [k for k in raw if k not in rules["fields"]]
    for key in rules["fields"]:
        if key not in raw:
            continue
        if key in _DATE_KEYS:
            value = _iso_date(raw.get(key))
            if value is None:
                return {}, f"{key} sai định dạng — cần YYYY-MM-DD, hỏi lại người dùng."
        elif key == "leave_type":
            value = _clean_text(raw.get(key), 50)
            if not value:
                return {}, "leave_type rỗng — hỏi người dùng muốn đổi sang loại nghỉ nào."
        else:
            #  Lý do đơn nghỉ là `Str1000` ở schema của form — cắt đúng trần đó, đừng cụt ở 500.
            value = _clean_text(raw.get(key), 1000 if key == "reason" else 500)
            if key == "reason" and not value:
                return {}, "reason rỗng — hỏi người dùng lý do nghỉ mới là gì."
        fields[key] = value
    if rejected:
        allowed = ", ".join(rules["fields"].values())
        return {}, (f"Trường {', '.join(rejected)} KHÔNG sửa được qua trợ lý với loại phiếu "
                    f"này (chỉ sửa được: {allowed}) — báo người dùng mở form sửa tay.")
    if not fields and not allow_empty:
        return {}, "changes rỗng — hỏi người dùng muốn sửa trường nào, giá trị mới là gì."
    return fields, None


# ── Dòng hàng YCMH / YCBG (AI-0006) ─────────────────────────────────────────────────────

def _current_lines(db, entity: str, doc_id: int) -> list:
    """Dòng hiện có của phiếu, theo thứ tự id — đúng thứ tự `line_no` người dùng thấy."""
    if entity == "purchase_request":
        from app.modules.purchase_request.model import PurchaseRequestItem
        return (db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == doc_id)
                .order_by(PurchaseRequestItem.id).all())
    from app.modules.survey_request.service import lines_of
    return lines_of(db, doc_id)


def _line_name(entity: str, row) -> str:
    if entity == "purchase_request":
        return row.product_name or row.product_code or ""
    return row.requirement_detail or row.item_group or ""


def _line_qty(entity: str, row) -> float:
    value = row.qty if entity == "purchase_request" else row.request_qty
    return float(value or 0)


def _line_unit(entity: str, row) -> str:
    return (row.unit if entity == "purchase_request" else row.uom) or ""


def _qty_text(qty: float, unit: str) -> str:
    return f"SL {qty:g}" + (f" {unit}" if unit else "")


def _as_qty(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        qty = float(value)
    except ValueError:
        return None
    return qty if 0 < qty <= _MAX_QTY else None


def _clean_line_ops(entity: str, raw, rows: list) -> tuple[list, list, str | None]:
    """Chuẩn hóa line_ops của model thành thao tác theo ID dòng (để lúc xác nhận không đếm
    lệch nếu ai đó vừa thêm dòng). Trả (ops theo id, dòng so sánh để hiện thẻ, lỗi)."""
    if raw in (None, []):
        return [], [], None
    if not isinstance(raw, list):
        return [], [], "line_ops phải là danh sách thao tác."
    if len(raw) > MAX_LINE_OPS:
        return [], [], (f"Quá {MAX_LINE_OPS} thao tác dòng trong một lần — báo người dùng mở "
                        "form sửa tay.")
    by_no = {i + 1: r for i, r in enumerate(rows)}
    ops: list[dict] = []
    view: list[dict] = []
    touched: set[int] = set()
    added = removed = 0
    for i, op in enumerate(raw, start=1):
        if not isinstance(op, dict):
            return [], [], f"Thao tác dòng thứ {i} sai định dạng."
        kind = str(op.get("op") or "").strip()
        if kind == "add":
            name = _clean_text(op.get("product_name"), 255)
            qty = _as_qty(op.get("qty"))
            unit = _clean_text(op.get("unit"), 25)
            if not name or qty is None:
                return [], [], ("Thêm dòng cần tên hàng và số lượng lớn hơn 0 — hỏi lại người "
                                "dùng, CẤM tự bịa.")
            ops.append({"op": "add", "name": name, "qty": qty, "unit": unit})
            view.append({"field": f"line_add_{i}", "label": "Thêm dòng", "old": "",
                         "new": f"{name} · {_qty_text(qty, unit)}"})
            added += 1
            continue
        if kind not in ("remove", "set_qty"):
            return [], [], f"Thao tác dòng thứ {i}: op phải là add | remove | set_qty."
        line_no = op.get("line_no")
        row = by_no.get(line_no) if isinstance(line_no, int) and not isinstance(line_no, bool) else None
        if row is None:
            return [], [], (f"Phiếu không có dòng số {line_no} (phiếu có {len(rows)} dòng) — tra "
                            "lại phiếu rồi hỏi người dùng đúng dòng nào.")
        if row.id in touched:
            return [], [], f"Dòng số {line_no} bị nêu hai lần — mỗi dòng một thao tác thôi."
        touched.add(row.id)
        name, unit, old_qty = _line_name(entity, row), _line_unit(entity, row), _line_qty(entity, row)
        label = f"Dòng {line_no} · {name}"
        if kind == "remove":
            ops.append({"op": "remove", "id": row.id})
            view.append({"field": f"line_remove_{row.id}", "label": label,
                         "old": _qty_text(old_qty, unit), "new": "Bỏ dòng"})
            removed += 1
            continue
        qty = _as_qty(op.get("qty"))
        if qty is None:
            return [], [], f"Số lượng mới của dòng {line_no} phải lớn hơn 0."
        if qty == old_qty:
            continue
        ops.append({"op": "set_qty", "id": row.id, "qty": qty})
        view.append({"field": f"line_qty_{row.id}", "label": label,
                     "old": _qty_text(old_qty, unit), "new": _qty_text(qty, unit)})
    if len(rows) - removed + added < 1:
        return [], [], ("Phiếu phải còn ít nhất một dòng — muốn bỏ cả phiếu thì dùng "
                        "propose_document_delete.")
    return ops, view, None


def _row_to_input(schema_cls, row):
    """Dựng lại MỘT dòng đúng hình form gửi lên, từ chính bản ghi trong sổ."""
    data = {}
    for name in schema_cls.model_fields:
        value = getattr(row, name, None)
        if value is None:
            continue
        data[name] = float(value) if isinstance(value, Decimal) else value
    return schema_cls(**data)


def _apply_line_ops(db, entity: str, doc, ops: list) -> list:
    """Áp thao tác (đã theo id) lên danh sách dòng HIỆN TẠI, trả danh sách đầu vào cho
    service. Dòng nêu trong token mà nay không còn → 400, không đoán."""
    if entity == "purchase_request":
        from app.modules.purchase_request.schema import PRItemIn as line_cls
    else:
        from app.modules.survey_request.schema import SurveyRequestLineIn as line_cls
    rows = _current_lines(db, entity, doc.id)
    known = {r.id for r in rows}
    drop = {o["id"] for o in ops if o.get("op") == "remove"}
    qty = {o["id"]: o["qty"] for o in ops if o.get("op") == "set_qty"}
    if not (drop | set(qty)) <= known:
        raise HTTPException(400, "Dòng hàng trên phiếu đã đổi sau lúc đề xuất — nhờ trợ lý "
                                 "soạn lại đề xuất mới.")
    try:
        items = [_row_to_input(line_cls, r) for r in rows if r.id not in drop]
        for item in items:
            if item.id in qty:
                setattr(item, "qty" if entity == "purchase_request" else "request_qty", qty[item.id])
        for o in ops:
            if o.get("op") != "add":
                continue
            if entity == "purchase_request":
                #  Dòng mới lấy ngày cần hàng của đầu phiếu: `_save_items` đồng bộ ngược ngày
                #  sớm nhất của các dòng lên đầu phiếu, dòng trống ngày thì không kéo lệch.
                items.append(line_cls(product_name=o["name"], qty=o["qty"], unit=o["unit"],
                                      required_date=doc.need_date or ""))
            else:
                items.append(line_cls(requirement_detail=o["name"], request_qty=o["qty"],
                                      uom=o["unit"]))
    except ValidationError as e:
        raise HTTPException(400, "Phiếu có dòng dữ liệu cũ không hợp lệ nên trợ lý không sửa "
                                 "dòng được — mở form sửa tay.") from e
    if not items:
        raise HTTPException(400, "Phiếu phải còn ít nhất một dòng.")
    return items


def _check_ops_payload(raw) -> list:
    """Ops lấy từ token: kiểm lại hình dạng (token chỉ là đề xuất, không phải giấy thông hành)."""
    if raw is None:
        return []
    if not isinstance(raw, list) or len(raw) > MAX_LINE_OPS:
        raise HTTPException(400, "Đề xuất sửa dòng không hợp lệ.")
    clean = []
    for o in raw:
        kind = o.get("op") if isinstance(o, dict) else None
        if kind == "add" and _as_qty(o.get("qty")) and _clean_text(o.get("name"), 255):
            clean.append({"op": "add", "name": _clean_text(o.get("name"), 255),
                          "qty": _as_qty(o.get("qty")), "unit": _clean_text(o.get("unit"), 25)})
        elif kind == "remove" and isinstance(o.get("id"), int):
            clean.append({"op": "remove", "id": o["id"]})
        elif kind == "set_qty" and isinstance(o.get("id"), int) and _as_qty(o.get("qty")):
            clean.append({"op": "set_qty", "id": o["id"], "qty": _as_qty(o.get("qty"))})
        else:
            raise HTTPException(400, "Đề xuất sửa dòng không hợp lệ.")
    return clean


# ── Đơn nghỉ phép (AI-0006) ─────────────────────────────────────────────────────────────

def _check_leave_change(db, doc, fields: dict) -> tuple[dict, str | None]:
    """Kiểm khoảng ngày + loại nghỉ; trả {field: chữ hiện trên thẻ} cho loại nghỉ."""
    from app.modules.leave.request_service import lines_of
    start = date.fromisoformat(fields["from_date"]) if "from_date" in fields else doc.from_date
    end = date.fromisoformat(fields["to_date"]) if "to_date" in fields else doc.to_date
    if start and end and start > end:
        return {}, f"Từ ngày {start.isoformat()} sau đến ngày {end.isoformat()} — hỏi lại người dùng."
    shown: dict[str, str] = {}
    if "leave_type" in fields:
        found, rows = _find_leave_type(db, fields["leave_type"])
        if found is None:
            names = ", ".join(r.name for r in rows)
            return {}, f"Không có loại nghỉ «{fields['leave_type']}». Danh mục hiện có: {names}."
        if len(lines_of(db, doc.id)) > 1:
            return {}, ("Đơn này gồm nhiều loại nghỉ — đổi loại nghỉ phải mở form để chia lại "
                        "số ngày, trợ lý không tự chia.")
        fields["leave_type"] = found.code
        shown["leave_type"] = found.name
        if found.id == doc.leave_type_id:
            shown["leave_type"] = _leave_type_name(db, doc.leave_type_id)
    return shown, None


def _run_propose(ctx: ToolContext, args: dict) -> dict:
    entity = str(args.get("entity") or "").strip()
    rules = _ENTITY_RULES.get(entity)
    if rules is None:
        return {"error": "entity phải là purchase_request | survey_request | payment_request "
                         "| leave_request."}
    if not ctx.can(entity, "write"):
        return {"denied": True,
                "reason": f"Bạn không có quyền sửa {rules['label']} ({entity}.write)."}

    code = _clean_text(args.get("code"), 50).upper()
    if not code:
        return {"error": "Thiếu code — hỏi người dùng mã phiếu cần sửa."}
    doc = _fetch_by_code(ctx.db, entity, code, ctx.user, ctx.profile)
    if doc is None:
        return {"error": f"Không tìm thấy phiếu {code} trong phạm vi dữ liệu bạn được sửa."}

    status_error = _editable_error(entity, doc)
    if status_error:
        return {"error": status_error}

    raw_ops = args.get("line_ops")
    if raw_ops and not rules.get("lines"):
        return {"error": f"{rules['label']} không sửa dòng hàng qua trợ lý — chỉ YCMH và YCBG."}
    fields, clean_error = _clean_changes(entity, args.get("changes"), allow_empty=bool(raw_ops))
    if clean_error:
        return {"error": clean_error}
    shown: dict[str, str] = {}
    if entity == "leave_request" and fields:
        shown, leave_error = _check_leave_change(ctx.db, doc, fields)
        if leave_error:
            return {"error": leave_error}

    #  Giá trị mới trùng giá trị cũ thì bỏ — đề xuất "sửa mà không đổi gì" chỉ gây nhiễu.
    changes = []
    for field, new in fields.items():
        old = _old_value(ctx.db, entity, doc, field)
        new_text = shown.get(field, new)
        if new_text.strip() == old.strip():
            continue
        changes.append({"field": field, "label": rules["fields"][field],
                        "old": old, "new": new_text})
    kept = {c["field"] for c in changes}

    ops: list = []
    if raw_ops:
        ops, line_view, ops_error = _clean_line_ops(entity, raw_ops,
                                                    _current_lines(ctx.db, entity, doc.id))
        if ops_error:
            return {"error": ops_error}
        changes += line_view
    if not changes:
        return {"error": "Giá trị mới trùng giá trị hiện tại — không có gì để sửa, "
                         "xác nhận lại với người dùng."}

    payload = {"u": ctx.user.id, "e": entity, "id": doc.id,
               "ch": {k: v for k, v in fields.items() if k in kept},
               "s": _state_sig(ctx.db, entity, doc)}
    if ops:
        payload["ln"] = ops
    token = _fernet().encrypt(json.dumps(payload, ensure_ascii=False).encode()).decode()

    # Gói vào khóa `proposal` để tầng provider chuyển tiếp nguyên khối về FE
    # (giống khuôn `draft`/`file`) — FE dựng thẻ so sánh + nút 'Xác nhận sửa' từ đây.
    return {
        "status": "ready",
        "proposal": {
            "kind": "update_proposal",
            "entity": entity,
            "entity_label": rules["label"],
            "code": doc.code,
            "doc_status_label": _status_label(entity, doc),
            "changes": changes,
            "confirm_token": token,
            "url": _url_of(entity, doc.id),
        },
        "total": len(changes),
        "reminder": "Phiếu CHƯA bị sửa. Hãy tóm tắt các thay đổi (cũ → mới) và mời người "
                    "dùng bấm nút 'Xác nhận sửa' ngay dưới câu trả lời — chỉ khi họ bấm "
                    "thì hệ thống mới ghi. Đề xuất hết hạn sau 15 phút.",
    }


PROPOSE_DOCUMENT_UPDATE_SPEC = ToolSpec(
    name="propose_document_update",
    description=_DESC,
    parameters=_PARAMS,
    handler=_run_propose,
)


# ── propose_document_delete (AI-0006) ───────────────────────────────────────────────────
#
#  Đại ca chốt 09/10: bot được XÓA phiếu, với ĐỦ ba điều kiện — chính người hỏi lập, phiếu
#  còn Nháp / Bị trả lại, tài khoản có quyền `delete` và phiếu nằm trong phạm vi xóa. Phiếu
#  đã gửi duyệt (hay của người khác) thì KHÔNG xóa, trả link để người đó tự mở hoặc nhờ
#  người có quyền. Đề nghị thanh toán (dính tiền) và phiếu hỗ trợ (gửi đi ngay khi tạo, không
#  có trạng thái nháp, không có đường xóa) KHÔNG xóa qua trợ lý.

_DELETE_RULES: dict[str, str] = {
    "purchase_request": "Yêu cầu mua hàng (YCMH)",
    "survey_request": "Yêu cầu báo giá (YCBG)",
    "leave_request": "Đơn nghỉ phép",
    "work_task": "Công việc (Dự án)",
}
_NO_DELETE: dict[str, str] = {
    "payment_request": "Đề nghị thanh toán dính tiền nên trợ lý không xóa.",
    "ticket": "Phiếu hỗ trợ được gửi cho nhóm hỗ trợ ngay khi tạo (không có trạng thái Nháp) "
              "nên trợ lý không xóa.",
}
_ASK_OTHERS = "Mở phiếu để tự xử lý nếu bạn có quyền, hoặc liên hệ người có quyền cao hơn."

_DELETE_PARAMS = {
    "type": "object",
    "properties": {
        "entity": {
            "type": "string",
            "enum": [*_DELETE_RULES, *_NO_DELETE],
            "description": "Loại phiếu: purchase_request (YCMH) | survey_request (YCBG) | "
                           "leave_request (đơn nghỉ phép) | work_task (việc Dự án) | "
                           "payment_request (YCTT — không xóa được) | ticket (phiếu hỗ trợ — "
                           "không xóa được).",
        },
        "code": {
            "type": "string",
            "description": "Mã phiếu cần xóa (YCMH00012, YCBG00034, mã đơn nghỉ…). Việc Dự án "
                           "không có mã: điền id số của việc, hoặc đúng tên việc.",
        },
    },
    "required": ["entity", "code"],
}

_DELETE_DESC = (
    "ĐỀ XUẤT xóa một phiếu theo yêu cầu người dùng — KHÔNG xóa gì. Chỉ xóa được phiếu CHÍNH "
    "người hỏi lập, đang Nháp hoặc Bị trả lại (việc Dự án: việc mình tạo, chưa xong), và "
    "người hỏi có quyền xóa: YCMH, YCBG, đơn nghỉ phép, việc Dự án. Đề nghị thanh toán và "
    "phiếu hỗ trợ KHÔNG xóa qua trợ lý. Phiếu đã gửi duyệt / của người khác thì tool trả "
    "lỗi kèm `url` — đưa link đó cho người dùng tự mở hoặc nhờ người có quyền. Chỉ gọi khi "
    "người dùng nói rõ XÓA phiếu nào; «bỏ», «hủy» mơ hồ thì hỏi lại xóa hẳn hay hủy phiếu. "
    "Sau khi gọi, mời người dùng bấm 'Xác nhận xóa' dưới câu trả lời — nhấn mạnh phiếu "
    "CHƯA bị xóa cho tới khi họ bấm."
)


def _work_actor(db, user):
    from app.modules.work.membership_service import resolve_actor
    return resolve_actor(db, user)


def _find_work_task(db, actor, ref: str):
    """Việc Dự án theo id số hoặc ĐÚNG tên — chỉ trong các dự án người hỏi thấy được.
    Trả (task, lỗi). Trùng tên nhiều việc thì trả lỗi kèm danh sách, không tự chọn."""
    from sqlalchemy import func

    from app.modules.work.task_model import WorkTask
    from app.modules.work.task_service import get_task_or_403

    if ref.isdigit():
        candidates = [int(ref)]
    else:
        rows = (db.query(WorkTask.id).filter(func.lower(WorkTask.title) == ref.lower(),
                                             WorkTask.deleted_at.is_(None))
                .order_by(WorkTask.id).limit(20).all())
        candidates = [r.id for r in rows]
    found = []
    for task_id in candidates:
        try:
            found.append(get_task_or_403(db, actor, task_id))
        except HTTPException:
            continue
    if not found:
        return None, f"Không tìm thấy việc «{ref}» trong các dự án bạn tham gia."
    if len(found) > 1:
        options = "; ".join(f"#{t.id} {t.title}" for t in found)
        return None, f"Có nhiều việc tên «{ref}»: {options} — hỏi người dùng xóa việc số mấy."
    return found[0], None


def _delete_block(entity: str, doc, user, actor=None) -> tuple[int, str] | None:
    """(mã HTTP, lý do) nếu KHÔNG được xóa; None nếu đủ điều kiện. Dùng chung cho cả bước đề
    xuất lẫn bước xác nhận để hai bước không bao giờ lệch luật."""
    if entity == "work_task":
        from app.modules.work.model import WorkTaskStatus
        if not actor or not actor.employee_id or doc.creator_employee_id != actor.employee_id:
            return 403, f"Việc «{doc.title}» do người khác tạo — trợ lý chỉ xóa việc chính bạn tạo."
        if int(doc.status or 0) != int(WorkTaskStatus.OPEN):
            return 400, f"Việc «{doc.title}» đã xong hoặc đã hủy — trợ lý chỉ xóa việc đang mở."
        return None
    label = _status_label(entity, doc)
    if doc.created_by != user.id:
        return 403, f"Phiếu {doc.code} do người khác lập — trợ lý chỉ xóa phiếu chính bạn lập."
    ok = (int(doc.status or 0) in _LEAVE_EDITABLE if entity == "leave_request"
          else doc.status in _DRAFT_STATUSES)
    if not ok:
        return 400, (f"Phiếu {doc.code} đang ở trạng thái {label} (đã gửi duyệt hoặc đã xử lý) "
                     "nên trợ lý không xóa được — chỉ xóa phiếu Nháp hoặc Bị trả lại.")
    return None


def _run_propose_delete(ctx: ToolContext, args: dict) -> dict:
    entity = str(args.get("entity") or "").strip()
    ref = _clean_text(args.get("code"), 255)
    if entity in _NO_DELETE:
        out = {"error": _NO_DELETE[entity] + " " + _ASK_OTHERS}
        doc = (_fetch_by_code(ctx.db, entity, ref.upper(), ctx.user, ctx.profile, action="read")
               if ref and ctx.can(entity, "read") else None)
        if doc is not None:
            out["url"] = _url_of(entity, doc.id)
        return out
    label = _DELETE_RULES.get(entity)
    if label is None:
        return {"error": "entity phải là purchase_request | survey_request | leave_request | "
                         "work_task."}
    if not ctx.can(entity, "delete"):
        return {"denied": True, "reason": f"Bạn không có quyền xóa {label} ({entity}.delete)."}
    if not ref:
        return {"error": "Thiếu code — hỏi người dùng phiếu nào cần xóa."}

    actor = None
    if entity == "work_task":
        actor = _work_actor(ctx.db, ctx.user)
        if not actor.employee_id:
            return {"error": "Tài khoản chưa gắn hồ sơ nhân sự nên không có việc Dự án."}
        doc, find_error = _find_work_task(ctx.db, actor, ref)
        if find_error:
            return {"error": find_error}
        shown = f"#{doc.id} {doc.title}"
        status_label = "Đang mở" if int(doc.status or 0) == 1 else "Đã đóng"
    else:
        #  Tìm theo phạm vi ĐỌC để nói được "phiếu này không xóa được, link đây"; phạm vi XÓA
        #  kiểm riêng ngay dưới — ngoài phạm vi xóa thì cũng chỉ trả link.
        doc = _fetch_by_code(ctx.db, entity, ref.upper(), ctx.user, ctx.profile, action="read")
        if doc is None:
            return {"error": f"Không tìm thấy phiếu {ref.upper()} trong phạm vi dữ liệu của bạn."}
        shown = doc.code
        status_label = _status_label(entity, doc)

    url = _url_of(entity, doc.id)
    block = _delete_block(entity, doc, ctx.user, actor)
    if block:
        return {"error": f"{block[1]} {_ASK_OTHERS}", "url": url}
    if entity != "work_task" and get_scoped(ctx.db, _model_of(entity), entity, doc.id,
                                            ctx.user, ctx.profile, action="delete") is None:
        return {"error": f"Phiếu {doc.code} nằm ngoài phạm vi bạn được xóa. {_ASK_OTHERS}",
                "url": url}

    payload = {"u": ctx.user.id, "a": "delete", "e": entity, "id": doc.id}
    token = _fernet().encrypt(json.dumps(payload).encode()).decode()
    return {
        "status": "ready",
        "proposal": {
            "kind": "update_proposal",
            "action": "delete",
            "entity": entity,
            "entity_label": label,
            "code": shown,
            "doc_status_label": status_label,
            "changes": [{"field": "delete", "label": "Thao tác", "old": shown,
                         "new": "Xóa phiếu"}],
            "confirm_token": token,
            "url": url,
        },
        "total": 1,
        "reminder": "Phiếu CHƯA bị xóa. Mời người dùng bấm nút 'Xác nhận xóa' ngay dưới câu "
                    "trả lời — chỉ khi họ bấm thì hệ thống mới xóa. Đề xuất hết hạn sau 15 phút.",
    }


PROPOSE_DOCUMENT_DELETE_SPEC = ToolSpec(
    name="propose_document_delete",
    description=_DELETE_DESC,
    parameters=_DELETE_PARAMS,
    handler=_run_propose_delete,
)


# ── Bước 2: người dùng bấm Xác nhận — controller gọi hàm này ─────────────────────────────

def confirm_update(db, user, token: str) -> dict:
    """Ghi thay đổi SAU KHI người dùng bấm Xác nhận trên thẻ đề xuất.

    Kiểm lại toàn bộ từ đầu (token là đề xuất, không phải giấy thông hành):
    1. Token hợp lệ + còn hạn (Fernet TTL) + đúng CHÍNH người đã nhận đề xuất.
    2. Quyền `entity.write` tại thời điểm bấm (quyền có thể vừa bị thu hồi).
    3. Phiếu còn trong phạm vi GHI (get_scoped action=write) — ngoài phạm vi trả 404.
    4. Trạng thái còn sửa được + trường còn trong whitelist đợt này.
    Rồi ghi qua ĐÚNG service của form để validate + audit đi chung một đường với sửa tay.
    Token xóa (`a = delete`, AI-0006) rẽ sang `_confirm_delete` — cùng một nút, một endpoint.
    """
    try:
        payload = json.loads(_fernet().decrypt(token.encode(), ttl=CONFIRM_TTL_SECONDS))
    except (InvalidToken, ValueError, TypeError) as e:
        raise HTTPException(400, "Đề xuất sửa đã hết hạn hoặc không hợp lệ — nhờ trợ lý "
                                 "soạn lại đề xuất mới.") from e
    if not isinstance(payload, dict) or payload.get("u") != user.id:
        raise HTTPException(403, "Đề xuất sửa không thuộc về bạn.")
    if payload.get("a") == "delete":
        return _confirm_delete(db, user, payload)
    entity = payload.get("e")
    rules = _ENTITY_RULES.get(entity)
    if rules is None:
        raise HTTPException(403, "Đề xuất sửa không thuộc về bạn.")
    if not user_has_permission(db, user, entity, "write"):
        raise HTTPException(403, f"Bạn không có quyền sửa {rules['label']}.")

    profile = get_perm_profile(db, user)
    doc = get_scoped(db, _model_of(entity), entity, int(payload.get("id") or 0),
                     user, profile, action="write")
    if doc is None or _soft_deleted(entity, doc):
        raise HTTPException(404, "Không tìm thấy phiếu trong phạm vi dữ liệu bạn được sửa.")

    status_error = _editable_error(entity, doc)
    if status_error:
        raise HTTPException(400, status_error)

    ops = _check_ops_payload(payload.get("ln"))
    if ops and not rules.get("lines"):
        raise HTTPException(400, "Đề xuất sửa dòng không hợp lệ.")
    raw = payload.get("ch")
    fields, clean_error = _clean_changes(entity, raw if isinstance(raw, dict) else {},
                                         allow_empty=bool(ops))
    if clean_error:
        raise HTTPException(400, clean_error)
    if entity == "leave_request" and fields:
        _, leave_error = _check_leave_change(db, doc, fields)
        if leave_error:
            raise HTTPException(400, leave_error)
    if payload.get("s") != _state_sig(db, entity, doc):
        raise HTTPException(409, "Đề xuất này đã dùng rồi, hoặc phiếu đã đổi sau lúc đề xuất — nhờ trợ lý soạn lại "
                                 "đề xuất mới.")

    if entity == "purchase_request":
        from app.modules.purchase_request.schema import PRUpdate
        from app.modules.purchase_request.service import update_pr
        items = _apply_line_ops(db, entity, doc, ops) if ops else None
        update_pr(db, doc.id, PRUpdate(**fields, items=items) if ops else PRUpdate(**fields),
                  user.id)
    elif entity == "survey_request":
        from app.modules.survey_request.schema import SurveyRequestUpdate
        from app.modules.survey_request.service import update_sr
        lines = _apply_line_ops(db, entity, doc, ops) if ops else None
        data = SurveyRequestUpdate(**fields, lines=lines) if ops else SurveyRequestUpdate(**fields)
        update_sr(db, doc.id, data, user.id, user=user, profile=profile)
    elif entity == "leave_request":
        _update_leave(db, user, doc, fields)
    else:
        from app.modules.payment_request.schema import PRequestUpdate
        from app.modules.payment_request.service import parse_print_texts, update_request
        #  Gộp câu mới vào các câu hiện có — chỉ đè khóa người dùng đổi, giữ nguyên phần còn
        #  lại. Payload gói MỖI print_texts nên service cho sửa cả khi submitted/approved.
        merged = parse_print_texts(doc.print_texts)
        merged.update({_PRINT_KEY_MAP[k]: v for k, v in fields.items()})
        update_request(db, doc.id, PRequestUpdate(print_texts=merged), user.id)

    updated = [rules["fields"][f] for f in fields]
    if ops:
        updated.append("Dòng hàng")
    return {
        "entity": entity,
        "entity_label": rules["label"],
        "code": doc.code,
        "updated_fields": updated,
        "url": _url_of(entity, doc.id),
    }


def _update_leave(db, user, doc, fields: dict) -> None:
    """Sửa đơn nghỉ qua ĐÚNG `request_service.update` (kiểm ngày, giờ, quỹ, giới tính, trùng
    đơn) + dòng nhật ký như đường PATCH của màn hình."""
    from app.core.audit import record as audit_record
    from app.modules.leave import request_service
    from app.modules.leave.schema import LeaveRequestUpdate

    values: dict = {}
    if "from_date" in fields:
        values["from_date"] = date.fromisoformat(fields["from_date"])
    if "to_date" in fields:
        values["to_date"] = date.fromisoformat(fields["to_date"])
    if "leave_type" in fields:
        found, _ = _find_leave_type(db, fields["leave_type"])
        values["leave_type_id"] = found.id
    if "reason" in fields:
        values["reason"] = fields["reason"]
    if not values.keys() & {"from_date", "to_date", "leave_type_id"}:
        #  Chỉ sửa lý do: giữ đúng số ngày đang có. Không gửi `total_days` thì service tính lại từ khoảng ngày —
        #  đơn đã chỉnh tay số ngày sẽ bị đổi ngầm, tức sửa vào quỹ phép chỉ vì sửa một câu chữ.
        values["total_days"] = float(doc.total_days or 0)
    obj = request_service.update(db, doc, LeaveRequestUpdate(**values), user)
    audit_record(db, user.id, "leave_request", obj.id, "update", f"Sửa đơn nghỉ phép {obj.code}")


def _confirm_delete(db, user, payload: dict) -> dict:
    """Xóa SAU KHI người dùng bấm 'Xác nhận xóa' — kiểm lại quyền `delete`, phạm vi xóa,
    người lập, trạng thái rồi gọi ĐÚNG service xóa của form (xóa mềm ở YCMH / đơn nghỉ /
    việc Dự án; YCBG xóa hẳn như nút Xóa của màn hình)."""
    entity = payload.get("e")
    label = _DELETE_RULES.get(entity)
    if label is None:
        raise HTTPException(403, "Đề xuất xóa không hợp lệ.")
    if not user_has_permission(db, user, entity, "delete"):
        raise HTTPException(403, f"Bạn không có quyền xóa {label}.")
    doc_id = int(payload.get("id") or 0)

    if entity == "work_task":
        from app.modules.work.task_service import delete_task, get_task_or_403
        actor = _work_actor(db, user)
        doc = get_task_or_403(db, actor, doc_id)
        block = _delete_block(entity, doc, user, actor)
        if block:
            raise HTTPException(*block)
        shown = f"#{doc.id} {doc.title}"
        delete_task(db, actor, doc_id)
        return {"entity": entity, "entity_label": label, "code": shown,
                "updated_fields": ["Đã xóa (vào thùng rác của dự án)"], "deleted": True,
                "url": ""}

    profile = get_perm_profile(db, user)
    doc = get_scoped(db, _model_of(entity), entity, doc_id, user, profile, action="delete")
    if doc is None or _soft_deleted(entity, doc):
        raise HTTPException(404, "Không tìm thấy phiếu trong phạm vi bạn được xóa.")
    block = _delete_block(entity, doc, user)
    if block:
        raise HTTPException(*block)
    code = doc.code
    if entity == "purchase_request":
        from app.modules.purchase_request.service import delete_pr
        delete_pr(db, doc.id, user.id)
    elif entity == "survey_request":
        from app.modules.survey_request.service import delete_sr
        delete_sr(db, doc.id, user.id)
    else:
        from app.core.audit import record as audit_record
        from app.modules.leave import request_service
        request_service.soft_delete(db, doc, user)
        audit_record(db, user.id, "leave_request", doc_id, "delete", f"Xóa đơn nghỉ phép {code}")
    return {"entity": entity, "entity_label": label, "code": code,
            "updated_fields": ["Đã xóa phiếu"], "deleted": True, "url": ""}
