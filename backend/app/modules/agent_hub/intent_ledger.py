"""Sổ ý định (ai-CR-137, phase 13.1–13.2 «Hiểu ý định + tự ghi nhớ», đại ca duyệt 09/10/2026).

Mỗi câu hỏi người dùng gửi bot (Telegram / Zalo riêng) hoặc Trợ lý AI web = MỘT dòng `tab_agent_intent`:
ai hỏi · kênh · cuộc nào (scope + scope_key, dùng lại khóa của nén hội thoại ai-CR-136) · nhãn lớn (6 nhãn của bộ phân
loại) · nhãn con theo nghiệp vụ · các đối tượng nhắc tới (NCC, pháp nhân, dự án, phòng, mã chứng từ…) · công cụ đã gọi ·
kết cục (trả lời được / phải hỏi lại / lỗi).

Ba luật cứng:
  1. KHÔNG lưu nguyên văn câu hỏi. Đối tượng chỉ lấy từ các THAM SỐ ĐỊNH DANH của công cụ (bảng `_ENTITY_ARGS`) và mã
     chứng từ dò bằng mẫu — tham số chữ tự do (`query`, `question`, `content`…) không bao giờ vào sổ.
  2. Nhãn con suy ra TẤT ĐỊNH từ công cụ đã gọi (`TOOL_SUB`), không hỏi model đoán: công cụ ghi / soạn nháp thắng công cụ
     đọc; không gọi công cụ nào thì theo nhãn lớn.
  3. Ghi sổ hỏng không bao giờ làm hỏng câu trả lời (nuốt lỗi, ghi log). Giữ RETENTION_DAYS ngày, vòng dọn hằng ngày.
"""
from __future__ import annotations

import logging
import re
from datetime import timedelta
from enum import IntEnum

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import channels
from .constants import CONV_CHAT
from .model import AgentIntent
from .timeutil import now_utc

log = logging.getLogger("app.agent_hub.intent_ledger")

RETENTION_DAYS = 180
MAX_ENTITIES = 10
MAX_TOOLS = 12
VALUE_MAX = 80


class Intent(IntEnum):
    """Nhãn lớn — đúng 6 nhãn của bộ phân loại (`manager.INTENT_*`)."""
    ASK = 1        # hoi
    TASK = 2       # viec — giao việc sửa phần mềm
    UNSURE = 3     # mo_ho
    ACT = 4        # thao_tac — thao tác trên việc của bot
    RESEARCH = 5   # tra_cuu — tìm web / đọc link / tài liệu
    DATA = 6       # du_lieu — sửa dữ liệu bằng lời


INTENT_CODES = {Intent.ASK: "hoi", Intent.TASK: "viec", Intent.UNSURE: "mo_ho", Intent.ACT: "thao_tac",
                Intent.RESEARCH: "tra_cuu", Intent.DATA: "du_lieu"}
_INTENT_BY_CODE = {v: k for k, v in INTENT_CODES.items()}


class Channel(IntEnum):
    WEB = 1
    TELEGRAM = 2
    ZALO = 3


class Outcome(IntEnum):
    OK = 1          # trả lời được
    CLARIFY = 2     # bot phải hỏi lại người dùng
    ERROR = 3       # lỗi (nhà cung cấp, khóa, công cụ…)


OUTCOME_LABELS = {Outcome.OK: "Trả lời được", Outcome.CLARIFY: "Phải hỏi lại", Outcome.ERROR: "Lỗi"}


class Sub(IntEnum):
    """Nhãn con theo nghiệp vụ. Số đã cấp không đổi / không tái dùng. 20–49 tra cứu · 50–79 thao tác ghi."""
    ASK_GENERAL = 10
    LOOKUP_PAYABLE = 20
    LOOKUP_PURCHASE = 21
    LOOKUP_APPROVAL = 22
    LOOKUP_SUPPLIER = 23
    LOOKUP_CONTRACT = 24
    LOOKUP_PRODUCT = 25
    LOOKUP_CUSTOMS = 26
    LOOKUP_DOCUMENT = 27
    LOOKUP_DRIVE = 28
    LOOKUP_EMPLOYEE = 29
    LOOKUP_LEAVE = 30
    LOOKUP_CALENDAR = 31
    LOOKUP_GROUP = 32
    LOOKUP_MEETING = 33
    LOOKUP_PERSONAL = 34
    LOOKUP_TICKET = 35
    LOOKUP_GUIDE = 36
    LOOKUP_ANALYTICS = 37
    LOOKUP_OTHER = 49
    MAKE_PURCHASE_REQUEST = 50
    MAKE_SURVEY_REQUEST = 51
    MAKE_PAYMENT_REQUEST = 52
    MAKE_LEAVE = 53
    MAKE_WORK_TASK = 54
    MAKE_TICKET = 55
    WRITE_CALENDAR = 56
    WRITE_MEMORY = 57
    EXPORT_FILE = 58
    PROPOSE_CHANGE = 59
    FEEDBACK = 60
    MEETING_MINUTES = 61
    BOT_TASK_ACTION = 62
    WRITE_OTHER = 79
    RESEARCH_WEB = 80
    RESEARCH_LINK = 81
    RESEARCH_DOCUMENT = 82
    BOT_TASK = 90
    DATA_CHANGE = 91


SUB_CODES: dict[Sub, tuple[str, str]] = {
    Sub.ASK_GENERAL: ("hoi.chung", "Hỏi chung, không tra dữ liệu"),
    Sub.LOOKUP_PAYABLE: ("tra_cuu.cong_no", "Công nợ, thanh toán"),
    Sub.LOOKUP_PURCHASE: ("tra_cuu.mua_hang", "Mua hàng (YCMH · YCBG · ĐMH)"),
    Sub.LOOKUP_APPROVAL: ("tra_cuu.duyet", "Việc chờ duyệt, luồng duyệt"),
    Sub.LOOKUP_SUPPLIER: ("tra_cuu.ncc", "Nhà cung cấp"),
    Sub.LOOKUP_CONTRACT: ("tra_cuu.hop_dong", "Hợp đồng"),
    Sub.LOOKUP_PRODUCT: ("tra_cuu.san_pham", "Sản phẩm, giá mua"),
    Sub.LOOKUP_CUSTOMS: ("tra_cuu.hai_quan", "Hải quan, giá thị trường"),
    Sub.LOOKUP_DOCUMENT: ("tra_cuu.van_ban", "Văn bản"),
    Sub.LOOKUP_DRIVE: ("tra_cuu.drive", "Google Drive"),
    Sub.LOOKUP_EMPLOYEE: ("tra_cuu.nhan_su", "Nhân sự"),
    Sub.LOOKUP_LEAVE: ("tra_cuu.nghi_phep", "Nghỉ phép"),
    Sub.LOOKUP_CALENDAR: ("tra_cuu.lich", "Lịch"),
    Sub.LOOKUP_GROUP: ("tra_cuu.nhom", "Nhóm chat"),
    Sub.LOOKUP_MEETING: ("tra_cuu.hop", "Cuộc họp"),
    Sub.LOOKUP_PERSONAL: ("tra_cuu.ca_nhan", "Sổ nhớ, ghi chú, lịch sử chat"),
    Sub.LOOKUP_TICKET: ("tra_cuu.ho_tro", "Phiếu hỗ trợ"),
    Sub.LOOKUP_GUIDE: ("tra_cuu.huong_dan", "Hướng dẫn, thuật ngữ"),
    Sub.LOOKUP_ANALYTICS: ("tra_cuu.phan_tich", "Phân tích số liệu"),
    Sub.LOOKUP_OTHER: ("tra_cuu.khac", "Tra cứu khác"),
    Sub.MAKE_PURCHASE_REQUEST: ("thao_tac.tao_ycmh", "Soạn YCMH"),
    Sub.MAKE_SURVEY_REQUEST: ("thao_tac.tao_ycbg", "Soạn YCBG"),
    Sub.MAKE_PAYMENT_REQUEST: ("thao_tac.tao_yctt", "Soạn YCTT"),
    Sub.MAKE_LEAVE: ("thao_tac.tao_nghi_phep", "Soạn đơn nghỉ phép"),
    Sub.MAKE_WORK_TASK: ("thao_tac.tao_viec", "Soạn việc dự án"),
    Sub.MAKE_TICKET: ("thao_tac.tao_ho_tro", "Tạo phiếu hỗ trợ"),
    Sub.WRITE_CALENDAR: ("thao_tac.lich", "Đặt / sửa lịch"),
    Sub.WRITE_MEMORY: ("thao_tac.ghi_nho", "Ghi nhớ, ghi chú, thẻ cá nhân"),
    Sub.EXPORT_FILE: ("thao_tac.xuat_file", "Xuất tệp"),
    Sub.PROPOSE_CHANGE: ("thao_tac.de_xuat_sua", "Đề xuất sửa phiếu / lập tài khoản"),
    Sub.FEEDBACK: ("thao_tac.gop_y", "Góp thuật ngữ, báo thiếu chức năng"),
    Sub.MEETING_MINUTES: ("thao_tac.bien_ban", "Biên bản họp"),
    Sub.BOT_TASK_ACTION: ("thao_tac.viec_bot", "Thao tác trên việc của bot"),
    Sub.WRITE_OTHER: ("thao_tac.khac", "Thao tác khác"),
    Sub.RESEARCH_WEB: ("nghien_cuu.web", "Tìm trên mạng"),
    Sub.RESEARCH_LINK: ("nghien_cuu.link", "Đọc link"),
    Sub.RESEARCH_DOCUMENT: ("nghien_cuu.tai_lieu", "Đọc tài liệu"),
    Sub.BOT_TASK: ("viec.ghi", "Giao việc sửa phần mềm"),
    Sub.DATA_CHANGE: ("du_lieu.sua", "Sửa dữ liệu bằng lời"),
}

#  Công cụ → nhãn con. Thêm công cụ mới mà quên khai ở đây thì bài kiểm `test_moi_cong_cu_deu_co_nhan_con` đỏ.
TOOL_SUB: dict[str, Sub] = {
    "payable_lookup": Sub.LOOKUP_PAYABLE, "payment_request_read": Sub.LOOKUP_PAYABLE,
    "purchase_report": Sub.LOOKUP_PURCHASE, "recent_purchase_orders": Sub.LOOKUP_PURCHASE,
    "recent_purchases": Sub.LOOKUP_PURCHASE, "my_procurement_requests": Sub.LOOKUP_PURCHASE,
    "procurement_doc_read": Sub.LOOKUP_PURCHASE, "my_requests_status": Sub.LOOKUP_APPROVAL,
    "pending_procurement_approvals": Sub.LOOKUP_APPROVAL, "my_approval_tasks": Sub.LOOKUP_APPROVAL,
    "approval_flow_lookup": Sub.LOOKUP_APPROVAL,
    "supplier_search": Sub.LOOKUP_SUPPLIER, "suppliers_for_product": Sub.LOOKUP_SUPPLIER,
    "top_suppliers_by_purchase": Sub.LOOKUP_SUPPLIER,
    "supplier_contracts": Sub.LOOKUP_CONTRACT, "contract_count_by_status": Sub.LOOKUP_CONTRACT,
    "contract_list_by_expiry": Sub.LOOKUP_CONTRACT,
    "product_search": Sub.LOOKUP_PRODUCT, "product_best_price": Sub.LOOKUP_PRODUCT,
    "product_purchase_history": Sub.LOOKUP_PRODUCT,
    "customs_price_stats": Sub.LOOKUP_CUSTOMS, "customs_buy_timing": Sub.LOOKUP_CUSTOMS,
    "customs_market": Sub.LOOKUP_CUSTOMS, "customs_legal_check": Sub.LOOKUP_CUSTOMS,
    "document_read": Sub.LOOKUP_DOCUMENT, "document_search": Sub.LOOKUP_DOCUMENT, "my_documents": Sub.LOOKUP_DOCUMENT,
    "drive_read": Sub.LOOKUP_DRIVE, "drive_search": Sub.LOOKUP_DRIVE,
    "employee_lookup": Sub.LOOKUP_EMPLOYEE, "my_leave_summary": Sub.LOOKUP_LEAVE,
    "my_calendar_events": Sub.LOOKUP_CALENDAR,
    "list_my_groups": Sub.LOOKUP_GROUP, "read_group_messages": Sub.LOOKUP_GROUP, "read_group_file": Sub.LOOKUP_GROUP,
    "latest_meeting_report": Sub.LOOKUP_MEETING, "list_my_meetings": Sub.LOOKUP_MEETING,
    "search_notes": Sub.LOOKUP_PERSONAL, "search_chat_history": Sub.LOOKUP_PERSONAL,
    "list_personal_items": Sub.LOOKUP_PERSONAL,
    "my_tickets": Sub.LOOKUP_TICKET,
    "search_docs": Sub.LOOKUP_GUIDE, "glossary_lookup": Sub.LOOKUP_GUIDE,
    "analytics_query": Sub.LOOKUP_ANALYTICS,
    "draft_purchase_request": Sub.MAKE_PURCHASE_REQUEST, "draft_survey_request": Sub.MAKE_SURVEY_REQUEST,
    "draft_payment_request": Sub.MAKE_PAYMENT_REQUEST, "draft_leave_request": Sub.MAKE_LEAVE,
    "draft_work_task": Sub.MAKE_WORK_TASK, "ticket_create": Sub.MAKE_TICKET,
    "create_calendar_event": Sub.WRITE_CALENDAR, "update_calendar_event": Sub.WRITE_CALENDAR,
    "delete_calendar_event": Sub.WRITE_CALENDAR,
    "remember_fact": Sub.WRITE_MEMORY, "forget_fact": Sub.WRITE_MEMORY, "save_note": Sub.WRITE_MEMORY,
    "add_personal_item": Sub.WRITE_MEMORY, "mark_personal_item": Sub.WRITE_MEMORY,
    "export_excel_file": Sub.EXPORT_FILE, "export_report_file": Sub.EXPORT_FILE,
    "propose_document_update": Sub.PROPOSE_CHANGE, "propose_account_setup": Sub.PROPOSE_CHANGE,
    "propose_glossary_term": Sub.FEEDBACK, "report_missing_feature": Sub.FEEDBACK,
    "rewrite_meeting_minutes": Sub.MEETING_MINUTES, "save_meeting_template": Sub.MEETING_MINUTES,
}

#  Chế độ nghiên cứu (`research.MODE_*`) → nhãn con; "doc" = link tới TỆP đọc như tệp gửi thẳng (ai-CR-134).
_RESEARCH_SUB = {"web": Sub.RESEARCH_WEB, "kiem_chung": Sub.RESEARCH_WEB, "doc_link": Sub.RESEARCH_LINK,
                 "tai_lieu": Sub.RESEARCH_DOCUMENT, "doc": Sub.RESEARCH_DOCUMENT}
_NO_TOOL_SUB = {Intent.ASK: Sub.ASK_GENERAL, Intent.UNSURE: Sub.ASK_GENERAL, Intent.TASK: Sub.BOT_TASK,
                Intent.ACT: Sub.BOT_TASK_ACTION, Intent.DATA: Sub.DATA_CHANGE, Intent.RESEARCH: Sub.RESEARCH_WEB}

#  Tham số ĐỊNH DANH của công cụ → (loại đối tượng, dạng giá trị). Chỉ những tham số này vào sổ; `entity` của công cụ
#  là LOẠI chứng từ (purchase_order…) chứ không phải pháp nhân, nên không có ở đây.
_ENTITY_ARGS: dict[str, tuple[str, str]] = {
    "supplier_code": ("ncc", "code"), "supplier": ("ncc", "ref"),
    "product_code": ("san_pham", "code"),
    "company": ("phap_nhan", "ref"),
    "department_id": ("phong", "id"), "department": ("phong", "ref"),
    "project": ("du_an", "ref"),
    "employee": ("nhan_su", "ref"),
    "code": ("chung_tu", "code"),
}
#  Mã chứng từ dò trong câu (PO00045, PYC00012, YCBG00034, YCTT00045, ĐMH-0012…): chỉ lấy MÃ, không lấy câu.
_DOC_CODE_RE = re.compile(r"(?<![\w])((?:PO|PYC|YCMH|YCBG|YCKS|YCTT|DMH|ĐMH|PNK|HĐ|HD)[-_]?\d{2,}[\w-]*)", re.IGNORECASE)
_ASK_BACK_RE = re.compile(r"\?\s*$")


def intent_of(code: str) -> Intent:
    return _INTENT_BY_CODE.get(str(code or "").strip(), Intent.ASK)


def channel_of(chat_id: str) -> Channel:
    return Channel.ZALO if channels.is_zalo(chat_id) or channels.is_zalo_account(chat_id) else Channel.TELEGRAM


def is_group_chat(chat_id: str) -> bool:
    """Telegram nhóm = mã âm; Zalo nhóm = tiền tố `zg:`. Sổ ý định và tự rút ghi nhớ KHÔNG BAO GIỜ đọc nhóm."""
    s = str(chat_id or "")
    return s.startswith("-") or s.startswith(channels.ZALO_GROUP_PREFIX)


def tool_names(tool_calls) -> list[str]:
    out: list[str] = []
    for c in tool_calls or []:
        name = str((c.get("name") if isinstance(c, dict) else c) or "").strip()
        if name and name not in out:
            out.append(name[:60])
    return out[:MAX_TOOLS]


def sub_of(intent: Intent, tools: list[str], mode: str = "") -> Sub:
    """Nhãn con TẤT ĐỊNH: công cụ ghi / soạn nháp thắng công cụ đọc; không có công cụ thì theo nhãn lớn."""
    subs = [TOOL_SUB.get(t, Sub.LOOKUP_OTHER) for t in tools]
    writes = [s for s in subs if 50 <= s < 80]
    if writes:
        return writes[0]
    if subs:
        return subs[0]
    if intent == Intent.RESEARCH:
        return _RESEARCH_SUB.get(mode, Sub.RESEARCH_WEB)
    return _NO_TOOL_SUB.get(intent, Sub.ASK_GENERAL)


def sub_code(value: int) -> str:
    try:
        return SUB_CODES[Sub(int(value))][0]
    except (ValueError, KeyError):
        return ""


def _clip(v) -> str:
    return " ".join(str(v).split())[:VALUE_MAX]


def entities_of(tool_calls, question: str = "") -> list[dict]:
    """Đối tượng nhắc tới: tham số định danh của công cụ (ưu tiên id / mã hơn tên) + mã chứng từ dò trong câu."""
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, form: str, value) -> None:
        if value in (None, "", 0) or isinstance(value, (dict, list, bool)):
            return
        val = _clip(value)
        if form == "id":
            try:
                ival = int(value)
            except (TypeError, ValueError):
                return
            if ival <= 0:
                return
            val = str(ival)
        if form == "code":
            val = val.upper()
        key = (kind, val.casefold())
        if not val or key in seen or len(out) >= MAX_ENTITIES:
            return
        seen.add(key)
        out.append({"type": kind, form: int(val) if form == "id" else val})

    for c in tool_calls or []:
        args = c.get("args") if isinstance(c, dict) else None
        if not isinstance(args, dict):
            continue
        for arg, (kind, form) in _ENTITY_ARGS.items():
            if arg in args:
                add(kind, form, args[arg])
    for m in _DOC_CODE_RE.finditer(question or ""):
        add("chung_tu", "code", m.group(1))
    return out


def outcome_of(text: str, *, error: bool = False, tools: list[str] | None = None) -> Outcome:
    """Lỗi → ERROR. Câu trả lời KHÔNG dùng công cụ nào và kết bằng dấu hỏi → bot đang hỏi lại. Còn lại OK."""
    if error:
        return Outcome.ERROR
    body = (text or "").strip()
    if not tools and body and _ASK_BACK_RE.search(body.splitlines()[-1]):
        return Outcome.CLARIFY
    return Outcome.OK


def record(db: Session, *, user_id: int, channel: Channel, scope_key: str, intent, scope: int = CONV_CHAT,
           tool_calls=None, mode: str = "", question: str = "", answer: str = "", error: bool = False) -> AgentIntent | None:
    """Ghi MỘT dòng. `question` chỉ dùng để dò mã chứng từ, KHÔNG lưu. Hỏng thì nuốt lỗi — câu trả lời đã đi rồi."""
    uid = int(user_id or 0)
    if uid <= 0 or (scope == CONV_CHAT and is_group_chat(scope_key)):
        return None
    try:
        big = intent if isinstance(intent, Intent) else intent_of(str(intent or ""))
        tools = tool_names(tool_calls)
        row = AgentIntent(
            user_id=uid, channel=int(channel), scope=int(scope), scope_key=str(scope_key or "")[:80],
            intent=int(big), sub_intent=int(sub_of(big, tools, mode)), entities=entities_of(tool_calls, question),
            tools=tools, outcome=int(outcome_of(answer, error=error, tools=tools)),
            created_by=uid, updated_by=uid)
        db.add(row)
        db.commit()
        return row
    except Exception:  # noqa: BLE001 — sổ ý định không bao giờ được làm hỏng câu trả lời
        db.rollback()
        log.exception("agent_hub: không ghi được sổ ý định")
        return None


def recent(db: Session, user_id: int, *, days: int = 30, limit: int = 300) -> list[AgentIntent]:
    since = now_utc() - timedelta(days=days)
    return list(db.scalars(select(AgentIntent).where(
        AgentIntent.user_id == int(user_id), AgentIntent.created_at >= since)
        .order_by(AgentIntent.id.desc()).limit(limit)))


def habit_lines(db: Session, user_id: int, *, days: int = 30, top: int = 6) -> list[str]:
    """Tóm sổ ý định của MỘT người thành vài dòng đếm (nhãn con, đối tượng hay nhắc) — đầu vào cho tự rút ghi nhớ."""
    rows = recent(db, user_id, days=days)
    if not rows:
        return []
    subs: dict[str, int] = {}
    ents: dict[str, int] = {}
    for r in rows:
        code = sub_code(r.sub_intent)
        if code:
            subs[code] = subs.get(code, 0) + 1
        for e in r.entities or []:
            if not isinstance(e, dict):
                continue
            val = e.get("code") or e.get("ref") or e.get("id")
            if val:
                key = f"{e.get('type')}: {val}"
                ents[key] = ents.get(key, 0) + 1
    lines = [f"- {k}: {n} lần" for k, n in sorted(subs.items(), key=lambda x: -x[1])[:top]]
    lines += [f"- hay nhắc {k} ({n} lần)" for k, n in sorted(ents.items(), key=lambda x: -x[1])[:top] if n >= 2]
    return lines


def purge(db: Session, *, days: int = RETENTION_DAYS) -> int:
    res = db.execute(delete(AgentIntent).where(AgentIntent.created_at < now_utc() - timedelta(days=days)))
    db.commit()
    return int(res.rowcount or 0)


def forget_user(db: Session, user_id: int) -> int:
    """Thu hồi / nghỉ việc: xóa sạch sổ ý định của người đó (dùng ở đợt B, 13.4)."""
    res = db.execute(delete(AgentIntent).where(AgentIntent.user_id == int(user_id)))
    db.commit()
    return int(res.rowcount or 0)
