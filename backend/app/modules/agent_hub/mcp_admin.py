"""Quản trị BẰNG LỜI qua cổng MCP (bao-CR-634, K9 — doc/erp/21 §7.2 đợt P7): năm tool cho AI riêng của người quản trị.

  draft_skill · draft_skill_publish · draft_skill_access — Kho skill (dữ liệu ở ERP, `ai_skill/mcp_admin.py`)
  draft_key_issue · draft_key_revoke                     — khóa AI của nhân sự (bảng ở dịch vụ AI, `key_admin_ops.py`)

Luật chung (đúng khuôn nháp → `confirm_draft` của cổng):
  - Chỉ khóa ĐƯỢC GHI thấy và gọi được; còn phải có quyền tương ứng (`TOOL_PERMS`) — thiếu thì tool không liệt kê, gọi
    thẳng bị từ chối. Nhóm `admin` của màn Cấu hình (G7) tắt thì cũng không liệt kê.
  - Tool draft_* KHÔNG ghi gì: trả bản xem trước + `draft` mang token (Fernet, hết hạn, buộc đúng người và đúng loại việc,
    kèm dấu trạng thái lúc soạn). Ghi chỉ xảy ra ở `confirm_draft` với đúng bản nháp đó — quyền + phạm vi kiểm LẠI, đích
    đổi sau lúc soạn (hoặc bản nháp đã dùng rồi) → từ chối. Thu hồi / gỡ quyền vì vậy luôn có một bước xác nhận tường minh.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings

from . import key_admin_ops, mcp_keys

log = logging.getLogger("app.agent_hub.mcp_admin")

TOKEN_TTL = 30 * 60
SUBJECT_SCHEMA = {"type": "object", "properties": {
    "kind": {"type": "string", "enum": ["employee", "department", "company", "role", "position", "job_level"]},
    "ref": {"type": "string", "maxLength": 150, "description": "Mã hoặc tên (nhân sự: mã NV hoặc họ tên)."}},
    "required": ["kind", "ref"]}
PEOPLE_SCHEMA = {"type": "array", "maxItems": 50, "items": {"type": "string", "maxLength": 150},
                 "description": "Mã nhân sự hoặc họ tên (tra bằng employee_lookup nếu chưa chắc)."}
NOTE = ("CHỈ trả bản xem trước, chưa ghi gì. Đưa người dùng đọc; họ đồng ý thì gọi confirm_draft với kind trong kết quả "
        "và đúng object `draft`.")
TOOL_DEFS = [
    {"name": "draft_skill",
     "description": ("Soạn tạo mới hoặc sửa BẢN NHÁP một skill trong Kho skill AI (tên gọi, tiêu đề, tóm tắt cho AI, nội "
                     "dung Markdown). Trùng tên trong bộ thì là sửa, chỉ gửi trường cần đổi. AI của nhân sự chỉ đọc bản mới "
                     "sau khi xuất bản (draft_skill_publish). " + NOTE),
     "inputSchema": {"type": "object", "properties": {
         "skill_set": {"type": "string", "maxLength": 150, "description": "Mã hoặc tên bộ skill."},
         "name": {"type": "string", "maxLength": 160, "description": "Tên gọi skill (chữ không dấu, số, -, _) hoặc MÃ-BỘ/tên."},
         "title": {"type": "string", "maxLength": 200}, "summary": {"type": "string", "maxLength": 500},
         "body_md": {"type": "string", "maxLength": 200000}}, "required": ["name"]}},
    {"name": "draft_skill_publish",
     "description": ("Soạn lệnh XUẤT BẢN bản nháp hiện tại của một skill thành phiên bản mới (kèm so sánh với bản đang dùng). "
                     "Cần quyền duyệt trên bộ. " + NOTE),
     "inputSchema": {"type": "object", "properties": {
         "name": {"type": "string", "maxLength": 160}, "skill_set": {"type": "string", "maxLength": 150},
         "change_note": {"type": "string", "maxLength": 500}}, "required": ["name"]}},
    {"name": "draft_skill_access",
     "description": ("Soạn GÁN (grant) hoặc THU HỒI (revoke) quyền ĐỌC một bộ skill, hoặc một skill lẻ nếu có `name`, cho người "
                     "/ phòng ban / pháp nhân / vai trò / chức vụ / cấp bậc. effect=deny là CẤM (cấm thắng cho phép). " + NOTE),
     "inputSchema": {"type": "object", "properties": {
         "action": {"type": "string", "enum": ["grant", "revoke"], "default": "grant"},
         "skill_set": {"type": "string", "maxLength": 150}, "name": {"type": "string", "maxLength": 160},
         "subjects": {"type": "array", "maxItems": 200, "items": SUBJECT_SCHEMA},
         "effect": {"type": "string", "enum": ["allow", "deny"], "default": "allow"},
         "include_children": {"type": "boolean", "default": True, "description": "Phòng ban: kể cả phòng con."},
         "valid_to": {"type": "string", "description": "Hết hạn YYYY-MM-DD, bỏ trống = không hạn."},
         "reason": {"type": "string", "maxLength": 500}}, "required": ["skill_set", "subjects"]}},
    {"name": "draft_key_issue",
     "description": ("Soạn lệnh PHÁT HỘ khóa kết nối AI (chỉ đọc, chờ người nhận bấm Nhận khóa) cho từng nhân sự hoặc cả "
                     f"phòng, tối đa {mcp_keys.BATCH_MAX} người. Người đã đủ khóa còn hiệu lực sẽ bị bỏ qua. " + NOTE),
     "inputSchema": {"type": "object", "properties": {
         "employees": PEOPLE_SCHEMA, "department": {"type": "string", "maxLength": 150},
         "days": {"type": "integer", "enum": list(mcp_keys.ISSUE_DAYS), "default": 90},
         "name": {"type": "string", "maxLength": 80}}}},
    {"name": "draft_key_revoke",
     "description": ("Soạn lệnh THU HỒI khóa kết nối AI của nhân sự (mọi khóa còn hiệu lực của những người này, các khóa theo "
                     "id, hoặc cả một lượt phát). Thu hồi xong ứng dụng AI của họ mất kết nối ngay. " + NOTE),
     "inputSchema": {"type": "object", "properties": {
         "employees": PEOPLE_SCHEMA, "key_ids": {"type": "array", "maxItems": 50, "items": {"type": "integer"}},
         "batch_id": {"type": "string", "maxLength": 32}}}},
]
TOOL_NAMES = frozenset(d["name"] for d in TOOL_DEFS)
#  Quyền phải có (ngoài khóa được ghi) để thấy / gọi từng tool.
TOOL_PERMS = {
    "draft_skill": ("ai_skill", "write"),
    "draft_skill_publish": ("ai_skill", "approve"),
    "draft_skill_access": ("ai_skill", "write"),
    "draft_key_issue": ("ai_mcp_key_admin", "create"),
    "draft_key_revoke": ("ai_mcp_key_admin", "delete"),
}
#  kind của confirm_draft ↔ tool soạn ra nó.
KIND_TOOL = {"skill": "draft_skill", "skill_publish": "draft_skill_publish", "skill_access": "draft_skill_access",
             "key_issue": "draft_key_issue", "key_revoke": "draft_key_revoke"}
SKILL_KINDS = frozenset({"skill", "skill_publish", "skill_access"})
KEY_KINDS = frozenset({"key_issue", "key_revoke"})


class KeyDraftError(Exception):
    pass


def _is_allowed(db: Session, user, tool: str) -> bool:
    """Có quyền dùng tool không — tra quyền hỏng (ERP không trả lời…) thì coi như KHÔNG (đóng chứ không mở)."""
    from . import erp

    entity, action = TOOL_PERMS[tool]
    try:
        return bool(erp.can(db, user, entity, action))
    except Exception:  # noqa: BLE001
        log.warning("mcp_admin: không tra được quyền %s.%s", entity, action, exc_info=True)
        return False


def list_defs(db: Session, user, scope: int) -> list[dict]:
    """Tool quản trị khóa này được thấy — rỗng với khóa chỉ đọc / người không có quyền / nhóm `admin` đang tắt."""
    from . import mcp_settings

    if scope != mcp_keys.SCOPE_WRITE:
        return []
    return [d for d in TOOL_DEFS if mcp_settings.tool_listed(db, d["name"]) and _is_allowed(db, user, d["name"])]


def _deny(tool: str, scope: int) -> dict | None:
    if scope != mcp_keys.SCOPE_WRITE:
        return {"denied": True, "error": f"Công cụ '{tool}' cần khóa **được ghi** (tạo ở Trang cá nhân → AI của tôi)."}
    return None


def run(db: Session, user, scope: int, tool: str, args: dict) -> dict:
    from . import erp

    if denied := _deny(tool, scope):
        return denied
    if not _is_allowed(db, user, tool):
        entity, action = TOOL_PERMS[tool]
        return {"denied": True, "error": f"Bạn không có quyền {action} trên {entity} nên không dùng được '{tool}'."}
    if tool in ("draft_key_issue", "draft_key_revoke"):
        try:
            return (_draft_key_issue if tool == "draft_key_issue" else _draft_key_revoke)(db, user, args or {})
        except KeyDraftError as e:
            return {"error": str(e)}
        except HTTPException as e:
            return {"error": str(e.detail)}
    return erp.skill_admin_draft(db, user, tool, args or {})


def confirm(db: Session, user, scope: int, kind: str, draft) -> dict:
    """Nhánh `confirm_draft` cho năm kind quản trị. Kiểm lại khóa + quyền + nhóm như lúc soạn."""
    from . import erp, mcp_settings

    tool = KIND_TOOL[kind]
    if denied := _deny(tool, scope):
        return denied
    if blocked := mcp_settings.tool_blocked(db, tool):
        return {"denied": True, "error": blocked}
    if not _is_allowed(db, user, tool):
        entity, action = TOOL_PERMS[tool]
        return {"denied": True, "error": f"Bạn không còn quyền {action} trên {entity} — bản nháp không được ghi."}
    if kind in SKILL_KINDS:
        return erp.skill_admin_confirm(db, user, kind, draft if isinstance(draft, dict) else {})
    try:
        payload = _open(user, kind, draft)
        return (_confirm_key_issue if kind == "key_issue" else _confirm_key_revoke)(db, user, payload)
    except KeyDraftError as e:
        db.rollback()
        return {"error": str(e)}
    except HTTPException as e:
        db.rollback()
        return {"error": str(e.detail), **({"denied": True} if e.status_code in (403, 404) else {})}


# ---------------------------------------------------------------------------
# Khóa của nhân sự — soạn / xác nhận ngay trong dịch vụ AI (bảng khóa ở đây)
# ---------------------------------------------------------------------------

def _make_fernet() -> Fernet:
    seed = f"mcp-key-admin|{settings.JWT_SECRET}".encode()
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(seed).digest()))


def _seal(user, kind: str, payload: dict) -> str:
    raw = json.dumps({"u": int(user.id), "k": kind, "p": payload}, ensure_ascii=False)
    return _make_fernet().encrypt(raw.encode()).decode()


def _open(user, kind: str, draft) -> dict:
    token = draft.get("token") if isinstance(draft, dict) else None
    if not isinstance(token, str) or not token:
        raise KeyDraftError("Thiếu bản nháp: gọi tool draft_* trước, đưa người dùng xem, rồi mới xác nhận đúng bản nháp đó.")
    try:
        data = json.loads(_make_fernet().decrypt(token.encode(), ttl=TOKEN_TTL))
    except (InvalidToken, ValueError, TypeError):
        raise KeyDraftError("Bản nháp đã hết hạn hoặc không hợp lệ — soạn lại bản nháp mới.") from None
    if not isinstance(data, dict) or data.get("u") != int(user.id):
        raise KeyDraftError("Bản nháp này không phải của bạn.")
    if data.get("k") != kind:
        raise KeyDraftError(f"Bản nháp này là loại \"{data.get('k')}\", không phải \"{kind}\".")
    return data.get("p") or {}


def sign_keys_state(db: Session, user_ids: list[int]) -> str:
    """Dấu tập khóa CHƯA thu hồi của những người này — lệch = có khóa mới phát / vừa thu hồi sau lúc soạn."""
    rows = key_admin_ops.find_live_keys(db, user_ids=user_ids) if user_ids else []
    return hashlib.sha256(json.dumps(sorted(r.id for r in rows)).encode()).hexdigest()[:40]


def _resolve(db: Session, user, args: dict) -> dict:
    from . import erp

    employees = args.get("employees") or []
    if not isinstance(employees, list):
        raise KeyDraftError("`employees` là danh sách mã hoặc tên nhân sự.")
    department = str(args.get("department") or "").strip()
    res = erp.resolve_people(db, user, [str(e) for e in employees[:mcp_keys.BATCH_MAX + 1]], department or None)
    if res.get("error"):
        raise KeyDraftError(str(res["error"]))
    return res


def _draft_key_issue(db: Session, user, args: dict) -> dict:
    res = _resolve(db, user, args)
    if not res.get("employee_ids") and not res.get("department_id"):
        raise KeyDraftError("Cần `employees` (mã / tên nhân sự) hoặc `department` (tên phòng).")
    days = int(args.get("days") or mcp_keys.DEFAULT_DAYS)
    people, skipped = key_admin_ops.plan_issue(db, user, user_ids=[], employee_ids=res["employee_ids"],
                                               department_id=0 if res["employee_ids"] else res["department_id"], days=days)
    if not people:
        raise KeyDraftError("Không có ai nhận được khóa: " + "; ".join(f"{s['label']} ({s['reason']})" for s in skipped))
    full = {p["user_id"] for p in people if mcp_keys.live_count(db, p["user_id"]) >= mcp_keys.MAX_KEYS}
    user_ids = [p["user_id"] for p in people]
    name = str(args.get("name") or "").strip()[:80]
    payload = {"user_ids": user_ids, "days": days, "name": name, "sig": sign_keys_state(db, user_ids)}
    preview = {"việc": f"PHÁT HỘ khóa kết nối AI CHỈ ĐỌC, hạn {days} ngày — người nhận bấm Nhận khóa ở Trang cá nhân",
               "người nhận": [p["label"] + (f" — đã đủ {mcp_keys.MAX_KEYS} khóa, sẽ bỏ qua" if p["user_id"] in full else "")
                              for p in people]}
    if res.get("department_label") and not res["employee_ids"]:
        preview["phòng"] = res["department_label"]
    if skipped:
        preview["bỏ qua"] = [f"{s['label']} ({s['reason']})" for s in skipped]
    return {"kind": "key_issue", "preview": preview,
            "draft": {"token": _seal(user, "key_issue", payload),
                      "summary": f"Phát {len(people) - len(full)} khóa AI chỉ đọc, hạn {days} ngày"},
            "note": NOTE}


def _draft_key_revoke(db: Session, user, args: dict) -> dict:
    from . import erp

    key_ids = [int(i) for i in (args.get("key_ids") or [])[:mcp_keys.BATCH_MAX] if str(i).isdigit()]
    batch_id = str(args.get("batch_id") or "").strip()[:32]
    owner_ids: list[int] = []
    if args.get("employees"):
        res = _resolve(db, user, {"employees": args.get("employees")})
        found = erp.key_admin_employees(db, user, "delete", res["employee_ids"])
        if found is None:
            raise KeyDraftError("Bạn không có quyền thu hồi khóa hộ.")
        if found["outside"]:
            raise KeyDraftError(f"{len(found['outside'])} nhân sự nằm ngoài phạm vi bạn được thu hồi hộ. Chưa soạn gì.")
        owner_ids = [p["user_id"] for p in found["people"]]
    if not (key_ids or batch_id or owner_ids):
        raise KeyDraftError("Cần `employees`, `key_ids` hoặc `batch_id` của khóa cần thu hồi.")
    rows = key_admin_ops.find_live_keys(db, key_ids=key_ids, user_ids=owner_ids, batch_id=batch_id)
    if not rows:
        raise KeyDraftError("Không có khóa nào đang hiệu lực khớp yêu cầu.")
    people = key_admin_ops.check_revoke_scope(db, user, rows)
    payload = {"key_ids": [r.id for r in rows]}
    preview = {"việc": f"THU HỒI {len(rows)} khóa kết nối AI — ứng dụng AI đang dùng các khóa này mất kết nối ngay",
               "khóa": [f"{people.get(int(r.user_id), {}).get('label', '#' + str(r.user_id))}: {r.name} …{r.key_hint} "
                        f"({mcp_keys.STATE_LABELS.get(mcp_keys.state_of(r), '')}, hạn "
                        f"{r.expires_at.date().isoformat() if r.expires_at else 'không'})" for r in rows]}
    return {"kind": "key_revoke", "preview": preview,
            "draft": {"token": _seal(user, "key_revoke", payload), "summary": f"Thu hồi {len(rows)} khóa AI"},
            "note": NOTE}


def _confirm_key_issue(db: Session, user, p: dict) -> dict:
    user_ids = [int(i) for i in p.get("user_ids") or []]
    if not user_ids:
        raise KeyDraftError("Bản nháp không có người nhận.")
    if sign_keys_state(db, user_ids) != p.get("sig"):
        raise KeyDraftError("Khóa của những người này đã đổi sau lúc soạn bản nháp (hoặc bản nháp đã dùng rồi) — soạn lại.")
    people = key_admin_ops.list_people_in_scope(db, user, "create", user_ids=user_ids, limit=mcp_keys.BATCH_MAX + 1)
    if set(user_ids) - {x["user_id"] for x in people}:
        raise KeyDraftError("Có người đã ra ngoài phạm vi bạn được phát khóa hộ — chưa phát khóa nào, soạn lại.")
    out = key_admin_ops.issue_to_people(db, user, [x for x in people if x["user_id"] in set(user_ids)],
                                        days=int(p.get("days") or mcp_keys.DEFAULT_DAYS), name=str(p.get("name") or ""))
    skipped = "; ".join(f"{s['label']} ({s['reason']})" for s in out["skipped"])
    return {"ok": True, "message": f"Đã phát {len(out['issued'])} khóa, mỗi người nhận chuông để lấy khóa."
                                   + (f" Bỏ qua: {skipped}." if skipped else ""),
            "batch_id": out["batch_id"], "link": "/ai-skill/keys"}


def _confirm_key_revoke(db: Session, user, p: dict) -> dict:
    key_ids = sorted(int(i) for i in p.get("key_ids") or [])
    rows = key_admin_ops.find_live_keys(db, key_ids=key_ids)
    if sorted(r.id for r in rows) != key_ids or not key_ids:
        raise KeyDraftError("Có khóa đã bị thu hồi / đổi sau lúc soạn bản nháp (hoặc bản nháp đã dùng rồi) — soạn lại.")
    key_admin_ops.check_revoke_scope(db, user, rows)
    n = mcp_keys.revoke_rows(db, rows, by_user_id=user.id)
    return {"ok": True, "message": f"Đã thu hồi {n} khóa.", "link": "/ai-skill/keys"}
