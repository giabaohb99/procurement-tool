"""CỔNG ERP của bot (ai-CR-119, phase S-2 — doc/agent-hub/13 §3.2): mọi thứ bot cần từ ERP đi qua MỘT lớp này.

Hai cách chạy, chọn theo `AGENT_MODE`:
  - embedded / erp: gọi THẲNG hàm nghiệp vụ trong cùng tiến trình (như trước 08/10/2026) — `_Local`.
  - service: gọi HTTP sang cổng B của ERP (`/api/agent-gw/*`, xem `modules/agent_gateway`) với chữ ký
    `core/agent_signature.py` mang id người dùng — `_Remote`. Dịch vụ AI không có bảng ERP nào.

`_Local` cũng là NGUỒN DUY NHẤT mà cổng B gọi, nên hai cách chạy không bao giờ lệch nhau. Mọi hàm trả dict / dataclass
JSON-hóa được, KHÔNG trả ORM — trừ `user_by_id` ở chế độ embedded trả đúng ORM `User` để các công cụ của Trợ lý (apply_scope)
chạy nguyên như cũ.

Người dùng ở chế độ service là `ErpUser` (id, email, employee_id, is_active, nhãn, chân dung) — đủ cho sổ riêng, thẻ việc,
biên bản; còn số liệu ERP thì công cụ chạy ở ERP dưới đúng quyền người đó.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field

import requests

from app.core import agent_signature
from app.core.config import settings

log = logging.getLogger("app.agent_hub.erp")

TIMEOUT = 30
TOOL_TIMEOUT = 90
#  Công cụ chạy NGAY trong dịch vụ AI (dữ liệu riêng từng người: sổ nhớ, thẻ, nhóm, họp, Google) — mọi tên khác chạy ở ERP.
LOCAL_TOOL_MODULES = ("personal_tool", "group_tool", "meeting_tool", "google_tool", "brief_tool",
                      "research_tool")      # ai-CR-178: nghiên cứu sâu chạy ở dịch vụ AI, không đọc ERP


#  ai-CR-162: chờ ERP khởi động lại khi kết nối bị từ chối — tổng ~45 giây (một lần dựng lại api dev ~30-40 giây).
CONNECT_RETRY_WAITS = (3, 12, 30)


def _not_connected(e: Exception) -> bool:
    """Lỗi xảy ra TRƯỚC khi yêu cầu tới được ERP (từ chối kết nối, không phân giải được tên, hết giờ chờ kết nối)."""
    if isinstance(e, requests.ConnectTimeout):
        return True
    if not isinstance(e, requests.ConnectionError) or isinstance(e, requests.ReadTimeout):
        return False
    text = repr(e)
    return any(k in text for k in ("NewConnectionError", "Connection refused", "Name or service not known",
                                   "Temporary failure in name resolution", "Failed to establish"))


class ErpError(RuntimeError):
    """Cổng ERP hỏng (mạng, chữ ký, ERP trả lỗi) — một câu nói được."""


@dataclass
class ErpUser:
    """Tài khoản ERP nhìn từ dịch vụ AI. Có cùng các thuộc tính mà mã bot đọc trên ORM `User`."""

    id: int
    email: str = ""
    employee_id: int = 0
    is_active: bool = True
    label: str = ""          # «Họ tên (MÃ NV)» — describe_user
    detail: str = ""         # «phòng … · tên đăng nhập …»
    context: str = ""        # chân dung cho system prompt (assistant.service._caller_context)
    names: list[str] = field(default_factory=list)   # tên / mã để tìm người («cho anh Được quyền gộp»)
    department_id: int = 0   # ai-CR-209: phòng ban / pháp nhân của hồ sơ nhân sự — nhật ký MCP chụp lúc gọi
    company_id: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict | None) -> "ErpUser | None":
        if not d:
            return None
        return cls(id=int(d.get("id") or 0), email=str(d.get("email") or ""), employee_id=int(d.get("employee_id") or 0),
                   is_active=bool(d.get("is_active", True)), label=str(d.get("label") or ""),
                   detail=str(d.get("detail") or ""), context=str(d.get("context") or ""),
                   names=[str(x) for x in (d.get("names") or [])], department_id=int(d.get("department_id") or 0),
                   company_id=int(d.get("company_id") or 0))


def is_remote() -> bool:
    return settings.agent_is_service


def _uid(user) -> int:
    return int(getattr(user, "id", 0) or 0)


def _src(source: int) -> dict:
    """ai-CR-182: chỉ truyền `source` xuống hàm ghi khi có kênh thật (khác 0) — 0 là mặc định của chính hàm đó,
    và các bản giả trong bài kiểm cũ vẫn gọi được theo chữ ký cũ."""
    return {"source": int(source)} if source else {}


# ===========================================================================
# Chạy THẲNG trong ERP (embedded) — và là mã của cổng B
# ===========================================================================
class _Local:
    @staticmethod
    def describe(db, user) -> tuple[str, str]:
        from .service import describe_user

        return describe_user(db, user)

    @staticmethod
    def names_of(db, user) -> list[str]:
        from app.modules.employee.model import Employee

        if user is None:
            return []
        emp = db.get(Employee, user.employee_id) if getattr(user, "employee_id", 0) else None
        names = [getattr(user, "email", "") or ""]
        if emp is not None:
            names += [emp.full_name or "", emp.code or "", (emp.full_name or "").split()[-1] if emp.full_name else ""]
        return [n for n in names if n]

    @classmethod
    def snapshot(cls, db, user) -> ErpUser | None:
        """ORM User → ErpUser đầy đủ (cổng B trả cho dịch vụ AI)."""
        from app.modules.assistant.service import _caller_context

        if user is None:
            return None
        label, detail = cls.describe(db, user)
        dept_id, comp_id = cls.org_of(db, user)
        return ErpUser(id=int(user.id), email=user.email or "", employee_id=int(user.employee_id or 0),
                       is_active=bool(user.is_active), label=label, detail=detail,
                       context=_caller_context(db, user) or "", names=cls.names_of(db, user),
                       department_id=dept_id, company_id=comp_id)

    @staticmethod
    def org_of(db, user) -> tuple[int, int]:
        """(phòng ban, pháp nhân) theo hồ sơ nhân sự của tài khoản; chưa gắn nhân sự thì (0, 0)."""
        from app.modules.employee.model import Employee

        emp = db.get(Employee, user.employee_id) if getattr(user, "employee_id", 0) else None
        return (int(getattr(emp, "department_id", 0) or 0), int(getattr(emp, "company_id", 0) or 0)) if emp else (0, 0)

    @staticmethod
    def user_by_id(db, user_id: int):
        from app.modules.user.model import User

        return db.get(User, int(user_id or 0)) if user_id else None

    @staticmethod
    def user_by_email(db, email: str):
        from sqlalchemy import select

        from app.modules.user.model import User

        email = (email or "").strip()
        return db.scalar(select(User).where(User.email == email)) if email else None

    @classmethod
    def search_users(cls, db, key: str) -> list:
        """Tài khoản đang hoạt động khớp tên / mã / tên đăng nhập (so không dấu). Trả ORM User (embedded)."""
        from sqlalchemy import select

        from app.modules.assistant.glossary import fold
        from app.modules.user.model import User

        key = fold(key)
        if not key:
            return []
        found, exact = [], []
        for user in db.scalars(select(User).where(User.is_active.is_(True))):
            folded = [fold(n) for n in cls.names_of(db, user) if n]
            if any(key == f for f in folded):
                exact.append(user)
            elif len(key) >= 3 and any(key in f for f in folded):
                found.append(user)
        return exact if exact else found

    @staticmethod
    def can(db, user, entity: str, action: str) -> bool:
        #  Đọc THẲNG hồ sơ quyền (không qua `user_has_permission`: ở chế độ service hàm đó lại gọi về cổng → vòng lặp).
        from app.core.auth import get_perm_profile

        if user is None:
            return False
        return bool(get_perm_profile(db, user)["perms_union"].get(entity, {}).get(action, False))

    @staticmethod
    def tool_defs(db, user=None) -> list:
        from app.modules.assistant.tools import tool_defs

        return tool_defs(db)

    @staticmethod
    def run_tool(db, user, name: str, args: dict) -> dict:
        from app.modules.assistant.tools import run_tool

        return run_tool(db, user, name, args or {})

    # --- Kho skill AI (bao-CR-622, K2 doc/erp/21) ---
    @staticmethod
    def skill_list(db, user, query: str = "", skill_set: str = "") -> dict:
        from app.modules.ai_skill import mcp_read

        return mcp_read.list_for_ai(db, user, query, skill_set)

    @staticmethod
    def skill_read(db, user, name: str) -> dict:
        from app.modules.ai_skill import mcp_read

        return mcp_read.read_for_ai(db, user, name)

    @staticmethod
    def skill_file(db, user, name: str, path: str) -> dict:
        from app.modules.ai_skill import mcp_read

        return mcp_read.file_for_ai(db, user, name, path)

    @staticmethod
    def caller_context(db, user) -> str | None:
        from app.modules.assistant.service import _caller_context

        return _caller_context(db, user)

    @staticmethod
    def glossary_block(db, texts: list[str]) -> str | None:
        from app.modules.assistant import glossary

        return glossary.prompt_block(db, *[t for t in texts if t])

    @staticmethod
    def settings_snapshot(db) -> dict:
        from app.modules.setting.model import Setting

        return {s.skey: s.svalue for s in db.query(Setting).all()}

    #  ai-CR-128: sổ JSON trong `tab_setting` mà bot đọc / ghi (thuật ngữ, đề xuất thuật ngữ, chỗ Trợ lý thiếu chức năng).
    @staticmethod
    def setting_raw_get(db, key: str) -> str:
        from app.modules.setting.model import Setting

        row = db.query(Setting).filter(Setting.skey == key).first()
        return row.svalue if row is not None and row.svalue else ""

    @staticmethod
    def setting_raw_put(db, key: str, value: str, user_id: int) -> None:
        from app.modules.setting import service as setting_service

        setting_service._upsert(db, key, value, int(user_id or 0))
        db.commit()

    # --- tạo phiếu từ nháp ---------------------------------------------------------------------------------------
    #  `source` (ai-CR-182): kênh người dùng xác nhận (`assistant.change_model.ChangeSource`) — chỉ để ghi sổ thay đổi.
    #  Cổng B truyền 1 (Telegram); chạy chung tiến trình không biết kênh thì để 0.
    @staticmethod
    def create_draft(db, user, kind: str, draft: dict, source: int = 0) -> tuple[str, int]:
        from . import draft_create

        return draft_create.create(db, user, kind, draft, **_src(source))

    @staticmethod
    def submit_draft(db, user, kind: str, oid: int, source: int = 0) -> None:
        from . import draft_create

        draft_create.submit(db, user, kind, oid, **_src(source))

    @staticmethod
    def created_details(db, kind: str, oid: int) -> list[str]:
        from . import draft_create

        return draft_create.created_details(db, kind, oid)

    #  ai-CR-143: đơn nháp của chính mình — xem / dùng lại / xóa bớt.
    @staticmethod
    def my_drafts(db, user) -> list[dict]:
        from . import draft_create

        return draft_create.list_mine(db, user)

    @staticmethod
    def update_leave_draft(db, user, oid: int, draft: dict, source: int = 0) -> str:
        from . import draft_create

        return draft_create.update_leave(db, user, oid, draft, **_src(source))

    @staticmethod
    def delete_my_drafts(db, user, items: list[dict], source: int = 0) -> dict:
        from . import draft_create

        return draft_create.delete_mine(db, user, items, **_src(source))

    @staticmethod
    def update_doc_draft(db, user, kind: str, oid: int, draft: dict, mode: str, source: int = 0) -> dict:
        from . import draft_create

        return draft_create.update_doc_draft(db, user, kind, oid, draft, mode, **_src(source))

    #  ai-CR-151: nút «Xác nhận sửa / xóa» của thẻ đề xuất. Ghi phiếu là việc của ERP — ở chế độ service phải đi qua
    #  cổng B, không được gọi `confirm_update` trên DB của bot (DB đó không có bảng phiếu).
    @staticmethod
    def confirm_proposal(db, user, token: str, source: int = 0) -> dict:
        from app.modules.assistant.tools.update_tool import confirm_update

        return confirm_update(db, user, token, **_src(source))

    #  ai-CR-182: sổ thay đổi do bot ghi + hoàn tác 24 giờ (`assistant/change_service.py`) — bảng ở DB ERP.
    @staticmethod
    def my_changes(db, user, limit: int = 20) -> list[dict]:
        from app.modules.assistant import change_service

        return change_service.list_for(db, user, limit=limit)

    @staticmethod
    def undo_change(db, user, change_id: int, source: int = 0) -> dict:
        from app.modules.assistant import change_service

        return change_service.undo(db, user, change_id, source=source)

    # --- phiếu hỗ trợ ------------------------------------------------------------------------------------------------
    @staticmethod
    def ticket_info(db, t) -> dict:
        from sqlalchemy import select

        from app.modules.employee.model import Employee
        from app.modules.ticket.model import TicketMessage

        first = db.scalar(select(TicketMessage).where(TicketMessage.ticket_id == t.id, TicketMessage.is_staff.is_(False))
                          .order_by(TicketMessage.id).limit(1))
        requester = db.get(Employee, t.requester_id) if t.requester_id else None
        return {"id": int(t.id), "code": t.code, "subject": t.subject or "", "department": t.department or "",
                "priority": str(t.priority or ""), "status": str(t.status or ""), "assignee_id": int(t.assignee_id or 0),
                "origin_url": t.origin_url or "", "requester": (requester.full_name if requester is not None else "") or "",
                "first_body": (first.body or "").strip() if first is not None else ""}

    @classmethod
    def tickets_open(cls, db, statuses: list[str], exclude_ids: list[int], *, limit: int = 200) -> list[dict]:
        from sqlalchemy import select

        from app.modules.ticket.model import Ticket

        q = select(Ticket).where(Ticket.status.in_(statuses))
        if exclude_ids:
            q = q.where(Ticket.id.not_in(exclude_ids))
        return [cls.ticket_info(db, t) for t in db.scalars(q.order_by(Ticket.id).limit(limit))]

    @staticmethod
    def tickets_max_id(db) -> int:
        from sqlalchemy import func, select

        from app.modules.ticket.model import Ticket

        return int(db.scalar(select(func.max(Ticket.id))) or 0)

    @classmethod
    def tickets_by_ids(cls, db, ids: list[int]) -> list[dict]:
        from sqlalchemy import select

        from app.modules.ticket.model import Ticket

        return [cls.ticket_info(db, t) for t in db.scalars(select(Ticket).where(Ticket.id.in_(ids)))] if ids else []

    @staticmethod
    def ticket_note(db, ticket_id: int, body: str, *, status: str, by_user_id: int, clear_assignee: bool = False) -> None:
        """Một dòng trả lời của nhóm hỗ trợ + đặt trạng thái (không qua service để khỏi tự đổi «Đã trả lời»)."""
        from app.modules.ticket.model import Ticket, TicketMessage

        t = db.get(Ticket, int(ticket_id))
        if t is None:
            return
        uid = int(by_user_id or 0)
        db.add(TicketMessage(ticket_id=t.id, body=body, is_staff=True, created_by=uid, updated_by=uid))
        t.status = status
        t.closed_at = None
        t.updated_by = uid
        if clear_assignee and uid and t.assignee_id == uid:
            t.assignee_id = 0
        db.commit()

    @staticmethod
    def create_ticket(db, user, *, subject: str, department: str, body: str) -> dict:
        from app.modules.ticket import service as ticket_service
        from app.modules.ticket.schema import TicketCreate

        t = ticket_service.create_ticket(db, TicketCreate(subject=subject, department=department, body=body),
                                         user_id=user.id, requester_emp_id=int(getattr(user, "employee_id", 0) or 0))
        db.commit()
        return {"id": int(t.id), "code": t.code}

    # --- phát khóa AI hộ (ai-CR-212) ------------------------------------------------------------------------------
    @staticmethod
    def key_admin_people(db, admin, action: str, *, user_ids: list[int] | None = None, department_id: int = 0,
                         limit: int = 2000) -> list[dict] | None:
        from app.modules.agent_gateway.key_admin import people_in_scope

        return people_in_scope(db, admin, action, user_ids=user_ids, department_id=department_id, limit=limit)

    @staticmethod
    def notify_users(db, user_ids: list[int], *, title: str, body: str, link: str, by_user_id: int = 0) -> int:
        from app.modules.agent_gateway.key_admin import notify

        return notify(db, user_ids, title=title, body=body, link=link, by_user_id=by_user_id)

    @staticmethod
    def skill_stats(db) -> dict:
        from app.modules.agent_gateway.key_admin import skill_stats

        return skill_stats(db)

    @staticmethod
    def key_admin_employees(db, admin, action: str, employee_ids: list[int]) -> dict | None:
        from app.modules.agent_gateway.key_admin import employee_accounts

        return employee_accounts(db, admin, action, employee_ids)

    # --- chuông ------------------------------------------------------------------------------------------------------
    @staticmethod
    def notifications_after(db, after_id: int, limit: int) -> list[dict]:
        from sqlalchemy import select

        from app.modules.notification.model import Notification

        rows = db.scalars(select(Notification).where(Notification.id > int(after_id)).order_by(Notification.id).limit(limit))
        return [{"id": int(n.id), "user_id": int(n.user_id or 0), "title": n.title or "", "body": n.body or "",
                 "link": n.link or ""} for n in rows]

    @staticmethod
    def notifications_max_id(db) -> int:
        from sqlalchemy import func, select

        from app.modules.notification.model import Notification

        return int(db.scalar(select(func.max(Notification.id))) or 0)

    # --- tệp đính kèm của Trợ lý web -------------------------------------------------------------------------------
    @staticmethod
    def attachment_blocks(db, user, ids: list[int]) -> tuple[list | None, list[dict]]:
        """(khối nội dung cho model, mô tả để lưu) của các tệp CỦA CHÍNH người này. Sai id → PermissionError."""
        from app.modules.assistant import attachments as attach

        files = attach.resolve_owned(db, user, ids or [])
        return (attach.build_blocks(files) if files else None), attach.meta_of(files)

    # --- tệp báo cáo do công cụ xuất ----------------------------------------------------------------------------------
    @staticmethod
    def report_file(db, user, file_id: int) -> dict | None:
        """{filename, content_type, data(bytes)} nếu tệp là báo cáo CỦA CHÍNH người này; không thì None."""
        from app.core.storage import download_bytes
        from app.modules.attachment.model import StoredFile

        f = db.get(StoredFile, int(file_id or 0)) if file_id else None
        if f is None or f.created_by != user.id or "/assistant-report/" not in (f.file_key or ""):
            return None
        return {"filename": f.filename, "content_type": f.content_type or "", "data": download_bytes(f.file_key),
                "size": int(f.size or 0)}

    # --- nhân sự, dự án ----------------------------------------------------------------------------------------------
    @staticmethod
    def match_employee(db, name: str) -> dict | None:
        from .meeting_actions import _match_employee_local

        return _match_employee_local(db, name)

    @staticmethod
    def projects_for(db, user) -> list[dict]:
        from .meeting_actions import _projects_local

        return [{"id": int(p.id), "name": p.name} for p in _projects_local(db, user)]

    #  bao-CR-616 (phase 24.1): kế hoạch việc — lớp ERP ở `work/plan_service` (đọc cây việc, ghi câu trả lời người làm).
    @staticmethod
    def plan_overview(db, user, list_id: int) -> dict:
        from app.modules.work import plan_service

        return plan_service.overview(db, user, int(list_id))

    @staticmethod
    def plan_reply(db, user, task_id: int, action: str, text: str = "", pct: int | None = None,
                   score: int | None = None) -> dict:
        from app.modules.work import plan_service

        return plan_service.reply(db, user, int(task_id), action, text=text, pct=pct, score=score)


# ===========================================================================
# Chạy ở dịch vụ AI: gọi cổng B
# ===========================================================================
class _Remote:
    def __init__(self) -> None:
        self._tool_defs: tuple[float, list] = (0.0, [])
        self._can: dict[tuple[int, str, str], tuple[float, bool]] = {}

    # --- vận chuyển ---
    def _call(self, method: str, path: str, *, user_id: int = 0, body: dict | None = None, params: dict | None = None,
              timeout: int = TIMEOUT, raw: bool = False):
        base = (settings.AGENT_GATEWAY_URL or "").rstrip("/")
        if not base:
            raise ErpError("Chưa khai AGENT_GATEWAY_URL — dịch vụ AI không biết ERP ở đâu")
        full = f"/api/agent-gw{path}"
        data = json.dumps(body, ensure_ascii=False, default=str).encode("utf-8") if body is not None else b""
        try:
            headers = agent_signature.sign_headers(method, full, data, user_id)
        except ValueError as e:
            raise ErpError(str(e)) from None
        if data:
            headers["content-type"] = "application/json"
        resp = None
        for wait in (*CONNECT_RETRY_WAITS, None):
            try:
                resp = requests.request(method, f"{base}{full}", params=params, data=data or None, headers=headers,
                                        timeout=timeout)
                break
            except requests.RequestException as e:
                #  ai-CR-162: ERP đang khởi động lại (deploy) thì kết nối bị từ chối vài chục giây — thử lại. Chỉ thử lại
                #  khi CHƯA kết nối được (yêu cầu chưa tới ERP), không thử lại khi đã gửi mà chờ quá giờ.
                if wait is None or not _not_connected(e):
                    raise ErpError(f"Không gọi được ERP ({type(e).__name__})") from None
                log.warning("agent_hub erp: ERP chưa nhận kết nối, thử lại sau %ss", wait)
                time.sleep(wait)
        if raw:
            if resp.status_code >= 400:
                raise ErpError(f"ERP trả lỗi {resp.status_code}")
            return resp
        try:
            payload = resp.json()
        except ValueError:
            raise ErpError(f"ERP trả {resp.status_code}, không phải JSON") from None
        if resp.status_code >= 400 or not payload.get("success", True):
            msg = ((payload.get("error") or {}).get("message")) or payload.get("message") or f"lỗi {resp.status_code}"
            raise ErpError(f"ERP: {msg}")
        return payload.get("data") if "data" in payload else payload

    # --- người dùng ---
    def user_by_id(self, db, user_id: int) -> ErpUser | None:
        if not user_id:
            return None
        return ErpUser.from_dict(self._call("GET", "/me", user_id=int(user_id)))

    def user_by_email(self, db, email: str) -> ErpUser | None:
        email = (email or "").strip()
        if not email:
            return None
        rows = self._call("POST", "/users/lookup", body={"emails": [email]})
        return ErpUser.from_dict(rows[0]) if rows else None

    def search_users(self, db, key: str) -> list[ErpUser]:
        return [u for u in (ErpUser.from_dict(d) for d in self._call("GET", "/users/search", params={"q": key})) if u]

    def describe(self, db, user) -> tuple[str, str]:
        if user is None:
            return "", ""
        if isinstance(user, ErpUser):
            return user.label or (user.email or f"tài khoản #{user.id}"), user.detail
        u = self.user_by_id(db, _uid(user))
        return (u.label, u.detail) if u else ("", "")

    def names_of(self, db, user) -> list[str]:
        return list(user.names) if isinstance(user, ErpUser) else []

    def can(self, db, user, entity: str, action: str) -> bool:
        key = (_uid(user), entity, action)
        hit = self._can.get(key)
        if hit and time.monotonic() - hit[0] < 60:
            return hit[1]
        ok = bool(self._call("POST", "/can", user_id=_uid(user), body={"entity": entity, "action": action}).get("ok"))
        self._can[key] = (time.monotonic(), ok)
        return ok

    def caller_context(self, db, user) -> str | None:
        return (user.context or None) if isinstance(user, ErpUser) else None

    def glossary_block(self, db, texts: list[str]) -> str | None:
        try:
            return (self._call("POST", "/glossary/block", body={"texts": [t for t in texts if t]}) or {}).get("block") or None
        except ErpError as e:
            log.info("agent_hub erp: không lấy được thuật ngữ: %s", e)
            return None

    def settings_snapshot(self, db=None) -> dict:
        try:
            return dict(self._call("GET", "/settings") or {})
        except ErpError as e:
            log.warning("agent_hub erp: không lấy được cấu hình hệ thống, dùng .env: %s", e)
            return {}

    def setting_raw_get(self, db, key: str) -> str:
        return str((self._call("GET", "/settings/raw", params={"key": key}) or {}).get("value") or "")

    def setting_raw_put(self, db, key: str, value: str, user_id: int) -> None:
        self._call("PUT", "/settings/raw", user_id=int(user_id or 0), body={"key": key, "value": value})

    # --- công cụ của Trợ lý ---
    def tool_defs(self, db, user=None) -> list:
        from app.modules.assistant.provider.base import ToolDef
        from app.modules.assistant.tools import tool_defs

        local = [d for d in tool_defs(db) if d.name in local_tool_names()]
        ts, cached = self._tool_defs
        if time.monotonic() - ts > 600 or not cached:
            try:
                remote = [ToolDef(name=d["name"], description=d["description"], parameters=d["parameters"])
                          for d in self._call("GET", "/tools", user_id=_uid(user))]
            except ErpError as e:
                log.warning("agent_hub erp: không lấy được danh sách công cụ ERP: %s", e)
                remote = cached
            self._tool_defs = (time.monotonic(), remote)
            cached = remote
        local_names = {d.name for d in local}
        return local + [d for d in cached if d.name not in local_names]

    def run_tool(self, db, user, name: str, args: dict) -> dict:
        if name in local_tool_names():
            from app.modules.assistant.tools import run_tool

            return run_tool(db, user, name, args or {})
        try:
            return self._call("POST", "/tools/run", user_id=_uid(user), body={"name": name, "args": args or {}},
                              timeout=TOOL_TIMEOUT) or {}
        except ErpError as e:
            return {"error": f"Không gọi được công cụ ERP: {e}"}

    # --- Kho skill AI (bao-CR-622) — dữ liệu skill nằm ở ERP, chỉ đọc qua cổng B ---
    def _skill_call(self, path: str, user, params: dict) -> dict:
        try:
            return self._call("GET", path, user_id=_uid(user), params=params, timeout=TOOL_TIMEOUT) or {}
        except ErpError as e:
            return {"error": f"Không đọc được Kho skill từ ERP: {e}"}

    def skill_list(self, db, user, query: str = "", skill_set: str = "") -> dict:
        return self._skill_call("/skills", user, {"query": query or "", "skill_set": skill_set or ""})

    def skill_read(self, db, user, name: str) -> dict:
        return self._skill_call("/skills/read", user, {"name": name or ""})

    def skill_file(self, db, user, name: str, path: str) -> dict:
        return self._skill_call("/skills/file", user, {"name": name or "", "path": path or ""})

    # --- tạo phiếu ---
    def create_draft(self, db, user, kind: str, draft: dict, source: int = 0) -> tuple[str, int]:
        from .draft_create import DraftError

        try:
            out = self._call("POST", "/draft/create", user_id=_uid(user), body={"kind": kind, "draft": draft})
        except ErpError as e:
            raise DraftError(str(e)) from None
        if out.get("error"):
            raise DraftError(str(out["error"]))
        return str(out.get("code") or ""), int(out.get("id") or 0)

    def submit_draft(self, db, user, kind: str, oid: int, source: int = 0) -> None:
        from .draft_create import DraftError

        try:
            out = self._call("POST", "/draft/submit", user_id=_uid(user), body={"kind": kind, "id": int(oid)})
        except ErpError as e:
            raise DraftError(str(e)) from None
        if out.get("error"):
            raise DraftError(str(out["error"]))

    def created_details(self, db, kind: str, oid: int) -> list[str]:
        try:
            return list(self._call("GET", "/draft/details", params={"kind": kind, "id": int(oid)}) or [])
        except ErpError:
            return []

    def my_drafts(self, db, user) -> list[dict]:
        try:
            return list(self._call("GET", "/draft/mine", user_id=_uid(user)) or [])
        except ErpError:
            return []

    def update_leave_draft(self, db, user, oid: int, draft: dict, source: int = 0) -> str:
        from .draft_create import DraftError

        try:
            out = self._call("POST", "/draft/update", user_id=_uid(user), body={"kind": "leave", "id": int(oid),
                                                                              "draft": draft})
        except ErpError as e:
            raise DraftError(str(e)) from None
        if out.get("error"):
            raise DraftError(str(out["error"]))
        return str(out.get("code") or "")

    def delete_my_drafts(self, db, user, items: list[dict], source: int = 0) -> dict:
        from .draft_create import DraftError

        try:
            return dict(self._call("POST", "/draft/delete", user_id=_uid(user), body={"items": items}) or {})
        except ErpError as e:
            raise DraftError(str(e)) from None

    def update_doc_draft(self, db, user, kind: str, oid: int, draft: dict, mode: str, source: int = 0) -> dict:
        from .draft_create import DraftError

        try:
            out = dict(self._call("POST", "/draft/reuse", user_id=_uid(user),
                                  body={"kind": kind, "id": int(oid), "draft": draft, "mode": mode}) or {})
        except ErpError as e:
            raise DraftError(str(e)) from None
        if out.get("error"):
            raise DraftError(str(out["error"]))
        return out

    def confirm_proposal(self, db, user, token: str, source: int = 0) -> dict:
        """Cổng trả lỗi nghiệp vụ dưới dạng `{error, status}` → ném lại HTTPException như bản chạy chung, để người gọi
        xử một đường. `source` do cổng B tự đặt (kênh bot), không gửi qua."""
        from fastapi import HTTPException

        out = dict(self._call("POST", "/proposal/confirm", user_id=_uid(user), body={"token": token}) or {})
        if out.get("error"):
            raise HTTPException(int(out.get("status") or 400), str(out["error"]))
        return out

    # --- sổ thay đổi + hoàn tác (ai-CR-182) ---
    def my_changes(self, db, user, limit: int = 20) -> list[dict]:
        try:
            return list(self._call("GET", "/changes/mine", user_id=_uid(user), params={"limit": int(limit)}) or [])
        except ErpError as e:
            log.warning("agent_hub erp: không đọc được sổ thay đổi: %s", e)
            return []

    def undo_change(self, db, user, change_id: int, source: int = 0) -> dict:
        from fastapi import HTTPException

        out = dict(self._call("POST", "/changes/undo", user_id=_uid(user), body={"id": int(change_id)}) or {})
        if out.get("error"):
            raise HTTPException(int(out.get("status") or 400), str(out["error"]))
        return out

    # --- phiếu hỗ trợ ---
    def tickets_open(self, db, statuses: list[str], exclude_ids: list[int], *, limit: int = 200) -> list[dict]:
        return list(self._call("POST", "/tickets/open", body={"statuses": statuses, "exclude_ids": exclude_ids,
                                                             "limit": limit}) or [])

    def tickets_max_id(self, db) -> int:
        return int((self._call("GET", "/tickets/max-id") or {}).get("max_id") or 0)

    def tickets_by_ids(self, db, ids: list[int]) -> list[dict]:
        return list(self._call("POST", "/tickets/by-ids", body={"ids": ids}) or []) if ids else []

    def ticket_note(self, db, ticket_id: int, body: str, *, status: str, by_user_id: int, clear_assignee: bool = False) -> None:
        self._call("POST", f"/tickets/{int(ticket_id)}/note", user_id=by_user_id,
                   body={"body": body, "status": status, "clear_assignee": clear_assignee})

    def create_ticket(self, db, user, *, subject: str, department: str, body: str) -> dict:
        return dict(self._call("POST", "/tickets", user_id=_uid(user),
                               body={"subject": subject, "department": department, "body": body}) or {})

    # --- phát khóa AI hộ (ai-CR-212) ---
    def key_admin_people(self, db, admin, action: str, *, user_ids: list[int] | None = None, department_id: int = 0,
                         limit: int = 2000) -> list[dict] | None:
        out = self._call("POST", "/key-admin/people", user_id=_uid(admin),
                         body={"action": action, "user_ids": user_ids, "department_id": int(department_id or 0),
                               "limit": int(limit)}) or {}
        return list(out.get("people") or []) if out.get("allowed") else None

    def notify_users(self, db, user_ids: list[int], *, title: str, body: str, link: str, by_user_id: int = 0) -> int:
        out = self._call("POST", "/key-admin/notify", user_id=int(by_user_id or 0),
                         body={"user_ids": [int(i) for i in user_ids], "title": title, "body": body, "link": link}) or {}
        return int(out.get("sent") or 0)

    def skill_stats(self, db) -> dict:
        return dict(self._call("GET", "/ai-skill/stats") or {})

    def key_admin_employees(self, db, admin, action: str, employee_ids: list[int]) -> dict | None:
        out = self._call("POST", "/key-admin/employees", user_id=_uid(admin),
                         body={"action": action, "employee_ids": [int(i) for i in employee_ids]}) or {}
        if not out.get("allowed"):
            return None
        return {k: list(out.get(k) or []) for k in ("people", "no_account", "outside")}

    # --- chuông ---
    def notifications_after(self, db, after_id: int, limit: int) -> list[dict]:
        return list(self._call("GET", "/notifications", params={"after_id": int(after_id), "limit": int(limit)}) or [])

    def notifications_max_id(self, db) -> int:
        return int((self._call("GET", "/notifications/max-id") or {}).get("max_id") or 0)

    # --- tệp ---
    def attachment_blocks(self, db, user, ids: list[int]) -> tuple[list | None, list[dict]]:
        if not ids:
            return None, []
        out = self._call("POST", "/attachments/blocks", user_id=_uid(user), body={"ids": ids}, timeout=120)
        if out.get("error"):
            raise PermissionError(str(out["error"]))
        return (out.get("blocks") or None), list(out.get("meta") or [])

    def report_file(self, db, user, file_id: int) -> dict | None:
        try:
            resp = self._call("GET", f"/files/{int(file_id)}", user_id=_uid(user), raw=True, timeout=120)
        except ErpError:
            return None
        from urllib.parse import unquote

        return {"filename": unquote(resp.headers.get("X-Filename") or "bao-cao.bin"),
                "content_type": resp.headers.get("content-type") or "", "data": resp.content, "size": len(resp.content)}

    # --- nhân sự, dự án ---
    def match_employee(self, db, name: str) -> dict | None:
        try:
            return self._call("GET", "/employees/match", params={"name": name}) or None
        except ErpError:
            return None

    def projects_for(self, db, user) -> list[dict]:
        try:
            return list(self._call("GET", "/projects", user_id=_uid(user)) or [])
        except ErpError:
            return []

    def plan_overview(self, db, user, list_id: int) -> dict:
        try:
            return dict(self._call("GET", "/plan/overview", user_id=_uid(user), params={"list_id": int(list_id)}) or {})
        except ErpError as e:
            return {"error": str(e)}

    def plan_reply(self, db, user, task_id: int, action: str, text: str = "", pct: int | None = None,
                   score: int | None = None) -> dict:
        try:
            return dict(self._call("POST", "/plan/reply", user_id=_uid(user),
                                   body={"task_id": int(task_id), "action": action, "text": text, "pct": pct,
                                         "score": score}) or {})
        except ErpError as e:
            return {"error": str(e)}


# ===========================================================================
# Mặt tiền
# ===========================================================================
_remote: _Remote | None = None


def _impl():
    global _remote
    if is_remote():
        if _remote is None:
            _remote = _Remote()
        return _remote
    return _Local


def local_tool_names() -> set[str]:
    """Tên các công cụ chạy ngay trong dịch vụ AI."""
    from app.modules.assistant.tools import _active_specs

    out = set()
    for spec in _active_specs():
        module = getattr(getattr(spec, "handler", None), "__module__", "") or ""
        if module.rsplit(".", 1)[-1] in LOCAL_TOOL_MODULES:
            out.add(spec.name)
    return out


def user_by_id(db, user_id: int):
    return _impl().user_by_id(db, user_id)


def user_by_email(db, email: str):
    return _impl().user_by_email(db, email)


def search_users(db, key: str) -> list:
    return _impl().search_users(db, key)


def describe(db, user) -> tuple[str, str]:
    return _impl().describe(db, user)


def names_of(db, user) -> list[str]:
    return _impl().names_of(db, user)


def can(db, user, entity: str, action: str) -> bool:
    return _impl().can(db, user, entity, action)


def tool_defs(db, user=None) -> list:
    return _impl().tool_defs(db, user)


def run_tool(db, user, name: str, args: dict) -> dict:
    return _impl().run_tool(db, user, name, args)


def caller_context(db, user) -> str | None:
    return _impl().caller_context(db, user)


def skill_list(db, user, query: str = "", skill_set: str = "") -> dict:
    return _impl().skill_list(db, user, query, skill_set)


def skill_read(db, user, name: str) -> dict:
    return _impl().skill_read(db, user, name)


def skill_file(db, user, name: str, path: str) -> dict:
    return _impl().skill_file(db, user, name, path)


def glossary_block(db, texts: list[str]) -> str | None:
    return _impl().glossary_block(db, texts)


#  Chỉ những khóa này đi qua cổng — cổng B không phải cửa sửa cấu hình tùy ý.
#  ai-CR-216: thêm `agent_mcp_settings` (cấu hình cổng MCP, màn G7) — thiếu thì chế độ tách dịch vụ không lưu / đọc được.
SETTING_RAW_KEYS = ("assistant_glossary", "assistant_glossary_pending", "assistant_feature_gaps", "agent_mcp_settings")


def setting_raw_get(db, key: str) -> str:
    return _impl().setting_raw_get(db, key)


def setting_raw_put(db, key: str, value: str, user_id: int = 0) -> None:
    _impl().setting_raw_put(db, key, value, user_id)


def settings_snapshot(db=None) -> dict:
    """Ảnh chụp tab_setting (dịch vụ AI gọi qua cổng; ERP đọc thẳng)."""
    if is_remote():
        return _Remote.settings_snapshot(_impl())
    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            return _Local.settings_snapshot(db)
        finally:
            db.close()
    return _Local.settings_snapshot(db)


def create_draft(db, user, kind: str, draft: dict, source: int = 0) -> tuple[str, int]:
    return _impl().create_draft(db, user, kind, draft, source)


def submit_draft(db, user, kind: str, oid: int, source: int = 0) -> None:
    _impl().submit_draft(db, user, kind, oid, source)


def my_drafts(db, user) -> list[dict]:
    return _impl().my_drafts(db, user)


def update_leave_draft(db, user, oid: int, draft: dict, source: int = 0) -> str:
    return _impl().update_leave_draft(db, user, oid, draft, source)


def delete_my_drafts(db, user, items: list[dict], source: int = 0) -> dict:
    return _impl().delete_my_drafts(db, user, items, source)


def confirm_proposal(db, user, token: str, source: int = 0) -> dict:
    return _impl().confirm_proposal(db, user, token, source)


def update_doc_draft(db, user, kind: str, oid: int, draft: dict, mode: str, source: int = 0) -> dict:
    return _impl().update_doc_draft(db, user, kind, oid, draft, mode, source)


def my_changes(db, user, limit: int = 20) -> list[dict]:
    """ai-CR-182: sổ thay đổi bot đã ghi của CHÍNH người này (mới nhất trước), mỗi dòng kèm can_undo + undo_reason."""
    return _impl().my_changes(db, user, limit)


def undo_change(db, user, change_id: int, source: int = 0) -> dict:
    """ai-CR-182: hoàn tác một dòng sổ — ERP kiểm lại từ đầu; lỗi nghiệp vụ ném HTTPException (như confirm_proposal)."""
    return _impl().undo_change(db, user, change_id, source)


def created_details(db, kind: str, oid: int) -> list[str]:
    return _impl().created_details(db, kind, oid)


def tickets_open(db, statuses: list[str], exclude_ids: list[int], *, limit: int = 200) -> list[dict]:
    return _impl().tickets_open(db, statuses, exclude_ids, limit=limit)


def tickets_max_id(db) -> int:
    return _impl().tickets_max_id(db)


def tickets_by_ids(db, ids: list[int]) -> list[dict]:
    return _impl().tickets_by_ids(db, ids)


def ticket_note(db, ticket_id: int, body: str, *, status: str, by_user_id: int, clear_assignee: bool = False) -> None:
    _impl().ticket_note(db, ticket_id, body, status=status, by_user_id=by_user_id, clear_assignee=clear_assignee)


def create_ticket(db, user, *, subject: str, department: str, body: str) -> dict:
    return _impl().create_ticket(db, user, subject=subject, department=department, body=body)


def notifications_after(db, after_id: int, limit: int) -> list[dict]:
    return _impl().notifications_after(db, after_id, limit)


def notifications_max_id(db) -> int:
    return _impl().notifications_max_id(db)


def key_admin_people(db, admin, action: str, *, user_ids: list[int] | None = None, department_id: int = 0,
                     limit: int = 2000) -> list[dict] | None:
    """ai-CR-212: người (tài khoản đang hoạt động, có hồ sơ nhân sự) trong phạm vi `ai_mcp_key_admin.<action>` của
    `admin`; None = không có quyền."""
    return _impl().key_admin_people(db, admin, action, user_ids=user_ids, department_id=department_id, limit=limit)


def notify_users(db, user_ids: list[int], *, title: str, body: str, link: str, by_user_id: int = 0) -> int:
    return _impl().notify_users(db, user_ids, title=title, body=body, link=link, by_user_id=by_user_id)


def skill_stats(db) -> dict:
    """ai-CR-213: {skill_sets, skills} đang dùng ở Kho skill AI (ERP)."""
    return _impl().skill_stats(db)


def key_admin_employees(db, admin, action: str, employee_ids: list[int]) -> dict | None:
    """ai-CR-215: phát khóa theo hồ sơ nhân sự — {people, no_account, outside}; None = không có quyền."""
    return _impl().key_admin_employees(db, admin, action, employee_ids)


def attachment_blocks(db, user, ids: list[int]) -> tuple[list | None, list[dict]]:
    return _impl().attachment_blocks(db, user, ids)


def report_file(db, user, file_id: int) -> dict | None:
    return _impl().report_file(db, user, file_id)


def match_employee(db, name: str) -> dict | None:
    return _impl().match_employee(db, name)


def projects_for(db, user) -> list[dict]:
    return _impl().projects_for(db, user)


def plan_overview(db, user, list_id: int) -> dict:
    return _impl().plan_overview(db, user, list_id)


def plan_reply(db, user, task_id: int, action: str, text: str = "", pct: int | None = None,
               score: int | None = None) -> dict:
    return _impl().plan_reply(db, user, task_id, action, text=text, pct=pct, score=score)
