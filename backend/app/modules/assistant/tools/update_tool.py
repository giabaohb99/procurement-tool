"""Tool tầng GHI có xác nhận (CR-218): `propose_document_update` — CHỈ trả BẢN ĐỀ XUẤT sửa.

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
KHÔNG đụng dòng hàng — sửa dòng vẫn phải mở form.
"""
import base64
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException

from app.core.auth import get_perm_profile, user_has_permission
from app.core.config import settings as _env
from app.core.scoping import apply_scope, get_scoped

from .approval_tool import _detail_url
from .base import ToolContext, ToolSpec
from .draft_tool import _clean_text, _iso_date
from .procurement_doc_tool import _label

CONFIRM_TTL_SECONDS = 15 * 60   # đề xuất sửa chỉ sống 15 phút — quá hạn phải hỏi lại

#  Trạng thái còn sửa được — chép ĐÚNG luật của service từng form (update_pr / update_sr /
#  update_request), không nới thêm: YCTT chỉ mở vì payload gói mỗi print_texts (CR-149).
_DRAFT_STATUSES = ("draft", "rejected")
_PRINT_TEXT_STATUSES = ("draft", "submitted", "approved")

#  Khóa phẳng cho model (dễ điền hơn dict lồng nhau) — 3 khóa print_* map về print_texts.
_PRINT_KEY_MAP = {"print_content": "content", "print_line_desc": "line_desc",
                  "print_transfer": "transfer"}

_ENTITY_RULES: dict[str, dict] = {
    "purchase_request": {
        "label": "Yêu cầu mua hàng (YCMH)",
        "fields": {"purpose": "Mục đích mua hàng", "need_date": "Ngày cần hàng",
                   "note": "Ghi chú"},
    },
    "survey_request": {
        "label": "Yêu cầu báo giá (YCBG)",
        "fields": {"purpose": "Mục đích khảo sát", "note": "Ghi chú"},
    },
    "payment_request": {
        "label": "Yêu cầu thanh toán (YCTT)",
        "fields": {"print_content": "Câu Nội dung (bản in)",
                   "print_line_desc": "Câu Diễn giải bảng (bản in)",
                   "print_transfer": "Nội dung chuyển khoản (bản in)"},
    },
}

_PARAMS = {
    "type": "object",
    "properties": {
        "entity": {
            "type": "string",
            "enum": list(_ENTITY_RULES),
            "description": "Loại phiếu: purchase_request (YCMH) | survey_request (YCBG) | "
                           "payment_request (YCTT).",
        },
        "code": {
            "type": "string",
            "description": "Mã phiếu cần sửa, ví dụ YCMH00012 / YCBG00034 / YCTT00045.",
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
            },
        },
    },
    "required": ["entity", "code", "changes"],
}

_DESC = (
    "ĐỀ XUẤT sửa một phiếu ĐÃ CÓ theo yêu cầu người dùng — KHÔNG ghi gì vào phiếu. Tool trả "
    "về bản so sánh cũ → mới; giao diện hiện thẻ xác nhận và CHÍNH NGƯỜI DÙNG bấm nút "
    "'Xác nhận sửa' thì hệ thống mới ghi. Phạm vi đợt này CHỈ phần đầu phiếu: "
    "YCMH sửa được mục đích / ngày cần hàng / ghi chú; YCBG sửa được mục đích / ghi chú; "
    "YCTT sửa được 3 câu chữ bản in (kể cả khi phiếu đã gửi duyệt / đã duyệt). "
    "KHÔNG sửa được: dòng hàng, số tiền, nhà cung cấp, trạng thái, hạn chi — các phần đó "
    "phải mở form sửa tay, nói rõ cho người dùng. Chỉ điền vào changes đúng trường người "
    "dùng yêu cầu đổi với giá trị MỚI họ nêu — thiếu giá trị thì hỏi lại trước, CẤM tự bịa. "
    "Sau khi gọi, tóm tắt thay đổi và mời người dùng bấm nút 'Xác nhận sửa' dưới câu trả "
    "lời — nhấn mạnh phiếu CHƯA bị sửa cho tới khi họ bấm."
)


def _fernet() -> Fernet:
    #  Cùng cách suy khóa với app_settings: sha256(JWT_SECRET) — không thêm secret mới.
    key = base64.urlsafe_b64encode(hashlib.sha256(_env.JWT_SECRET.encode()).digest())
    return Fernet(key)


def _model_of(entity: str):
    if entity == "purchase_request":
        from app.modules.purchase_request.model import PurchaseRequest
        return PurchaseRequest
    if entity == "survey_request":
        from app.modules.survey_request.model import SurveyRequest
        return SurveyRequest
    from app.modules.payment_request.model import PaymentRequest
    return PaymentRequest


def _fetch_by_code(db, entity: str, code: str, user, profile):
    """Tìm phiếu theo mã TRONG phạm vi GHI của người hỏi — ngoài phạm vi coi như không có."""
    model = _model_of(entity)
    q = db.query(model).filter(model.code == code)
    if entity == "purchase_request":
        q = q.filter(model.is_deleted.is_(False))
    q = apply_scope(q, model, entity, user, profile, action="write")
    return q.first()


def _editable_error(entity: str, doc) -> str | None:
    """None nếu phiếu còn sửa được; ngược lại trả câu giải thích cho người dùng."""
    label = _label(entity, doc.status)
    if entity == "payment_request":
        if doc.status in _PRINT_TEXT_STATUSES:
            return None
        return (f"Phiếu {doc.code} đang ở trạng thái {label} — câu chữ bản in chỉ sửa được "
                "khi phiếu Nháp, Chờ duyệt hoặc Đã duyệt.")
    if doc.status in _DRAFT_STATUSES:
        return None
    return (f"Phiếu {doc.code} đang ở trạng thái {label} — chỉ sửa được khi phiếu ở "
            "trạng thái Nháp hoặc Bị trả lại.")


def _old_value(entity: str, doc, field: str) -> str:
    if field in _PRINT_KEY_MAP:
        from app.modules.payment_request.service import parse_print_texts
        return parse_print_texts(doc.print_texts).get(_PRINT_KEY_MAP[field], "")
    return str(getattr(doc, field, "") or "")


def _clean_changes(entity: str, raw: dict) -> tuple[dict, str | None]:
    """Lọc changes theo whitelist của entity + chuẩn hóa giá trị. Trả (fields, lỗi)."""
    rules = _ENTITY_RULES[entity]
    if not isinstance(raw, dict):
        return {}, "Thiếu changes — hỏi người dùng muốn sửa trường nào, giá trị mới là gì."
    fields: dict[str, str] = {}
    rejected = [k for k in raw if k not in rules["fields"]]
    for key in rules["fields"]:
        if key not in raw:
            continue
        if key == "need_date":
            value = _iso_date(raw.get(key))
            if value is None:
                return {}, "need_date sai định dạng — cần YYYY-MM-DD, hỏi lại người dùng."
        else:
            value = _clean_text(raw.get(key), 500)
        fields[key] = value
    if rejected:
        allowed = ", ".join(rules["fields"].values())
        return {}, (f"Trường {', '.join(rejected)} KHÔNG sửa được qua trợ lý với loại phiếu "
                    f"này (chỉ sửa được: {allowed}) — báo người dùng mở form sửa tay.")
    if not fields:
        return {}, "changes rỗng — hỏi người dùng muốn sửa trường nào, giá trị mới là gì."
    return fields, None


def _run_propose(ctx: ToolContext, args: dict) -> dict:
    entity = str(args.get("entity") or "").strip()
    rules = _ENTITY_RULES.get(entity)
    if rules is None:
        return {"error": "entity phải là purchase_request | survey_request | payment_request."}
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

    fields, clean_error = _clean_changes(entity, args.get("changes"))
    if clean_error:
        return {"error": clean_error}

    #  Giá trị mới trùng giá trị cũ thì bỏ — đề xuất "sửa mà không đổi gì" chỉ gây nhiễu.
    changes = []
    for field, new in fields.items():
        old = _old_value(entity, doc, field)
        if new.strip() == old.strip():
            continue
        changes.append({"field": field, "label": rules["fields"][field],
                        "old": old, "new": new})
    if not changes:
        return {"error": "Giá trị mới trùng giá trị hiện tại — không có gì để sửa, "
                         "xác nhận lại với người dùng."}

    payload = {"u": ctx.user.id, "e": entity, "id": doc.id,
               "ch": {c["field"]: c["new"] for c in changes}}
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
            "doc_status_label": _label(entity, doc.status),
            "changes": changes,
            "confirm_token": token,
            "url": _detail_url(entity, doc.id),
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


# ── Bước 2: người dùng bấm Xác nhận — controller gọi hàm này ─────────────────────────────

def confirm_update(db, user, token: str) -> dict:
    """Ghi thay đổi SAU KHI người dùng bấm Xác nhận trên thẻ đề xuất.

    Kiểm lại toàn bộ từ đầu (token là đề xuất, không phải giấy thông hành):
    1. Token hợp lệ + còn hạn (Fernet TTL) + đúng CHÍNH người đã nhận đề xuất.
    2. Quyền `entity.write` tại thời điểm bấm (quyền có thể vừa bị thu hồi).
    3. Phiếu còn trong phạm vi GHI (get_scoped action=write) — ngoài phạm vi trả 404.
    4. Trạng thái còn sửa được + trường còn trong whitelist đợt này.
    Rồi ghi qua ĐÚNG service của form để validate + audit đi chung một đường với sửa tay.
    """
    try:
        payload = json.loads(_fernet().decrypt(token.encode(), ttl=CONFIRM_TTL_SECONDS))
    except (InvalidToken, ValueError, TypeError) as e:
        raise HTTPException(400, "Đề xuất sửa đã hết hạn hoặc không hợp lệ — nhờ trợ lý "
                                 "soạn lại đề xuất mới.") from e
    entity = payload.get("e")
    rules = _ENTITY_RULES.get(entity)
    if rules is None or payload.get("u") != user.id:
        raise HTTPException(403, "Đề xuất sửa không thuộc về bạn.")
    if not user_has_permission(db, user, entity, "write"):
        raise HTTPException(403, f"Bạn không có quyền sửa {rules['label']}.")

    profile = get_perm_profile(db, user)
    doc = get_scoped(db, _model_of(entity), entity, int(payload.get("id") or 0),
                     user, profile, action="write")
    if doc is None or (entity == "purchase_request" and getattr(doc, "is_deleted", False)):
        raise HTTPException(404, "Không tìm thấy phiếu trong phạm vi dữ liệu bạn được sửa.")

    status_error = _editable_error(entity, doc)
    if status_error:
        raise HTTPException(400, status_error)

    raw = payload.get("ch")
    fields, clean_error = _clean_changes(entity, raw if isinstance(raw, dict) else {})
    if clean_error:
        raise HTTPException(400, clean_error)

    if entity == "purchase_request":
        from app.modules.purchase_request.schema import PRUpdate
        from app.modules.purchase_request.service import update_pr
        update_pr(db, doc.id, PRUpdate(**fields), user.id)
    elif entity == "survey_request":
        from app.modules.survey_request.schema import SurveyRequestUpdate
        from app.modules.survey_request.service import update_sr
        update_sr(db, doc.id, SurveyRequestUpdate(**fields), user.id,
                  user=user, profile=profile)
    else:
        from app.modules.payment_request.schema import PRequestUpdate
        from app.modules.payment_request.service import parse_print_texts, update_request
        #  Gộp câu mới vào các câu hiện có — chỉ đè khóa người dùng đổi, giữ nguyên phần còn
        #  lại. Payload gói MỖI print_texts nên service cho sửa cả khi submitted/approved.
        merged = parse_print_texts(doc.print_texts)
        merged.update({_PRINT_KEY_MAP[k]: v for k, v in fields.items()})
        update_request(db, doc.id, PRequestUpdate(print_texts=merged), user.id)

    return {
        "entity": entity,
        "entity_label": rules["label"],
        "code": doc.code,
        "updated_fields": [rules["fields"][f] for f in fields],
        "url": _detail_url(entity, doc.id),
    }
