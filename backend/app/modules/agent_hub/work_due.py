"""NHẮC HẠN VIỆC DỰ ÁN cho đúng người được giao (ai-CR-175, T-14 của `doc/agent-hub/04`).

Đại ca 10/10/2026 (hướng trợ lý cá nhân): mỗi người chỉ nhận tin về VIỆC CỦA MÌNH. Ba mốc cho mỗi việc đang mở mình
phụ trách ở phân hệ Dự án: **trước hạn một ngày** · **sáng ngày hạn** · **khi đã quá hạn** (một lần, sáng hôm sau).
Một tin gộp mỗi sáng (mặc định 08:00 giờ VN, trong cửa sổ SEND_WINDOW để máy khởi động muộn vẫn gửi), mỗi mốc của mỗi
việc chỉ nhắc một lần — đánh dấu bằng mã `[vh:<id việc>:<mốc>]` ghi vào SỔ (không gửi lên Telegram), cùng cách nhắc họp.

Mặc định BẬT cho ai đã đăng nhập bot và chưa tắt chuông; tắt / đổi giờ bằng câu nhắn («tắt nhắc hạn việc», «nhắc hạn
việc lúc 7h»). Trạng thái ghi ở `tab_agent_brief_sub` với `kind = Kind.WORK_DUE` (dùng chung bảng bản tin, không thêm
bảng). Dữ liệu việc lấy qua `erp.run_tool(my_work_tasks)` dưới quyền của chính người đó — dịch vụ AI tách (phase 11)
không đọc thẳng bảng Dự án. Không có lượt model nào.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from enum import IntEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from .brief_subs import ALL_DAYS, SEND_WINDOW, Kind, day_bit
from .constants import ACT_WORK_DUE, DIR_OUT, NOTIFY_OFF
from .model import AgentBriefSub, AgentChatLink, AgentMessage
from .timeutil import LOCAL_OFFSET, now_utc

log = logging.getLogger("app.agent_hub.work_due")

DEFAULT_HOUR, DEFAULT_MINUTE = 8, 0
LOOKBACK_DAYS = 14             # chỉ soi sổ 14 ngày gần nhất để biết mốc nào đã nhắc
MAX_LINES = 12                 # mỗi mục tối đa chừng này việc, dư thì gộp một dòng đếm
_MARK = re.compile(r"\[vh:(\d+):([123])\]")


class Milestone(IntEnum):
    BEFORE = 1        # hạn ngày mai
    TODAY = 2         # hạn hôm nay
    OVERDUE = 3       # đã quá hạn


HEADINGS = {Milestone.BEFORE: "Hạn ngày mai", Milestone.TODAY: "Hạn hôm nay", Milestone.OVERDUE: "Đã quá hạn"}


# ---------------------------------------------------------------------------
# Trạng thái bật / tắt của từng người
# ---------------------------------------------------------------------------
def _row(db: Session, user_id: int) -> AgentBriefSub | None:
    return db.scalar(select(AgentBriefSub).where(AgentBriefSub.user_id == int(user_id),
                                                 AgentBriefSub.kind == Kind.WORK_DUE).order_by(AgentBriefSub.id).limit(1))


def state(db: Session, user_id: int) -> dict:
    row = _row(db, user_id)
    if row is None:
        return {"id": 0, "enabled": True, "hour": DEFAULT_HOUR, "minute": DEFAULT_MINUTE, "days": ALL_DAYS, "implicit": True}
    return {"id": row.id, "enabled": bool(row.enabled), "hour": row.hour, "minute": row.minute, "days": row.days,
            "implicit": False}


def set_state(db: Session, user_id: int, *, enabled: bool | None = None, hour: int | None = None,
              minute: int | None = None) -> dict:
    uid = int(user_id)
    if uid <= 0:
        raise ValueError("chat này chưa đăng nhập ERP")
    row = _row(db, uid)
    if row is None:
        row = AgentBriefSub(user_id=uid, kind=Kind.WORK_DUE, enabled=True, hour=DEFAULT_HOUR, minute=DEFAULT_MINUTE,
                            days=ALL_DAYS, created_by=uid, updated_by=uid)
        db.add(row)
    if enabled is not None:
        row.enabled = bool(enabled)
    if hour is not None:
        if not (0 <= int(hour) <= 23 and 0 <= int(minute or 0) <= 59):
            raise ValueError("giờ không hợp lệ")
        row.hour, row.minute = int(hour), int(minute or 0)
    row.updated_by = uid
    db.commit()
    return state(db, uid)


def state_text(db: Session, user_id: int) -> str:
    st = state(db, user_id)
    if not st["enabled"]:
        return "Nhắc hạn việc Dự án: <b>đang tắt</b>. Bật lại: «bật nhắc hạn việc»."
    return (f"Nhắc hạn việc Dự án: <b>đang bật</b>, mỗi sáng {st['hour']:02d}:{st['minute']:02d} — việc anh/chị phụ "
            "trách sắp tới hạn (trước 1 ngày), tới hạn hôm nay và vừa quá hạn; mỗi mốc nhắc một lần. "
            "Nhắn «tắt nhắc hạn việc» · «nhắc hạn việc lúc 7h» · «nhắc hạn việc hôm nay».")


# ---------------------------------------------------------------------------
# Gom việc theo mốc
# ---------------------------------------------------------------------------
def classify(items: list[dict], today: date) -> dict[Milestone, list[dict]]:
    """Việc có hạn → mốc. Hạn ngày mai → BEFORE; hôm nay → TODAY; đã qua → OVERDUE; xa hơn hay không hạn → bỏ."""
    out: dict[Milestone, list[dict]] = {m: [] for m in Milestone}
    t, tm = today.isoformat(), (today + timedelta(days=1)).isoformat()
    for it in items:
        due = str(it.get("due_date") or "")
        if not due:
            continue
        if due == tm:
            out[Milestone.BEFORE].append(it)
        elif due == t:
            out[Milestone.TODAY].append(it)
        elif due < t:
            out[Milestone.OVERDUE].append(it)
    return out


def already_sent(db: Session, chat_id: str, now: datetime) -> set[tuple[int, int]]:
    """(id việc, mốc) đã nhắc ở chat này trong LOOKBACK_DAYS ngày — đọc mã trong sổ."""
    seen: set[tuple[int, int]] = set()
    for body in db.scalars(select(AgentMessage.body).where(
            AgentMessage.chat_id == str(chat_id), AgentMessage.action == ACT_WORK_DUE,
            AgentMessage.created_at >= now - timedelta(days=LOOKBACK_DAYS))):
        for tid, m in _MARK.findall(body or ""):
            seen.add((int(tid), int(m)))
    return seen


def _dmy(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m")
    except ValueError:
        return iso


def compose(groups: dict[Milestone, list[dict]], today: date) -> tuple[str, str]:
    """→ (tin gửi, chuỗi mã đánh dấu ghi sổ). Tin rỗng nếu không có việc nào."""
    from .telegram import esc

    lines: list[str] = []
    marks: list[str] = []
    for m in Milestone:
        items = groups.get(m) or []
        if not items:
            continue
        lines.append(f"<b>{HEADINGS[m]}</b> ({len(items)}):")
        for it in items[:MAX_LINES]:
            extra = ""
            if m == Milestone.OVERDUE:
                try:
                    late = (today - date.fromisoformat(str(it.get("due_date")))).days
                except ValueError:
                    late = 0
                extra = f", hạn {esc(_dmy(str(it.get('due_date'))))}, trễ {late} ngày"
            lines.append(f"• {esc(str(it.get('title') or ''))[:90]} ({esc(str(it.get('project') or ''))[:40]}{extra})")
            marks.append(f"[vh:{int(it.get('id') or 0)}:{int(m)}]")
        if len(items) > MAX_LINES:
            lines.append(f"… và {len(items) - MAX_LINES} việc khác, xem ở phân hệ Dự án.")
        lines.append("")
    if not lines:
        return "", ""
    text = "<b>Việc Dự án của anh/chị</b>\n" + "\n".join(lines).rstrip() + \
        "\n<i>Em nhắc mỗi mốc một lần. Tắt: «tắt nhắc hạn việc».</i>"
    return text, " ".join(marks)


# ---------------------------------------------------------------------------
# Vòng nền
# ---------------------------------------------------------------------------
def _targets(db: Session, now: datetime) -> dict[int, str]:
    """user_id → chat Telegram riêng đang đăng nhập (chuông không tắt). Nhiều chat thì lấy chat mới nhất."""
    out: dict[int, str] = {}
    for link in db.scalars(select(AgentChatLink).where(
            AgentChatLink.chat_id != "", AgentChatLink.revoked_at.is_(None), AgentChatLink.expires_at > now)
            .order_by(AgentChatLink.id)):
        if int(link.notify_mode or NOTIFY_OFF) != NOTIFY_OFF and int(link.user_id or 0) > 0:
            out[int(link.user_id)] = str(link.chat_id)
    return out


def _due_now(st: dict, local: datetime) -> bool:
    if not st["enabled"] or not (int(st["days"]) & day_bit(local.weekday())):
        return False
    at = local.replace(hour=int(st["hour"]), minute=int(st["minute"]), second=0, microsecond=0)
    return at <= local < at + SEND_WINDOW


def _send(db: Session, chat_id: str, text: str, marks: str) -> None:
    from . import telegram

    try:
        mid = telegram.send(text, chat_id=chat_id)
    except telegram.TelegramError as e:
        mid, text = 0, f"[KHÔNG GỬI ĐƯỢC: {e}] {text}"
    db.add(AgentMessage(task_id=0, direction=DIR_OUT, chat_id=chat_id, tg_message_id=mid, body=f"{text} {marks}".strip(),
                        action=ACT_WORK_DUE))


def items_for(db: Session, user, today: date) -> list[dict]:
    """Việc đang mở mình phụ trách có hạn tới ngày mai (gồm quá hạn) — qua tool dưới quyền của chính người đó."""
    from . import erp

    out = erp.run_tool(db, user, "my_work_tasks", {"until": (today + timedelta(days=1)).isoformat(), "limit": 100})
    if not isinstance(out, dict) or out.get("error") or out.get("denied"):
        return []
    return list(out.get("items") or [])


def send_for_user(db: Session, user_id: int, chat_id: str, *, now: datetime | None = None, force: bool = False) -> bool:
    """Gộp và gửi tin nhắc hạn cho một người. `force` (lệnh «nhắc hạn việc hôm nay») bỏ qua dấu đã nhắc; trả True nếu gửi."""
    from . import erp

    now = now or now_utc()
    today = (now + LOCAL_OFFSET).date()
    user = erp.user_by_id(db, int(user_id))
    if user is None or not getattr(user, "is_active", True):
        return False
    groups = classify(items_for(db, user, today), today)
    if not force:
        seen = already_sent(db, chat_id, now)
        groups = {m: [it for it in v if (int(it.get("id") or 0), int(m)) not in seen] for m, v in groups.items()}
    text, marks = compose(groups, today)
    if not text:
        return False
    _send(db, chat_id, text, "" if force else marks)
    db.commit()
    return True


def tick(db: Session, *, now: datetime | None = None) -> dict:
    """Mỗi 5 phút: người nào tới giờ (mặc định 08:00), hôm nay chưa chạy → gom việc, gửi mốc chưa nhắc."""
    now = now or now_utc()
    local = now + LOCAL_OFFSET
    today = local.date().isoformat()
    sent = failed = 0
    for uid, chat_id in _targets(db, now).items():
        row = _row(db, uid)
        st = state(db, uid)
        if not _due_now(st, local) or (row is not None and row.last_sent_on == today):
            continue
        if row is None:
            row = AgentBriefSub(user_id=uid, kind=Kind.WORK_DUE, enabled=True, hour=DEFAULT_HOUR, minute=DEFAULT_MINUTE,
                                days=ALL_DAYS, created_by=0, updated_by=0)
            db.add(row)
        row.last_sent_on = today            # đánh dấu TRƯỚC: gửi hỏng cũng không lặp cả ngày
        db.commit()
        try:
            if send_for_user(db, uid, chat_id, now=now):
                sent += 1
        except Exception:  # noqa: BLE001 — một người hỏng không chặn người khác
            db.rollback()
            failed += 1
            log.exception("agent_hub: nhắc hạn việc của user %s hỏng", uid)
    return {"sent": sent, "failed": failed}


# ---------------------------------------------------------------------------
# Câu nhắn
# ---------------------------------------------------------------------------
_ON_OFF = re.compile(r"^(?P<op>bat|tat|mo|ngung|thoi)\s+nhac\s+han(?:\s+viec)?(?:\s+du\s+an)?$")
_AT = re.compile(r"^(?:dat\s+|doi\s+)?nhac\s+han(?:\s+viec)?(?:\s+du\s+an)?\s+(?:luc|vao)\s+(?P<rest>.+)$")
_NOW = re.compile(r"^nhac\s+han(?:\s+viec)?(?:\s+du\s+an)?\s+hom\s+nay$")
_SHOW = re.compile(r"^(?:xem\s+)?nhac\s+han(?:\s+viec)?(?:\s+du\s+an)?(?:\s+cua\s+(?:toi|anh|em|chi|minh))?$")


def parse_command(text: str) -> dict | None:
    """«tắt nhắc hạn việc» · «bật nhắc hạn việc» · «nhắc hạn việc lúc 7h» · «nhắc hạn việc hôm nay» · «nhắc hạn việc»."""
    from app.modules.assistant.glossary import fold

    f = " ".join(fold((text or "").strip().rstrip(".!?")).split())
    if m := _ON_OFF.match(f):
        return {"op": "on" if m.group("op") in ("bat", "mo") else "off"}
    if m := _AT.match(f):
        return {"op": "at", "rest": m.group("rest")}
    if _NOW.match(f):
        return {"op": "now"}
    if _SHOW.match(f):
        return {"op": "show"}
    return None
