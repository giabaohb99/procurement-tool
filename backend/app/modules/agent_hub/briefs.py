"""BẢN TIN SÁNG (T-08) và NHẮC TRƯỚC HỌP (T-09) — ai-CR-064, phase 5.

Chạy cho người đã nối CẢ Telegram (chat đang đăng nhập, chuông không tắt) LẪN Google. Đọc lịch bằng token
của chính người đó; việc chờ duyệt lấy từ tool `my_approval_tasks` dưới quyền của họ. Không có lượt model
nào — chỉ ghép chữ, nên không tốn khóa Gemini.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import google_link, telegram
from .constants import ACT_BRIEF, ACT_MEETING, DIR_OUT, NOTIFY_OFF
from .model import AgentChatLink, AgentGoogleLink, AgentMessage
from .timeutil import LOCAL_OFFSET, now_local, now_utc

MEETING_LEAD_MIN = 15          # nhắc khi cuộc họp bắt đầu trong 10–20 phút tới (vòng chạy mỗi 5 phút)
MEETING_WINDOW_MIN = 10


def _targets(db: Session, now: datetime) -> list[tuple[AgentGoogleLink, list[AgentChatLink]]]:
    """Mỗi người đã nối Google → các chat Telegram đang đăng nhập của họ (chuông không tắt)."""
    out = []
    for g in db.scalars(select(AgentGoogleLink).where(AgentGoogleLink.revoked_at.is_(None))):
        chats = [c for c in db.scalars(select(AgentChatLink).where(
            AgentChatLink.user_id == g.user_id, AgentChatLink.chat_id != "", AgentChatLink.revoked_at.is_(None),
            AgentChatLink.expires_at > now)) if int(c.notify_mode or 0) != NOTIFY_OFF]
        if chats:
            out.append((g, chats))
    return out


def _send(db: Session, chat_id: str, text: str, action: str) -> None:
    try:
        mid = telegram.send(text, chat_id=chat_id)
    except telegram.TelegramError as e:
        mid, text = 0, f"[KHÔNG GỬI ĐƯỢC: {e}] {text}"
    db.add(AgentMessage(task_id=0, direction=DIR_OUT, chat_id=chat_id, tg_message_id=mid, body=text, action=action))


def _hhmm(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%H:%M")
    except ValueError:
        return ""


def morning_text(db: Session, user, events: list[dict]) -> str:
    from app.modules.assistant.tools import run_tool

    esc = telegram.esc
    lines = [f"<b>Sáng {now_local():%d/%m}</b>"]
    if events:
        lines.append(f"Lịch hôm nay ({len(events)}):")
        for ev in events[:10]:
            when = "cả ngày" if ev.get("all_day") else _hhmm(str(ev.get("start") or ""))
            loc = f" · {esc(ev['location'])}" if ev.get("location") else ""
            lines.append(f"• {when} {esc(ev['title'])}{loc}")
    else:
        lines.append("Hôm nay lịch trống.")
    try:
        tasks = run_tool(db, user, "my_approval_tasks", {"limit": 10})
        items = tasks.get("items") or []
        if items:
            lines.append(f"Chờ anh/chị duyệt ({tasks.get('total') or len(items)}):")
            for t in items[:5]:
                lines.append(f"• {esc(str(t.get('doc_code') or t.get('code') or ''))} {esc(str(t.get('title') or t.get('subject') or ''))[:60]}")
    except Exception:  # noqa: BLE001 — thiếu quyền hay tool lỗi thì bỏ mục này, bản tin vẫn đi
        pass
    return "\n".join(lines)


def send_morning_briefs(db: Session, *, now: datetime | None = None) -> int:
    from app.modules.user.model import User

    from app.modules.assistant.tools.google_tool import list_events

    now = now or now_utc()
    sent = 0
    for g, chats in _targets(db, now):
        user = db.get(User, g.user_id)
        if user is None or not user.is_active:
            continue
        try:
            events = list_events(db, g)
        except google_link.GoogleError as e:
            events, note = [], str(e)
        else:
            note = ""
        text = morning_text(db, user, events) + (f"\n(Không đọc được lịch Google: {telegram.esc(note[:120])})" if note else "")
        for c in chats:
            _send(db, c.chat_id, text, ACT_BRIEF)
            sent += 1
    if sent:
        db.commit()
    return sent


def _already_reminded(db: Session, chat_id: str, event_id: str, now: datetime) -> bool:
    return db.scalar(select(AgentMessage.id).where(
        AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_MEETING,
        AgentMessage.body.contains(f"[{event_id}]"), AgentMessage.created_at >= now - timedelta(hours=6)).limit(1)) is not None


def send_meeting_reminders(db: Session, *, now: datetime | None = None) -> int:
    """Sự kiện bắt đầu trong (lead - window, lead] phút tới → một tin «Sắp họp» mỗi sự kiện mỗi chat."""
    from app.modules.assistant.tools.google_tool import list_events

    now = now or now_utc()
    local = now + LOCAL_OFFSET
    lo, hi = now + timedelta(minutes=MEETING_LEAD_MIN - MEETING_WINDOW_MIN), now + timedelta(minutes=MEETING_LEAD_MIN)
    sent = 0
    for g, chats in _targets(db, now):
        try:
            events = list_events(db, g, local.date().isoformat(), local.date().isoformat())
        except google_link.GoogleError:
            continue
        for ev in events:
            if ev.get("all_day") or not ev.get("start"):
                continue
            try:
                start = datetime.fromisoformat(str(ev["start"]))
            except ValueError:
                continue
            start_utc = start.replace(tzinfo=None) - (start.utcoffset() or LOCAL_OFFSET)
            if not (lo < start_utc <= hi):
                continue
            for c in chats:
                if _already_reminded(db, c.chat_id, str(ev["id"]), now):
                    continue
                esc = telegram.esc
                text = (f"<b>Sắp họp</b> lúc {esc(_hhmm(str(ev['start'])))}: {esc(ev['title'])}"
                        + (f" · {esc(ev['location'])}" if ev.get("location") else "")
                        + (f"\n{esc(ev['meet'])}" if ev.get("meet") else "") + f" [{esc(str(ev['id']))}]")
                _send(db, c.chat_id, text, ACT_MEETING)
                sent += 1
    if sent:
        db.commit()
    return sent
