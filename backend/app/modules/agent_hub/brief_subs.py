"""BẢN TIN bật / tắt ngay trong chat (ai-CR-140 — đại ca 09/10/2026: «cần bản tin hằng ngày, hoặc danh sách việc hôm nay,
bật tắt trong khi chat được không»).

Hai loại, mỗi người tự đăng ký (`tab_agent_brief_sub`):
  · BẢN TIN SÁNG (`Kind.DAILY`, mỗi người tối đa một): lịch Google hôm nay (nếu đã nối) · việc riêng · việc Dự án tới hạn /
    quá hạn (`my_work_tasks`) · phiếu chờ mình duyệt. Chỉ ghép chữ, không tốn lượt model. Giờ + thứ chỉnh được.
  · BẢN TIN CHỦ ĐỀ (`Kind.TOPIC`, tối đa MAX_TOPICS): một câu hỏi chạy qua Trợ lý AI như người đó tự hỏi, bằng khóa của
    chính họ, vào giờ + thứ đã chọn — vd «sáng thứ hai gửi anh công nợ quá hạn của DEGO». Nguồn: lệnh chat (model gọi tool
    `manage_briefs`) hoặc nút «Bật» trên đề xuất chủ động của 13.5.

Người đã nối Google mà CHƯA có dòng bản tin sáng = đang bật 07:30 mọi ngày (giữ đúng hành vi cũ của ai-CR-064). Tắt là ghi
một dòng `enabled = False`.

Vòng nền mỗi 5 phút (`tick`): dòng nào tới giờ (trong cửa sổ SEND_WINDOW sau giờ hẹn, để máy khởi động lại muộn vẫn gửi
nhưng không gửi bản tin sáng lúc 6 giờ chiều), đúng thứ, hôm nay chưa gửi → đánh dấu đã gửi TRƯỚC rồi mới gửi (gửi hỏng
cũng không lặp lại cả ngày). Bot không tự gửi gì người dùng chưa bật.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from enum import IntEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import AgentBriefSub, AgentGoogleLink
from .timeutil import LOCAL_OFFSET, now_utc

log = logging.getLogger("app.agent_hub.brief_subs")

MAX_TOPICS = 10
TOPIC_MAX = 300
SEND_WINDOW = timedelta(hours=3)
ALL_DAYS = 127
WORKDAYS = 63                       # thứ hai → thứ bảy
DEFAULT_HOUR, DEFAULT_MINUTE = 7, 30
_DAY_NAMES = ("thứ hai", "thứ ba", "thứ tư", "thứ năm", "thứ sáu", "thứ bảy", "chủ nhật")


class Kind(IntEnum):
    DAILY = 1
    TOPIC = 2
    WORK_DUE = 3       # ai-CR-175: nhắc hạn việc Dự án — vòng riêng ở `work_due.py`, không phải bản tin


KIND_LABELS = {Kind.DAILY: "Bản tin sáng", Kind.TOPIC: "Bản tin chủ đề", Kind.WORK_DUE: "Nhắc hạn việc Dự án"}


def day_bit(weekday: int) -> int:
    """`weekday` theo Python (thứ hai = 0) → bit trong `days`."""
    return 1 << int(weekday)


def days_text(mask: int) -> str:
    mask = int(mask or 0) & ALL_DAYS
    if mask == ALL_DAYS:
        return "mọi ngày"
    if mask == WORKDAYS:
        return "thứ hai → thứ bảy"
    if mask == 31:
        return "thứ hai → thứ sáu"
    return ", ".join(n for i, n in enumerate(_DAY_NAMES) if mask & day_bit(i)) or "không ngày nào"


def parse_days(values) -> int:
    """['thứ hai', 'T2', 'chủ nhật', 0, 6] / 'mọi ngày' / 'ngày thường' → mặt nạ. Rỗng → mọi ngày."""
    from app.modules.assistant.glossary import fold

    if values in (None, "", []):
        return ALL_DAYS
    items = values if isinstance(values, list) else [values]
    mask = 0
    for v in items:
        if isinstance(v, int) and 0 <= v <= 6:
            mask |= day_bit(v)
            continue
        f = fold(str(v)).strip()
        if f in ("moi ngay", "hang ngay", "hằng ngày", "all", "every day"):
            return ALL_DAYS
        if f in ("ngay thuong", "ngay lam viec", "thu 2 den thu 6", "weekdays"):
            mask |= 31
            continue
        m = re.fullmatch(r"(?:thu\s*|t)(\d)", f)
        if m and 2 <= int(m.group(1)) <= 7:
            mask |= day_bit(int(m.group(1)) - 2)
            continue
        if f in ("chu nhat", "cn", "sunday"):
            mask |= day_bit(6)
            continue
        for i, name in enumerate(_DAY_NAMES):
            if f == fold(name):
                mask |= day_bit(i)
    return mask or ALL_DAYS


def parse_time(text: str) -> tuple[int, int] | None:
    """'7h', '7h30', '07:30', '8 giờ', '19h15' → (giờ, phút). Không đọc được → None."""
    m = (re.search(r"(\d{1,2})\s*(?:h|g|giờ|gio|:)\s*(\d{1,2})?", str(text or ""), re.IGNORECASE)
         or re.search(r"\b(\d{1,2})\s+(\d{2})\b", str(text or "")))       # «07 30» sau khi bỏ dấu câu
    if not m:
        return None
    hour, minute = int(m.group(1)), int(m.group(2) or 0)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour, minute


# ---------------------------------------------------------------------------
# Đọc / ghi đăng ký — luôn theo `user_id` của người đang chat / đăng nhập
# ---------------------------------------------------------------------------
def _daily_row(db: Session, user_id: int) -> AgentBriefSub | None:
    return db.scalar(select(AgentBriefSub).where(AgentBriefSub.user_id == int(user_id), AgentBriefSub.kind == Kind.DAILY)
                     .order_by(AgentBriefSub.id).limit(1))


def _has_google(db: Session, user_id: int) -> bool:
    return db.scalar(select(AgentGoogleLink.id).where(AgentGoogleLink.user_id == int(user_id),
                                                     AgentGoogleLink.revoked_at.is_(None)).limit(1)) is not None


def daily_state(db: Session, user_id: int) -> dict:
    row = _daily_row(db, user_id)
    if row is None:
        on = _has_google(db, user_id)
        return {"id": 0, "kind": int(Kind.DAILY), "enabled": on, "hour": DEFAULT_HOUR, "minute": DEFAULT_MINUTE,
                "days": ALL_DAYS, "implicit": True}
    return {"id": row.id, "kind": int(Kind.DAILY), "enabled": bool(row.enabled), "hour": row.hour, "minute": row.minute,
            "days": row.days, "implicit": False}


def set_daily(db: Session, user_id: int, *, enabled: bool, hour: int | None = None, minute: int | None = None,
              days: int | None = None) -> dict:
    uid = int(user_id)
    if uid <= 0:
        raise ValueError("chat này chưa đăng nhập ERP")
    row = _daily_row(db, uid)
    if row is None:
        row = AgentBriefSub(user_id=uid, kind=Kind.DAILY, hour=DEFAULT_HOUR, minute=DEFAULT_MINUTE, days=ALL_DAYS,
                            created_by=uid, updated_by=uid)
        db.add(row)
    row.enabled = bool(enabled)
    if hour is not None:
        row.hour = int(hour)
    if minute is not None:
        row.minute = int(minute)
    if days is not None:
        row.days = int(days) & ALL_DAYS or ALL_DAYS
    row.updated_by = uid
    db.commit()
    return daily_state(db, uid)


def topics(db: Session, user_id: int) -> list[AgentBriefSub]:
    return list(db.scalars(select(AgentBriefSub).where(AgentBriefSub.user_id == int(user_id),
                                                       AgentBriefSub.kind == Kind.TOPIC).order_by(AgentBriefSub.id)))


def add_topic(db: Session, user_id: int, question: str, *, hour: int = DEFAULT_HOUR, minute: int = DEFAULT_MINUTE,
              days: int = ALL_DAYS, sub_code: str = "") -> AgentBriefSub:
    from . import personal_memory

    uid = int(user_id)
    q = " ".join(str(question or "").split())[:TOPIC_MAX]
    if uid <= 0:
        raise ValueError("chat này chưa đăng nhập ERP")
    if not q:
        raise ValueError("chưa có nội dung bản tin")
    if personal_memory.is_secret(q):
        raise ValueError("bản tin không được chứa mật khẩu, khóa, số thẻ hay số tài khoản")
    if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
        raise ValueError("giờ không hợp lệ")
    if len(topics(db, uid)) >= MAX_TOPICS:
        raise ValueError(f"đã có {MAX_TOPICS} bản tin chủ đề — tắt bớt rồi thêm")
    row = AgentBriefSub(user_id=uid, kind=Kind.TOPIC, enabled=True, hour=int(hour), minute=int(minute),
                        days=int(days) & ALL_DAYS or ALL_DAYS, topic=q, sub_code=str(sub_code or "")[:40],
                        created_by=uid, updated_by=uid)
    db.add(row)
    db.commit()
    return row


def set_enabled(db: Session, user_id: int, sub_id: int, enabled: bool) -> bool:
    row = db.get(AgentBriefSub, int(sub_id))
    if row is None or int(row.user_id) != int(user_id):
        return False
    row.enabled = bool(enabled)
    db.commit()
    return True


def remove(db: Session, user_id: int, sub_id: int) -> bool:
    row = db.get(AgentBriefSub, int(sub_id))
    if row is None or int(row.user_id) != int(user_id):
        return False
    if row.kind == Kind.DAILY:
        row.enabled = False                 # bản tin sáng: «xóa» = tắt (để không bật lại ngầm theo Google)
    else:
        db.delete(row)
    db.commit()
    return True


def disable_all(db: Session, user_id: int) -> int:
    n = 0
    for row in topics(db, user_id):
        if row.enabled:
            row.enabled = False
            n += 1
    d = daily_state(db, user_id)
    db.commit()
    if d["enabled"]:
        set_daily(db, user_id, enabled=False)
        n += 1
    return n


def serialize(row_or_state) -> dict:
    if isinstance(row_or_state, dict):
        d = dict(row_or_state)
        d.update(topic="", sub_code="", label=KIND_LABELS[Kind.DAILY])
    else:
        r = row_or_state
        d = {"id": r.id, "kind": int(r.kind), "enabled": bool(r.enabled), "hour": r.hour, "minute": r.minute,
             "days": r.days, "topic": r.topic, "sub_code": r.sub_code, "implicit": False,
             "label": KIND_LABELS.get(Kind(r.kind), "")}
    d["when"] = f"{d['hour']:02d}:{d['minute']:02d} · {days_text(d['days'])}"
    return d


def list_for(db: Session, user_id: int) -> list[dict]:
    return [serialize(daily_state(db, user_id))] + [serialize(r) for r in topics(db, user_id)]


def render_list(db: Session, user_id: int) -> str:
    from .telegram import esc

    items = list_for(db, user_id)
    lines = ["<b>BẢN TIN CỦA ANH/CHỊ</b>"]
    for i, it in enumerate(items, 1):
        state = "đang bật" if it["enabled"] else "đang tắt"
        what = it["label"] if it["kind"] == Kind.DAILY else f"«{esc(it['topic'])}»"
        lines.append(f"{i}. {what} · {it['when']} · {state}")
    from . import work_due

    lines.append("")
    lines.append(work_due.state_text(db, user_id).split(" — ")[0])     # ai-CR-175: một dòng trạng thái
    lines.append("")
    lines.append("<i>Nhắn: bật bản tin · tắt bản tin · bản tin lúc 6h45 · bản tin hôm nay · tắt bản tin 2 · "
                 "hoặc nói tự nhiên «sáng thứ hai gửi anh công nợ quá hạn».</i>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Gửi
# ---------------------------------------------------------------------------
def daily_text(db: Session, user) -> str:
    """Bản tin sáng của MỘT người: lịch Google (nếu nối) + việc riêng + việc Dự án + chờ duyệt."""
    from . import briefs, google_link

    events = None
    note = ""
    link = db.scalar(select(AgentGoogleLink).where(AgentGoogleLink.user_id == int(user.id),
                                                   AgentGoogleLink.revoked_at.is_(None)).limit(1))
    if link is not None:
        from app.modules.assistant.tools.google_tool import list_events

        try:
            events = list_events(db, link)
        except google_link.GoogleError as e:
            events, note = [], str(e)
    from .telegram import esc

    text = briefs.morning_text(db, user, events)
    return text + (f"\n(Không đọc được lịch Google: {esc(note[:120])})" if note else "")


def _due(row_or_state: dict, local: datetime) -> bool:
    if not row_or_state["enabled"] or not (int(row_or_state["days"]) & day_bit(local.weekday())):
        return False
    at = local.replace(hour=int(row_or_state["hour"]), minute=int(row_or_state["minute"]), second=0, microsecond=0)
    return at <= local < at + SEND_WINDOW


def _bell_on(db: Session, user_id: int) -> bool:
    """Bản tin NGẦM (người nối Google chưa tự bật) giữ luật cũ của ai-CR-064: chuông của chat không tắt mới gửi."""
    from .constants import NOTIFY_OFF
    from .model import AgentChatLink

    return any(int(c.notify_mode or 0) != NOTIFY_OFF for c in db.scalars(select(AgentChatLink).where(
        AgentChatLink.user_id == int(user_id), AgentChatLink.chat_id != "", AgentChatLink.revoked_at.is_(None))))


def _candidates(db: Session) -> list[tuple[int, object]]:
    """(user_id, dòng hoặc trạng thái ngầm). Ngầm = người đã nối Google mà chưa có dòng bản tin sáng."""
    out: list[tuple[int, object]] = [(r.user_id, r) for r in db.scalars(select(AgentBriefSub).where(
        AgentBriefSub.enabled.is_(True), AgentBriefSub.kind.in_([int(Kind.DAILY), int(Kind.TOPIC)])))]
    with_daily = {int(r.user_id) for r in db.scalars(select(AgentBriefSub).where(AgentBriefSub.kind == Kind.DAILY))}
    for g in db.scalars(select(AgentGoogleLink).where(AgentGoogleLink.revoked_at.is_(None))):
        if int(g.user_id) not in with_daily:
            out.append((int(g.user_id), None))
    return out


def send_one(db: Session, user_id: int, row: AgentBriefSub | None, chat_id: str = "") -> bool:
    """Gửi một bản tin ngay (vòng nền hoặc lệnh «bản tin hôm nay»). Trả True nếu đã gửi."""
    from . import erp, groups, service, user_keys
    from .constants import ACT_BRIEF

    user = erp.user_by_id(db, int(user_id))
    if user is None or not getattr(user, "is_active", True):
        return False
    chat = chat_id or groups.private_chat_of(db, int(user_id))
    if not chat:
        return False
    if row is None or row.kind == Kind.DAILY:
        service.reply(db, chat, daily_text(db, user), action=ACT_BRIEF)
        db.commit()
        return True
    from .telegram import esc

    service.reply(db, chat, f"<b>Bản tin:</b> {esc(row.topic)}", action=ACT_BRIEF)
    db.commit()
    with user_keys.for_chat(db, chat):
        if not user_keys.active_key():
            service.reply(db, chat, user_keys.NO_KEY_HELP, action=ACT_BRIEF)
            db.commit()
            return True
        service.answer_question(db, chat, row.topic, intent="hoi", ledger=False)
    return True


def tick(db: Session, *, now: datetime | None = None) -> dict:
    now = now or now_utc()
    local = now + LOCAL_OFFSET
    today = local.date().isoformat()
    sent = failed = 0
    for uid, row in _candidates(db):
        if row is None:
            state = {"enabled": True, "days": ALL_DAYS, "hour": DEFAULT_HOUR, "minute": DEFAULT_MINUTE}
            if not _due(state, local) or not _bell_on(db, uid):
                continue
            #  Ngầm (người đã nối Google): ghi hẳn một dòng để đánh dấu đã gửi hôm nay.
            row = AgentBriefSub(user_id=uid, kind=Kind.DAILY, enabled=True, hour=DEFAULT_HOUR, minute=DEFAULT_MINUTE,
                                days=ALL_DAYS, created_by=0, updated_by=0)
            db.add(row)
        elif not _due({"enabled": row.enabled, "days": row.days, "hour": row.hour, "minute": row.minute}, local) \
                or row.last_sent_on == today:
            continue
        row.last_sent_on = today            # đánh dấu TRƯỚC: gửi hỏng cũng không lặp lại cả ngày
        db.commit()
        try:
            if send_one(db, uid, row):
                sent += 1
        except Exception:  # noqa: BLE001 — một bản tin hỏng không được chặn người khác
            db.rollback()
            failed += 1
            log.exception("agent_hub: gửi bản tin %s của user %s hỏng", row.id, uid)
    return {"sent": sent, "failed": failed}
