"""Sổ thay đổi do bot ghi + HOÀN TÁC 24 giờ (ai-CR-182, phase 15.1 — đại ca chốt 13/10/2026).

Luật hoàn tác (kiểm lại TỪ ĐẦU lúc bấm, không tin dữ liệu cũ):
  - trong 24 giờ kể từ lúc ghi (`UNDO_WINDOW`), chưa hoàn tác, không phải dòng ghi việc hoàn tác;
  - chính người đã xác nhận, hoặc người quản lý bot AI (`agent_group.read`) — người hoàn tác dùng QUYỀN
    + PHẠM VI hiện tại của chính mình (`write` cho sửa / dùng lại, `delete` cho tạo / xóa);
  - phiếu còn tồn tại, còn Nháp / Bị trả lại (đã gửi duyệt thì KHÔNG hoàn tác), và dấu trạng thái hiện tại
    == `after_sig` lúc bot ghi — ai sửa chen vào là chặn;
  - gửi duyệt (SUBMIT) và lập bộ tài khoản (ACCOUNT) chỉ ghi sổ, không hoàn tác tự động.
Hoàn tác đi NGƯỢC qua ĐÚNG service của form (như nút Xác nhận sửa / xóa): sửa → ghi lại ảnh TRƯỚC;
tạo → xóa mềm; xóa → bỏ cờ xóa mềm (`restore_soft_deleted`); dùng lại nháp → đưa đầu phiếu + dòng về
ảnh TRƯỚC. Xong thì dòng gốc `undo_status = UNDONE`, ghi thêm MỘT dòng ngược trỏ `undo_of`, và một
dòng nhật ký ERP (`undo`).

Ghi sổ KHÔNG được làm hỏng đường ghi chính: `record_change` / `snapshot` / `state_sig` nuốt lỗi và ghi
log, trả về rỗng. Hợp đồng API cho bot Telegram và màn web: `doc/agent-hub/18-so-thay-doi-va-hoan-tac.md`.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime, time, timedelta

from fastapi import HTTPException
from pydantic import ValidationError

from app.core.audit import record as audit_record
from app.core.auth import get_perm_profile, user_has_permission
from app.core.scoping import scope_condition

from .change_model import (ACTION_LABELS, SOURCE_LABELS, UNDO_STATUS_LABELS, AssistantChange, ChangeAction,
                           ChangeSource, UndoStatus)

log = logging.getLogger("app.assistant.change")

UNDO_WINDOW = timedelta(hours=24)
MAX_JSON_BYTES = 64 * 1024          # trần mỗi cột before / after
LIST_MAX = 200
#  Quyền «quản lý bot AI»: xem sổ của mọi người + hoàn tác thay người khác.
MANAGER_PERM = ("agent_group", "read")

ENTITY_LABELS = {
    "purchase_request": "Yêu cầu mua hàng (YCMH)",
    "survey_request": "Yêu cầu báo giá (YCBG)",
    "leave_request": "Đơn nghỉ phép",
    "payment_request": "Yêu cầu thanh toán (YCTT)",
    "work_task": "Công việc (Dự án)",
    "ticket": "Phiếu hỗ trợ",
    "account_setup": "Bộ tài khoản",
    "ai_skill": "Skill AI",
    "ai_skill_access": "Quyền đọc skill AI",
}
#  bao-CR-634: thay đổi Kho skill AI do AI riêng ghi qua MCP — kiểm / làm ngược nằm ở chính phân hệ đó
#  (`ai_skill/mcp_admin.undo_check` + `undo_apply`), phiếu ở đây không có model chung để đi đường `_load_doc`.
EXTERNAL_UNDO = {"ai_skill": "app.modules.ai_skill.mcp_admin", "ai_skill_access": "app.modules.ai_skill.mcp_admin"}
#  Phiếu có model tra được qua `update_tool._model_of` (việc Dự án đi đường riêng).
DOC_ENTITIES = ("purchase_request", "survey_request", "leave_request", "payment_request", "ticket")
UNDOABLE_ACTIONS = (ChangeAction.CREATE, ChangeAction.UPDATE, ChangeAction.DELETE, ChangeAction.REUSE)
#  Hành động ghi vào dòng NGƯỢC khi hoàn tác.
REVERSE_ACTION = {ChangeAction.UPDATE: ChangeAction.UPDATE, ChangeAction.REUSE: ChangeAction.UPDATE,
                  ChangeAction.CREATE: ChangeAction.DELETE, ChangeAction.DELETE: ChangeAction.CREATE}


# ── Ảnh phiếu + dấu trạng thái ──────────────────────────────────────────────────────────

def _jsonable(value):
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def _size(data) -> int:
    return len(json.dumps(data, ensure_ascii=False).encode("utf-8"))


def _fit(data: dict | None) -> dict | None:
    """Ép ảnh dưới trần 64 KB: cắt bớt dòng (ghi `truncated: true`), cùng đường thì cắt chuỗi dài."""
    if data is None:
        return None
    data = _jsonable(data)
    if _size(data) <= MAX_JSON_BYTES:
        return data
    lines = data.get("lines")
    if isinstance(lines, list):
        while lines and _size(data) > MAX_JSON_BYTES:
            lines.pop()
        data["truncated"] = True
    if _size(data) > MAX_JSON_BYTES:
        data = {"truncated": True,
                "fields": {k: str(v)[:500] for k, v in (data.get("fields") or {}).items()}}
    return data


def _leave_full(db, doc) -> dict:
    """Ảnh ĐỦ của đơn nghỉ để ghi lại nguyên vẹn qua `request_service.update` (dòng loại nghỉ, buổi, giờ…)."""
    from app.modules.leave.request_periods import periods_of
    from app.modules.leave.request_service import lines_of

    iso = lambda v: v.isoformat() if v else None   # noqa: E731
    return {"lines": [{"leave_type_id": int(ln.leave_type_id or 0), "days": float(ln.days or 0)} for ln in lines_of(db, doc.id)],
            "from_date": iso(doc.from_date), "to_date": iso(doc.to_date),
            "from_session": int(doc.from_session or 1), "to_session": int(doc.to_session or 1),
            "from_time": iso(doc.from_time), "to_time": iso(doc.to_time),
            #  duoc-CR-683: từng khoảng ngày, hoàn tác ghi lại ĐÚNG các khoảng (không gộp thành bao ngoài).
            "periods": [{"from_date": iso(p.from_date), "to_date": iso(p.to_date),
                         "from_session": int(p.from_session or 1), "to_session": int(p.to_session or 1)}
                        for p in periods_of(db, doc)],
            "reason": doc.reason or "", "contact_phone": doc.contact_phone or "",
            "total_days": float(doc.total_days or 0)}


def _line_cls(entity: str):
    if entity == "purchase_request":
        from app.modules.purchase_request.schema import PRItemIn
        return PRItemIn
    from app.modules.survey_request.schema import SurveyRequestLineIn
    return SurveyRequestLineIn


def _line_dicts(db, entity: str, doc) -> list[dict]:
    """Dòng hàng đúng hình form gửi lên (có `id`) — ghi lại được qua `update_pr` / `update_sr`."""
    from .tools import update_tool as ut

    cls = _line_cls(entity)
    out = []
    for row in ut._current_lines(db, entity, doc.id):
        try:
            out.append(ut._row_to_input(cls, row).model_dump(mode="json"))
        except ValidationError:
            #  Dữ liệu cũ hỏng: vẫn ghi để ĐỌC được, nhưng hoàn tác sẽ từ chối (xem `_reverse_update`).
            out.append({"id": row.id, "partial": True, "name": ut._line_name(entity, row),
                        "qty": ut._line_qty(entity, row), "unit": ut._line_unit(entity, row)})
    return out


def _snapshot(db, entity: str, doc, fields: list[str] | None, lines: bool) -> dict:
    from .tools import update_tool as ut

    out: dict = {}
    rules = ut._ENTITY_RULES.get(entity)
    if rules is not None:
        keys = [f for f in (fields if fields is not None else list(rules["fields"])) if f in rules["fields"]]
        out["fields"] = {f: ut._old_value(db, entity, doc, f) for f in keys}
        if rules.get("lines") and lines:
            out["lines"] = _line_dicts(db, entity, doc)
        if entity == "leave_request":
            out["leave"] = _leave_full(db, doc)
        out["status"] = str(doc.status)
    elif entity == "work_task":
        out["fields"] = {"title": doc.title or "", "description": doc.description or "",
                         "start_date": doc.start_date or "", "due_date": doc.due_date or ""}
        out["status"] = int(doc.status or 0)
        out["list_id"] = int(doc.list_id or 0)
    elif entity == "ticket":
        out["fields"] = {"subject": doc.subject or "", "department": doc.department or "",
                         "priority": doc.priority or ""}
        out["status"] = str(doc.status or "")
    return _jsonable(out)


def snapshot(db, entity: str, doc, *, fields: list[str] | None = None, lines: bool = True) -> dict:
    """Ảnh phiếu để ghi sổ: `fields` = chỉ các khóa này (None = mọi ô sửa được), `lines` = kèm dòng hàng.
    Không bao giờ ném lỗi ra đường ghi chính."""
    try:
        return _snapshot(db, entity, doc, fields, lines)
    except Exception:  # noqa: BLE001 — ghi sổ không được làm hỏng việc ghi phiếu
        log.exception("assistant change: không chụp được ảnh %s #%s", entity, getattr(doc, "id", "?"))
        return {"error": "không chụp được ảnh phiếu"}


def _deleted(doc) -> bool:
    return bool(getattr(doc, "is_deleted", False)) or getattr(doc, "deleted_at", None) is not None


def state_sig(db, entity: str, doc) -> str:
    """Dấu trạng thái phiếu: mọi ô sửa được + dòng (`update_tool._state_sig`) + trạng thái + cờ xóa.
    Lệch dấu = có người sửa phiếu sau lúc bot ghi → không hoàn tác tự động."""
    try:
        from .tools import update_tool as ut

        if entity in ut._ENTITY_RULES:
            base = ut._state_sig(db, entity, doc)
            if entity == "leave_request":
                base += json.dumps(_leave_full(db, doc), sort_keys=True, ensure_ascii=False)
        else:
            base = json.dumps(_snapshot(db, entity, doc, None, False).get("fields"), sort_keys=True, ensure_ascii=False)
        raw = json.dumps({"b": base, "st": str(getattr(doc, "status", "")), "del": _deleted(doc)}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:40]
    except Exception:  # noqa: BLE001
        log.exception("assistant change: không tính được dấu %s #%s", entity, getattr(doc, "id", "?"))
        return ""


# ── Ghi sổ ──────────────────────────────────────────────────────────────────────────────

def record_change(db, user, *, entity: str, entity_id: int, doc_code: str, action: ChangeAction, summary: str,
                  before: dict | None, after: dict | None, after_sig: str, source: int = 0,
                  undo_of: int = 0) -> AssistantChange | None:
    """Thêm một dòng sổ (commit riêng, SAU khi phiếu đã ghi xong). Lỗi thì log + trả None, không ném."""
    try:
        row = AssistantChange(
            user_id=int(getattr(user, "id", 0) or 0), entity=(entity or "")[:50], entity_id=int(entity_id or 0),
            doc_code=(doc_code or "")[:50], action=int(action), summary=(summary or "")[:300],
            before=_fit(before), after=_fit(after), after_sig=(after_sig or "")[:64],
            source=int(source or 0), undo_of=int(undo_of or 0), created_at=datetime.utcnow(),
            created_by=int(getattr(user, "id", 0) or 0), updated_by=int(getattr(user, "id", 0) or 0))
        db.add(row)
        db.commit()
        return row
    except Exception:  # noqa: BLE001 — ghi sổ không được làm hỏng đường ghi chính
        log.exception("assistant change: không ghi được sổ thay đổi %s #%s", entity, entity_id)
        db.rollback()
        return None


# ── Đọc sổ ──────────────────────────────────────────────────────────────────────────────

def is_manager(db, user) -> bool:
    return user_has_permission(db, user, *MANAGER_PERM)


def url_of(entity: str, entity_id: int) -> str:
    try:
        if entity == "account_setup":
            from .tools.account_setup_tool import USER_PERMISSION_URL
            return USER_PERMISSION_URL.format(user_id=entity_id)
        if entity == "ai_skill":
            return f"/ai-skill/skills/{entity_id}"
        if entity == "ai_skill_access":
            return f"/ai-skill/sets/{entity_id}?tab=access"
        if entity in DOC_ENTITIES or entity == "work_task":
            from .tools.update_tool import _url_of
            return _url_of(entity, entity_id)
    except Exception:  # noqa: BLE001
        log.exception("assistant change: không dựng được url %s #%s", entity, entity_id)
    return ""


def user_name_of(db, user_id: int) -> str:
    """ai-CR-185: tên hiện trên cột «Người» của màn web (chế độ xem mọi người): họ tên nhân sự, không có thì email, không
    có nữa thì #id. Không có giá trị bí mật nào."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    u = db.get(User, int(user_id or 0)) if user_id else None
    if u is None:
        return f"#{int(user_id or 0)}"
    emp = db.get(Employee, u.employee_id) if getattr(u, "employee_id", 0) else None
    if emp is not None and (emp.full_name or "").strip():
        return emp.full_name.strip()
    return (getattr(u, "email", "") or "").strip() or f"#{u.id}"


def serialize(db, user, row: AssistantChange, *, detail: bool = False) -> dict:
    ok, reason = can_undo(db, user, row)
    action = int(row.action or 0)
    out = {
        "id": int(row.id), "when": row.created_at.isoformat() if row.created_at else "",
        "user_id": int(row.user_id or 0), "user_name": user_name_of(db, int(row.user_id or 0)),
        "entity": row.entity, "entity_label": ENTITY_LABELS.get(row.entity, row.entity),
        "doc_code": row.doc_code or "", "entity_id": int(row.entity_id or 0),
        "action": action, "action_label": ACTION_LABELS.get(action, str(action)),
        "summary": row.summary or "",
        "source": int(row.source or 0), "source_label": SOURCE_LABELS.get(int(row.source or 0), ""),
        "undo_status": int(row.undo_status or 0),
        "undo_status_label": UNDO_STATUS_LABELS.get(int(row.undo_status or 0), ""),
        "undo_of": int(row.undo_of or 0),
        "can_undo": ok, "undo_reason": reason,
        "url": url_of(row.entity, int(row.entity_id or 0)),
    }
    if detail:
        out["before"] = row.before
        out["after"] = row.after
        out["undone_at"] = row.undone_at.isoformat() if row.undone_at else ""
        out["undone_by"] = int(row.undone_by or 0)
    return out


def list_for(db, user, *, limit: int = 50, all_users: bool = False) -> list[dict]:
    """Sổ của CHÍNH người này; `all_users` = của mọi người, chỉ cho người quản lý bot AI."""
    if all_users and not is_manager(db, user):
        raise HTTPException(403, "Chỉ người quản lý bot AI (quyền agent_group.read) mới xem được sổ của mọi người.")
    q = db.query(AssistantChange)
    if not all_users:
        q = q.filter(AssistantChange.user_id == int(user.id))
    rows = q.order_by(AssistantChange.id.desc()).limit(max(1, min(int(limit or 50), LIST_MAX))).all()
    return [serialize(db, user, r) for r in rows]


def get_for(db, user, change_id: int) -> AssistantChange | None:
    """Một dòng sổ — của mình, hoặc bất kỳ ai nếu là người quản lý bot AI; ngoài ra coi như không có."""
    row = db.get(AssistantChange, int(change_id or 0)) if change_id else None
    if row is None:
        return None
    if row.user_id != int(user.id) and not is_manager(db, user):
        return None
    return row


# ── Hoàn tác ────────────────────────────────────────────────────────────────────────────

def _needed_action(action: ChangeAction, entity: str) -> str:
    if action in (ChangeAction.UPDATE, ChangeAction.REUSE):
        return "write"
    if action == ChangeAction.CREATE and entity == "ticket":
        return "write"          # phiếu hỗ trợ không xóa — đóng lại
    return "delete"


def _load_doc(db, user, row: AssistantChange, action: ChangeAction):
    """Phiếu theo PHẠM VI hiện tại của người bấm (kể cả đã xóa mềm — hoàn tác xóa cần tới nó).
    Trả (doc, câu lỗi)."""
    from .tools import update_tool as ut

    model = ut._model_of(row.entity)
    cond = scope_condition(model, row.entity, user, get_perm_profile(db, user), _needed_action(action, row.entity))
    q = db.query(model).filter(model.id == int(row.entity_id or 0))
    if cond is not None:
        q = q.filter(cond)
    doc = q.first()
    if doc is None:
        return None, "Phiếu không còn, hoặc nằm ngoài phạm vi dữ liệu bạn được thao tác."
    if action == ChangeAction.DELETE and not _deleted(doc):
        return None, "Phiếu đã được khôi phục rồi."
    if action != ChangeAction.DELETE and _deleted(doc):
        return None, "Phiếu đã bị xóa."
    return doc, ""


def _load_task(db, user, row: AssistantChange, action: ChangeAction):
    from app.modules.work.membership_service import CAN_EDIT, get_list_or_403, resolve_actor
    from app.modules.work.task_model import WorkTask

    t = db.get(WorkTask, int(row.entity_id or 0))
    if t is None:
        return None, "Việc không còn."
    actor = resolve_actor(db, user)
    try:
        get_list_or_403(db, actor, t.list_id, CAN_EDIT)
    except HTTPException:
        return None, "Bạn không còn quyền sửa trên dự án chứa việc này."
    if action == ChangeAction.DELETE and t.deleted_at is None:
        return None, "Việc đã được khôi phục rồi."
    if action != ChangeAction.DELETE and t.deleted_at is not None:
        return None, "Việc đã bị xóa."
    return t, ""


def _status_block(entity: str, doc, action: ChangeAction) -> str:
    """Phiếu đã gửi duyệt / đã xử lý thì không hoàn tác (đại ca chốt 13/10). Phiếu đã xóa thì bỏ qua —
    lúc xóa nó còn nháp, và dấu `after_sig` đã khóa trạng thái đó."""
    if action == ChangeAction.DELETE:
        return ""
    if entity in ("purchase_request", "survey_request"):
        ok = doc.status in ("draft", "rejected")
    elif entity == "payment_request":
        ok = doc.status == "draft"
    elif entity == "leave_request":
        from app.modules.leave.constants import EDITABLE_STATUSES
        ok = int(doc.status or 0) in EDITABLE_STATUSES
    elif entity == "work_task":
        from app.modules.work.model import WorkTaskStatus
        ok = int(doc.status or 0) == int(WorkTaskStatus.OPEN)
    elif entity == "ticket":
        ok = (doc.status or "") != "closed"
    else:
        ok = False
    return "" if ok else "Phiếu đã gửi duyệt hoặc đã xử lý — không hoàn tác được, chỉ sửa bằng tay trên ERP."


def _check_undo(db, user, row: AssistantChange):
    """Trả (ok, lý do, mã HTTP, chặn hẳn?, doc). `chặn hẳn` = lý do nằm ở phiếu (đổi / gửi duyệt / mất),
    ghi `undo_status = BLOCKED` để màn danh sách khỏi hỏi lại."""
    label = ENTITY_LABELS.get(row.entity, row.entity)
    if row.undo_of:
        return False, "Đây là dòng ghi việc hoàn tác — không hoàn tác lại.", 400, False, None
    if int(row.undo_status or 0) == int(UndoStatus.UNDONE):
        return False, "Thay đổi này đã được hoàn tác rồi.", 409, False, None
    try:
        action = ChangeAction(int(row.action or 0))
    except ValueError:
        action = None
    if action == ChangeAction.SUBMIT:
        return False, "Phiếu đã gửi duyệt — muốn lấy lại thì rút hoặc trả về bằng tay trên ERP.", 400, False, None
    if action == ChangeAction.ACCOUNT:
        return False, "Lập bộ tài khoản không hoàn tác tự động — sửa tay ở màn Phân quyền.", 400, False, None
    if action == ChangeAction.PUBLISH:
        return False, ("Xuất bản tạo phiên bản mới, không hoàn tác — muốn quay lại thì sửa nháp rồi xuất bản lại."), 400,             False, None
    if action not in UNDOABLE_ACTIONS:
        return False, "Loại thay đổi này không hoàn tác được.", 400, False, None
    if row.created_at and datetime.utcnow() - row.created_at > UNDO_WINDOW:
        return False, "Đã quá hạn 24 giờ kể từ lúc bot ghi.", 400, False, None
    if row.user_id != int(user.id) and not is_manager(db, user):
        return False, ("Thay đổi này do người khác xác nhận — chỉ chính người đó hoặc người quản lý bot AI "
                       "hoàn tác được."), 403, False, None
    if row.entity in EXTERNAL_UNDO:
        err = _external_undo(row.entity).undo_check(db, user, row, action)
        return (False, err, 409, True, None) if err else (True, "", 200, False, None)
    need = _needed_action(action, row.entity)
    if not user_has_permission(db, user, row.entity, need):
        return False, f"Bạn không còn quyền {need} trên {label}.", 403, False, None
    if row.entity == "work_task":
        doc, err = _load_task(db, user, row, action)
    elif row.entity in DOC_ENTITIES:
        doc, err = _load_doc(db, user, row, action)
    else:
        doc, err = None, "Loại phiếu này không hoàn tác được."
    if err:
        return False, err, 409, True, None
    err = _status_block(row.entity, doc, action)
    if err:
        return False, err, 409, True, doc
    if state_sig(db, row.entity, doc) != (row.after_sig or ""):
        return False, ("Phiếu đã được sửa sau lúc bot ghi (không qua trợ lý) — không hoàn tác tự động, "
                       "mở phiếu sửa tay."), 409, True, doc
    return True, "", 200, False, doc


def _external_undo(entity: str):
    import importlib

    return importlib.import_module(EXTERNAL_UNDO[entity])


def can_undo(db, user, row: AssistantChange) -> tuple[bool, str]:
    """(được không, lý do) — kiểm từ đầu theo luật ở đầu tệp; không đổi gì trong sổ."""
    try:
        ok, reason, _status, _permanent, _doc = _check_undo(db, user, row)
    except Exception:  # noqa: BLE001 — một dòng hỏng không được làm đỏ cả danh sách
        log.exception("assistant change: kiểm hoàn tác dòng #%s hỏng", row.id)
        return False, "Không kiểm được trạng thái phiếu."
    return ok, reason


def restore_soft_deleted(db, entity: str, doc, user) -> None:
    """Bỏ cờ xóa mềm (`is_deleted` + `deleted_at` + `deleted_by`, hoặc `deleted_at` của việc Dự án —
    kèm việc con chết theo cha), ghi nhật ký `restore`. Dùng chung cho mọi loại phiếu."""
    code = getattr(doc, "code", None) or f"#{doc.id}"
    uid = int(getattr(user, "id", 0) or 0)
    if hasattr(doc, "is_deleted"):
        doc.is_deleted = False
        if hasattr(doc, "deleted_at"):
            doc.deleted_at = None
        if hasattr(doc, "deleted_by"):
            doc.deleted_by = 0
    elif getattr(doc, "deleted_at", None) is not None:
        stamp = doc.deleted_at
        doc.deleted_at = None
        if entity == "work_task":
            from app.modules.work.task_model import WorkTask
            (db.query(WorkTask).filter(WorkTask.parent_id == doc.id, WorkTask.deleted_at == stamp)
             .update({WorkTask.deleted_at: None}, synchronize_session=False))
    else:
        raise HTTPException(409, "Phiếu này không ở trạng thái đã xóa.")
    if hasattr(doc, "updated_by"):
        doc.updated_by = uid
    db.commit()
    audit_record(db, uid, entity, int(doc.id), "restore", f"Khôi phục {code} (hoàn tác xóa qua Trợ lý AI)",
                 doc_code=code if getattr(doc, "code", None) else "")


def _restore_leave(db, user, doc, full: dict) -> None:
    from app.modules.leave import request_service
    from app.modules.leave.schema import LeaveLineItem, LeavePeriodItem, LeaveRequestUpdate

    as_time = lambda v: time.fromisoformat(v) if v else None   # noqa: E731
    lines = [LeaveLineItem(leave_type_id=int(ln.get("leave_type_id") or 0), days=float(ln.get("days") or 0))
             for ln in full.get("lines") or []]
    #  Luôn gửi `periods` tường minh: đơn đang ≥2 khoảng mà chỉ gửi from/to thì service chặn (R11),
    #  còn nếu cho qua thì gộp nhầm thành một khoảng liền. Ảnh cũ (trước CR-683) không có khóa → 1 khoảng.
    raw_periods = full.get("periods") or [
        {k: full.get(k) for k in ("from_date", "to_date", "from_session", "to_session")}]
    periods = [LeavePeriodItem(
        from_date=date.fromisoformat(pr["from_date"]), to_date=date.fromisoformat(pr["to_date"]),
        from_session=int(pr.get("from_session") or 1), to_session=int(pr.get("to_session") or 1))
        for pr in raw_periods]
    data = LeaveRequestUpdate(
        lines=lines or None, periods=periods,
        from_date=date.fromisoformat(full["from_date"]), to_date=date.fromisoformat(full["to_date"]),
        from_session=int(full.get("from_session") or 1), to_session=int(full.get("to_session") or 1),
        from_time=as_time(full.get("from_time")), to_time=as_time(full.get("to_time")),
        reason=str(full.get("reason") or "")[:1000], contact_phone=str(full.get("contact_phone") or "")[:30])
    request_service.update(db, doc, data, user)
    audit_record(db, user.id, "leave_request", doc.id, "update", f"Hoàn tác sửa đơn nghỉ phép {doc.code} (Trợ lý AI)")


def _reverse_update(db, user, entity: str, doc, before: dict) -> None:
    """Ghi lại ảnh TRƯỚC qua `update_tool.write_doc` — cùng đường với nút Xác nhận sửa."""
    from .tools import update_tool as ut

    if entity == "leave_request" and before.get("leave"):
        _restore_leave(db, user, doc, before["leave"])
        return
    fields = dict(before.get("fields") or {})
    rules = ut._ENTITY_RULES.get(entity) or {"fields": {}}
    fields = {k: v for k, v in fields.items() if k in rules["fields"]}
    lines = None
    if before.get("lines") is not None:
        if before.get("truncated") or any(ln.get("partial") for ln in before["lines"] if isinstance(ln, dict)):
            raise HTTPException(409, "Ảnh dòng hàng trước đó bị cắt bớt hoặc không hợp lệ — không hoàn tác tự động, "
                                     "mở phiếu sửa tay.")
        try:
            lines = [_line_cls(entity)(**ln) for ln in before["lines"]]
        except (ValidationError, TypeError) as e:
            raise HTTPException(409, "Ảnh dòng hàng trước đó không đọc được — mở phiếu sửa tay.") from e
    if not fields and lines is None:
        raise HTTPException(409, "Dòng sổ này không có ảnh trước để ghi lại.")
    ut.write_doc(db, user, get_perm_profile(db, user), entity, doc, fields, lines)


def _reverse_create(db, user, entity: str, doc) -> None:
    """Tạo → xóa mềm qua đúng hàm xóa của form; phiếu hỗ trợ không xóa được thì đóng + ghi chú."""
    if entity == "work_task":
        from app.modules.work.membership_service import resolve_actor
        from app.modules.work.task_service import delete_task
        delete_task(db, resolve_actor(db, user), int(doc.id))
        return
    if entity == "ticket":
        from app.modules.ticket import service as ticket_service
        ticket_service.add_message(db, int(doc.id), "Hoàn tác tạo phiếu qua Trợ lý AI — đóng phiếu.", user.id,
                                   is_staff=False)
        ticket_service.set_status(db, int(doc.id), "closed", user.id)
        return
    from .tools.update_tool import delete_doc
    delete_doc(db, user, entity, doc)


def undo(db, user, change_id: int, source: int = 0) -> dict:
    """Hoàn tác MỘT dòng sổ. Kiểm lại từ đầu (quyền, phạm vi, trạng thái, dấu) rồi làm ngược qua đúng service."""
    row = get_for(db, user, change_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy dòng thay đổi này.")
    ok, reason, status, permanent, doc = _check_undo(db, user, row)
    if not ok:
        if permanent and int(row.undo_status or 0) == int(UndoStatus.NONE):
            row.undo_status = int(UndoStatus.BLOCKED)
            db.commit()
        raise HTTPException(status, reason)
    entity, action = row.entity, ChangeAction(int(row.action))
    external = _external_undo(entity) if entity in EXTERNAL_UNDO else None
    try:
        if external is not None:
            new_sig = external.undo_apply(db, user, row, action)
        elif action in (ChangeAction.UPDATE, ChangeAction.REUSE):
            _reverse_update(db, user, entity, doc, row.before or {})
        elif action == ChangeAction.CREATE:
            _reverse_create(db, user, entity, doc)
        else:
            restore_soft_deleted(db, entity, doc, user)
    except HTTPException:
        db.rollback()
        raise
    if external is None:
        db.refresh(doc)
        new_sig = state_sig(db, entity, doc)
    now = datetime.utcnow()
    row.undo_status = int(UndoStatus.UNDONE)
    row.undone_at = now
    row.undone_by = int(user.id)
    row.updated_by = int(user.id)
    db.commit()
    reverse = REVERSE_ACTION[action]
    summary = f"Hoàn tác: {row.summary}"[:300]
    new = record_change(db, user, entity=entity, entity_id=row.entity_id, doc_code=row.doc_code, action=reverse,
                        summary=summary, before=row.after, after=None if action == ChangeAction.CREATE else row.before,
                        after_sig=new_sig, source=source, undo_of=row.id)
    audit_record(db, user.id, entity, int(row.entity_id or 0), "undo",
                 f"Hoàn tác thay đổi #{row.id} của Trợ lý AI: {row.summary}"[:1000], doc_code=row.doc_code or "")
    return {
        "id": int(new.id) if new is not None else 0, "undo_of": int(row.id),
        "entity": entity, "entity_label": ENTITY_LABELS.get(entity, entity), "doc_code": row.doc_code or "",
        "action": int(reverse), "action_label": ACTION_LABELS.get(reverse, ""), "summary": summary,
        "url": url_of(entity, int(row.entity_id or 0)),
    }


__all__ = ["ChangeAction", "ChangeSource", "UndoStatus", "UNDO_WINDOW", "record_change", "snapshot", "state_sig",
           "list_for", "get_for", "can_undo", "undo", "restore_soft_deleted", "serialize", "is_manager", "url_of"]
