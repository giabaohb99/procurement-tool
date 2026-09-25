"""Mỗi người tự đăng nhập tài khoản ERP ngay trong Telegram (ai-CR-038).

Đường đi: trang cá nhân ERP → «Lấy mã liên kết» (mã 6 số, sống `AGENT_LINK_CODE_MINUTES` phút,
chỉ lưu dạng băm) → nhắn `/dangnhap <mã>` cho bot trong chat RIÊNG → chat đó gắn với tài khoản,
sống `AGENT_LINK_DAYS` ngày → hết hạn, `/dangxuat`, hoặc gỡ ở trang cá nhân.

Không bao giờ hỏi mật khẩu trong khung chat: Telegram giữ lịch sử vĩnh viễn, và một mật khẩu nằm
trong lịch sử chat là mật khẩu đã lộ. Mã một lần hết hạn sau vài phút thì lộ cũng vô hại.

Người đã liên kết CHỈ hỏi được Trợ lý AI, chạy dưới đúng phạm vi dữ liệu của chính họ. Nhận việc
sửa mã, gộp, deploy… vẫn chỉ chat của đại ca (`AGENT_TELEGRAM_CHAT_ID`) làm được.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings

from .model import AgentChatLink, AgentMessage

#  Sai quá bấy nhiêu lần trong một giờ thì chat đó bị lờ đi (chống dò mã 6 số).
MAX_FAILURES_PER_HOUR = 5
ACT_LOGIN_FAIL = "dn_sai"


def hash_code(code: str) -> str:
    return hashlib.sha256(f"agent-link:{code}".encode()).hexdigest()


def issue_code(db: Session, user_id: int, *, now: datetime | None = None) -> tuple[str, datetime]:
    """Phát mã mới cho `user_id`; mã cũ chưa dùng của người đó bị hủy. Trả (mã, hạn)."""
    now = now or datetime.now()
    for old in db.scalars(select(AgentChatLink).where(
            AgentChatLink.user_id == user_id, AgentChatLink.chat_id == "", AgentChatLink.revoked_at.is_(None))):
        old.revoked_at = now
        old.code_hash = ""
    expires = now + timedelta(minutes=settings.AGENT_LINK_CODE_MINUTES)
    for _attempt in range(10):
        code = f"{secrets.randbelow(1_000_000):06d}"
        if find_pending(db, code, now) is None:      # không trùng mã đang chờ của người khác
            break
    db.add(AgentChatLink(user_id=user_id, code_hash=hash_code(code), code_expires_at=expires,
                         created_by=user_id, updated_by=user_id))
    db.commit()
    return code, expires


def find_pending(db: Session, code: str, now: datetime) -> AgentChatLink | None:
    return db.scalar(select(AgentChatLink).where(
        AgentChatLink.code_hash == hash_code(code), AgentChatLink.chat_id == "",
        AgentChatLink.revoked_at.is_(None), AgentChatLink.code_expires_at > now))


def redeem_code(db: Session, chat_id: str, code: str, tg_name: str = "", *,
                now: datetime | None = None) -> AgentChatLink | None:
    """Đổi mã lấy liên kết cho `chat_id`. Sai / hết hạn thì None. Liên kết cũ của chat bị gỡ."""
    now = now or datetime.now()
    link = find_pending(db, code, now)
    if link is None:
        return None
    for old in db.scalars(select(AgentChatLink).where(
            AgentChatLink.chat_id == chat_id, AgentChatLink.revoked_at.is_(None))):
        old.revoked_at = now
    link.chat_id = chat_id
    link.tg_name = (tg_name or "")[:255]
    link.code_hash = ""
    link.linked_at = now
    link.expires_at = now + timedelta(days=settings.AGENT_LINK_DAYS)
    db.commit()
    return link


def get_active_link(db: Session, chat_id: str, *, now: datetime | None = None) -> AgentChatLink | None:
    now = now or datetime.now()
    return db.scalar(select(AgentChatLink).where(
        AgentChatLink.chat_id == chat_id, AgentChatLink.revoked_at.is_(None),
        AgentChatLink.expires_at > now).order_by(AgentChatLink.id.desc()).limit(1))


def get_expired_link(db: Session, chat_id: str, *, now: datetime | None = None) -> AgentChatLink | None:
    """Liên kết đã HẾT HẠN mà chưa ai gỡ — để báo người dùng lấy mã mới (đúng một lần)."""
    now = now or datetime.now()
    return db.scalar(select(AgentChatLink).where(
        AgentChatLink.chat_id == chat_id, AgentChatLink.revoked_at.is_(None),
        AgentChatLink.expires_at <= now).order_by(AgentChatLink.id.desc()).limit(1))


def revoke_chat(db: Session, chat_id: str, *, now: datetime | None = None) -> int:
    now = now or datetime.now()
    n = 0
    for link in db.scalars(select(AgentChatLink).where(
            AgentChatLink.chat_id == chat_id, AgentChatLink.revoked_at.is_(None))):
        link.revoked_at = now
        n += 1
    db.commit()
    return n


def list_user_links(db: Session, user_id: int, *, now: datetime | None = None) -> list[AgentChatLink]:
    """Liên kết còn hiệu lực của một người — cho trang cá nhân."""
    now = now or datetime.now()
    return list(db.scalars(select(AgentChatLink).where(
        AgentChatLink.user_id == user_id, AgentChatLink.chat_id != "", AgentChatLink.revoked_at.is_(None),
        AgentChatLink.expires_at > now).order_by(AgentChatLink.id.desc())))


def has_too_many_failures(db: Session, chat_id: str, *, now: datetime | None = None) -> bool:
    now = now or datetime.now()
    n = db.scalar(select(func.count(AgentMessage.id)).where(
        AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_LOGIN_FAIL,
        AgentMessage.created_at >= now - timedelta(hours=1))) or 0
    return n >= MAX_FAILURES_PER_HOUR


def mask_chat(chat_id: str) -> str:
    """`…4321` — trang cá nhân không cần cả số chat."""
    return f"…{chat_id[-4:]}" if len(chat_id) > 4 else chat_id
