"""NHẮC VIỆC bằng câu nói (ai-CR-060, T-10 của `doc/agent-hub/04`).

«nhắc anh 3h gọi nhà cung cấp X» · «nhắc tôi mai 9h họp» · «30 phút nữa nhắc em nộp báo cáo»: bot đọc giờ
bằng `parse_schedule_time` (cùng bộ đọc giờ của hẹn gộp + deploy, ai-CR-014), ghi một dòng `tab_agent_reminder`
và vòng beat mỗi phút gửi lại đúng chat đó khi tới giờ. Không đọc được giờ thì hỏi lại, không đoán.
Ai đã đăng nhập bot đều dùng được, không cần khóa Gemini (không có lượt model nào).
"""
from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import AgentReminder
from .timeutil import fmt_local, now_local, now_utc, to_utc

MAX_OPEN = 50          # mỗi chat tối đa chừng này lời nhắc đang chờ
_LEAD = re.compile(r"^(nhắc|nhắc nhở|nhắc giúp|nhớ nhắc)\s+(anh|tôi|em|mình|chị|giúp anh|giúp em|cho anh|cho em|cho tôi)?\s*", re.I)
_LEAD_MID = re.compile(r"^(?P<pre>.{1,40}?)\s+(nhắc|nhắc nhở)\s+(anh|tôi|em|mình|chị|giúp anh|giúp em)?\s*(?P<body>.+)$", re.I)
_LIST = re.compile(r"^(nhắc gì|xem nhắc|danh sách nhắc|các lời nhắc|nhắc việc gì|lịch nhắc)[?.! ]*$", re.I)
_CANCEL = re.compile(r"^(bỏ|xóa|hủy)\s+(lời )?nhắc\s+(số\s+)?(?P<n>\d+)[.! ]*$", re.I)
_CANCEL_ALL = re.compile(r"^(bỏ|xóa|hủy)\s+(hết|tất cả)\s+(lời )?nhắc[.! ]*$", re.I)
#  Cụm giờ để bóc khỏi nội dung: «3h», «14:30», «20h30», «8 giờ sáng mai», «45 phút nữa», «sau 2 tiếng», «mai», «tối».
_TIME_BITS = re.compile(
    r"((lúc|vào|vào lúc)\s+)?(\d{1,2}\s*(?::|h|g|giờ|gio)\s*\d{0,2}(\s*(sáng|trưa|chiều|tối))?(\s+mai)?"
    r"|\d{1,3}\s*(phút|phut|tiếng|tieng|giờ|gio)\s+(nữa|nua)|sau\s+\d{1,3}\s*(phút|phut|tiếng|tieng|giờ|gio)"
    r"|(ngày\s+)?mai|sáng mai|chiều mai|tối nay|chiều nay|trưa nay)", re.I)


def parse(text: str, *, now: datetime | None = None) -> dict | None:
    """Câu nhắc → {"when": datetime local | None, "what": str}; không phải câu nhắc → None."""
    raw = text.strip()
    if _LIST.match(raw) or _CANCEL.match(raw) or _CANCEL_ALL.match(raw):
        return None
    m = _LEAD.match(raw)
    if m:
        body = raw[m.end():].strip()
    else:
        #  Cụm giờ đứng trước: «30 phút nữa nhắc em nộp báo cáo», «mai 9h nhắc anh họp».
        mm = _LEAD_MID.match(raw)
        if not mm or _TIME_BITS.sub("", mm.group("pre")).strip(" ,.:;-"):
            return None
        body = (mm.group("pre").strip() + " " + mm.group("body").strip()).strip()
    if not body:
        return {"when": None, "what": ""}
    from .service import parse_schedule_time   # cùng bộ đọc giờ với hẹn gộp/deploy

    when = parse_schedule_time(body, now or now_local())
    what = _TIME_BITS.sub(" ", body)
    what = re.sub(r"\s{2,}", " ", what).strip(" ,.:;-")
    return {"when": when, "what": what or body}


def parse_command(text: str) -> dict | None:
    raw = text.strip()
    if _LIST.match(raw):
        return {"op": "list"}
    if _CANCEL_ALL.match(raw):
        return {"op": "cancel_all"}
    if m := _CANCEL.match(raw):
        return {"op": "cancel", "n": int(m.group("n"))}
    return None


def open_for_chat(db: Session, chat_id: str) -> list[AgentReminder]:
    return list(db.scalars(select(AgentReminder).where(
        AgentReminder.chat_id == chat_id, AgentReminder.sent_at.is_(None), AgentReminder.cancelled_at.is_(None))
        .order_by(AgentReminder.due_at)))


def create(db: Session, chat_id: str, user_id: int, what: str, when_local: datetime) -> AgentReminder:
    row = AgentReminder(chat_id=chat_id, user_id=int(user_id or 0), text=what[:500], due_at=to_utc(when_local),
                        created_by=int(user_id or 0), updated_by=int(user_id or 0))
    db.add(row)
    db.commit()
    return row


def cancel(db: Session, row: AgentReminder) -> None:
    row.cancelled_at = datetime.now()
    db.commit()


def listing(db: Session, chat_id: str) -> str:
    from . import telegram

    rows = open_for_chat(db, chat_id)
    if not rows:
        return "Chưa có lời nhắc nào đang chờ. Nhắn ví dụ «nhắc anh 15h gọi nhà cung cấp X»."
    lines = ["<b>Lời nhắc đang chờ:</b>"]
    for i, r in enumerate(rows, 1):
        lines.append(f"{i}. {fmt_local(r.due_at)} — {telegram.esc(r.text)}")
    lines.append("Bỏ một lời: «bỏ nhắc 2»; bỏ hết: «bỏ hết nhắc».")
    return "\n".join(lines)


def fire_due(db: Session, *, now: datetime | None = None) -> int:
    """Vòng beat: gửi các lời nhắc tới giờ. Trả số đã gửi."""
    from . import telegram
    from .constants import ACT_REMINDER, DIR_OUT
    from .model import AgentMessage

    now = now or now_utc()
    rows = list(db.scalars(select(AgentReminder).where(
        AgentReminder.due_at <= now, AgentReminder.sent_at.is_(None), AgentReminder.cancelled_at.is_(None))
        .order_by(AgentReminder.due_at).limit(100)))
    n = 0
    for r in rows:
        text = f"<b>Nhắc:</b> {telegram.esc(r.text)}"
        try:
            mid = telegram.send(text, chat_id=r.chat_id)
        except telegram.TelegramError as e:
            mid, text = 0, f"[KHÔNG GỬI ĐƯỢC: {e}] {text}"
        r.sent_at = datetime.now()
        db.add(AgentMessage(task_id=0, direction=DIR_OUT, chat_id=r.chat_id, tg_message_id=mid, body=text,
                            action=ACT_REMINDER))
        n += 1
    if rows:
        db.commit()
    return n
