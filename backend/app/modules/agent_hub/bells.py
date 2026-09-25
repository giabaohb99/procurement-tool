"""CHUÔNG ERP sang Telegram của từng người đã đăng nhập (ai-CR-059, P-01 của `doc/agent-hub/04`).

Mọi thông báo trong app (`tab_notification`: phiếu chờ duyệt, việc được giao, phiếu bị trả, phiếu hỗ trợ…)
đều là một dòng chuông. Thay vì móc vào từng nơi tạo chuông (workflow, duyệt, nghỉ phép, ticket…), một vòng
beat mỗi phút đọc các dòng mới hơn con trỏ `bell_offset` và gửi cho chat Telegram đã liên kết của người
nhận. Nhờ vậy nguồn chuông nào cũng đi, kể cả nguồn thêm sau này.

Mỗi liên kết chọn một mức (`AgentChatLink.notify_mode`), đổi ở Trang cá nhân → Telegram hoặc nhắn bot:
  0 tắt · 1 «việc của tôi» (mặc định — chờ tôi duyệt, giao cho tôi, trả lại cho tôi) · 2 tất cả.
Đại ca chốt mặc định 25/09/2026: chỉ «chờ bạn duyệt / việc giao cho bạn», không đẩy toàn bộ chuông.
"""
from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.notification.model import Notification

from . import telegram
from .constants import ACT_BELL, DIR_OUT, NOTIFY_ALL, NOTIFY_MINE, NOTIFY_OFF
from .model import AgentChatLink, AgentCursor, AgentMessage

CURSOR_NAME = "bell_offset"
BATCH = 300                 # dòng chuông tối đa một lượt
PER_CHAT = 5                # tin tối đa một chat một lượt; dư thì gộp thành một dòng đếm
#  Chuông «của tôi»: chờ tôi duyệt / xử lý, được phân công, giao cho tôi, bị trả lại cho tôi, nhắc tôi.
_MINE = re.compile(
    r"(chờ|cần|đến lượt|mời)\s+(bạn|anh/chị|anh|chị)\s+(duyệt|xử lý|xác nhận|ký)"
    r"|bạn được (phân công|giao|chọn|ủy quyền)|giao cho bạn|phân công .{0,30}cho bạn|bàn giao cho bạn"
    r"|của bạn (đã )?bị (trả|từ chối)|nhắc (bạn|việc)|quá hạn", re.I)


def is_mine(title: str, body: str) -> bool:
    return bool(_MINE.search(f"{title or ''} {body or ''}"))


def _cursor(db: Session) -> AgentCursor:
    row = db.scalar(select(AgentCursor).where(AgentCursor.name == CURSOR_NAME))
    if row is None:
        #  Lần đầu: đứng ở dòng mới nhất, không đổ cả lịch sử chuông cũ vào Telegram.
        last = int(db.scalar(select(func.max(Notification.id))) or 0)
        row = AgentCursor(name=CURSOR_NAME, value=last, created_by=0, updated_by=0)
        db.add(row)
        db.commit()
    return row


def _active_links_by_user(db: Session, user_ids: set[int], now: datetime) -> dict[int, list[AgentChatLink]]:
    out: dict[int, list[AgentChatLink]] = {}
    if not user_ids:
        return out
    for link in db.scalars(select(AgentChatLink).where(
            AgentChatLink.user_id.in_(list(user_ids)), AgentChatLink.chat_id != "",
            AgentChatLink.revoked_at.is_(None), AgentChatLink.expires_at > now)):
        if int(link.notify_mode or NOTIFY_OFF) != NOTIFY_OFF:
            out.setdefault(link.user_id, []).append(link)
    return out


def format_bell(n: Notification) -> str:
    esc = telegram.esc
    text = f"<b>{esc(n.title or '')}</b>"
    if n.body:
        text += f"\n{esc((n.body or '')[:600])}"
    if n.link:
        text += f'\n<a href="{esc(telegram.absolute_url(n.link))}">Mở trên ERP</a>'
    return text


def forward_bells(db: Session, *, now: datetime | None = None) -> int:
    """Một lượt: đọc chuông mới hơn con trỏ, gửi cho chat đã liên kết theo mức từng chat. Trả số tin đã gửi."""
    now = now or datetime.now()
    cur = _cursor(db)
    rows = list(db.scalars(select(Notification).where(Notification.id > cur.value)
                           .order_by(Notification.id).limit(BATCH)))
    if not rows:
        return 0
    links = _active_links_by_user(db, {int(r.user_id or 0) for r in rows if r.user_id}, now)
    per_chat: dict[str, list[Notification]] = {}
    for n in rows:
        for link in links.get(int(n.user_id or 0), []):
            mode = int(link.notify_mode or NOTIFY_OFF)
            if mode == NOTIFY_ALL or (mode == NOTIFY_MINE and is_mine(n.title, n.body)):
                per_chat.setdefault(link.chat_id, []).append(n)
    sent = 0
    for chat_id, items in per_chat.items():
        for n in items[:PER_CHAT]:
            _send(db, chat_id, format_bell(n), n.id)
            sent += 1
        if len(items) > PER_CHAT:
            _send(db, chat_id, f"… và {len(items) - PER_CHAT} thông báo khác, xem ở chuông trên ERP.", 0)
            sent += 1
    cur.value = rows[-1].id
    db.commit()
    return sent


def _send(db: Session, chat_id: str, text: str, bell_id: int) -> None:
    try:
        mid = telegram.send(text, chat_id=chat_id)
    except telegram.TelegramError as e:
        mid, text = 0, f"[KHÔNG GỬI ĐƯỢC: {e}] {text}"
    db.add(AgentMessage(task_id=0, direction=DIR_OUT, chat_id=chat_id, tg_message_id=mid,
                        body=f"[chuông #{bell_id}] {text}" if bell_id else text, action=ACT_BELL))


# ---------------------------------------------------------------------------
# Câu nhắn đổi mức: «tắt chuông» · «bật chuông» · «chuông tất cả» · «chuông việc của tôi»
# ---------------------------------------------------------------------------
_OFF = re.compile(r"^(tắt|ngưng|dừng|thôi)\s+(chuông|thông báo)(\s+erp)?[.! ]*$")
_ALL = re.compile(r"^(chuông|thông báo)\s+(tất cả|hết|toàn bộ)[.! ]*$|^(bật|nhận)\s+(tất cả|hết|toàn bộ)\s+(chuông|thông báo)[.! ]*$")
_MINE_CMD = re.compile(r"^(bật|mở)\s+(chuông|thông báo)(\s+erp)?[.! ]*$|^(chuông|thông báo)\s+(việc )?của (tôi|anh|em|mình)[.! ]*$")


def parse_mode(text: str) -> int | None:
    low = text.strip().lower()
    if _OFF.match(low):
        return NOTIFY_OFF
    if _ALL.match(low):
        return NOTIFY_ALL
    if _MINE_CMD.match(low):
        return NOTIFY_MINE
    return None
