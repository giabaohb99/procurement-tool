"""Khóa Gemini CÁ NHÂN (ai-CR-053, D-01 + D-02 của `doc/agent-hub/04`).

Đại ca chốt 24/09/2026: bot trên dev là trợ lý của TỪNG NGƯỜI, mỗi người dán khóa Gemini của mình ở
Trang cá nhân → «Khóa AI» (web, KHÔNG qua chat: Telegram giữ lịch sử vĩnh viễn). Mọi lượt Gemini
trong chat của người đó (đọc ý định, Trợ lý ERP, nghiên cứu) đi bằng khóa của họ; không lùi về khóa
công ty. Chưa gắn khóa thì bot không trả lời câu hỏi AI, các việc không cần Gemini (đăng nhập, xem
tình trạng việc, ra lệnh trên việc) vẫn dùng được.

Ba loại khóa, không chung nhau:
  - khóa cá nhân (bảng `tab_agent_user_key`, mã hóa Fernet như cấu hình hệ thống);
  - khóa công ty của Trợ lý web (`tab_setting.gemini_api_key`) — bot KHÔNG đọc;
  - `AGENT_GEMINI_API_KEY` trong `.env` — chỉ còn là đường lùi cho CHAT ĐẠI CA khi máy chạy bot là máy
    đại ca (phase 0/1). Trên dev biến này để trống, đại ca cũng dùng khóa cá nhân.

Khóa đang dùng cho lượt gọi hiện tại nằm trong một ContextVar: `service` mở ngữ cảnh
(`for_chat` / `for_admin`) quanh mỗi tin nhắn hoặc mỗi việc nền, provider của bot đọc từ đó.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.config import settings

from . import chat_link, telegram
from .model import AgentUserKey

PROVIDER_GEMINI = "gemini"
PROBE_URL = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1"
PROBE_TIMEOUT = 15

NO_KEY_HELP = ("Chat này chưa gắn khóa Gemini nên em chưa trả lời câu hỏi AI được. Vào ERP → <b>Trang cá nhân → "
               "Khóa AI</b>, dán khóa của anh/chị rồi hỏi lại. Đăng nhập, xem tình trạng việc, ra lệnh trên việc "
               "vẫn dùng được, không cần khóa.")

#  (đã mở ngữ cảnh?, khóa, chủ khóa). Ngoài mọi ngữ cảnh (bài kiểm, script) thì provider lùi về
#  `AGENT_GEMINI_API_KEY` như trước — không đổi hành vi cũ ở chỗ chưa nối.
_ctx_open: ContextVar[bool] = ContextVar("agent_key_ctx", default=False)
_ctx_key: ContextVar[str] = ContextVar("agent_key", default="")
_ctx_owner: ContextVar[int] = ContextVar("agent_key_owner", default=0)


class InvalidKey(ValueError):
    """Khóa không được Gemini chấp nhận (sai, bị thu hồi, hoặc dự án chưa bật API)."""


def active_key() -> str:
    """Khóa cho lượt gọi hiện tại. Ngoài ngữ cảnh: khóa `.env` (hành vi cũ)."""
    return _ctx_key.get() if _ctx_open.get() else settings.AGENT_GEMINI_API_KEY


def active_owner() -> int:
    return _ctx_owner.get()


def in_context() -> bool:
    return _ctx_open.get()


@contextmanager
def use(key: str, owner: int = 0):
    tokens = (_ctx_open.set(True), _ctx_key.set(key or ""), _ctx_owner.set(int(owner or 0)))
    try:
        yield key
    finally:
        _ctx_owner.reset(tokens[2])
        _ctx_key.reset(tokens[1])
        _ctx_open.reset(tokens[0])


def key_for_user(db: Session, user_id: int) -> str:
    row = active_row(db, user_id)
    return app_settings._decrypt(row.key_enc) if row is not None else ""


def key_for_chat(db: Session, chat_id: str) -> tuple[str, int]:
    """(khóa, chủ khóa) cho một chat. Chat đã liên kết → khóa của tài khoản đó; chat đại ca chưa có khóa
    cá nhân → đường lùi `.env`; chat khác không bao giờ được lùi."""
    link = chat_link.get_active_link(db, chat_id) if chat_id else None
    if link is not None:
        key = key_for_user(db, link.user_id)
        if key:
            return key, link.user_id
        if telegram.is_allowed_chat(chat_id):
            return settings.AGENT_GEMINI_API_KEY, link.user_id
        return "", link.user_id
    if telegram.is_allowed_chat(chat_id):
        return settings.AGENT_GEMINI_API_KEY, 0
    return "", 0


@contextmanager
def for_chat(db: Session, chat_id: str):
    key, owner = key_for_chat(db, chat_id)
    with use(key, owner):
        yield key


@contextmanager
def for_admin(db: Session):
    """Việc nền của mảng mã nguồn (gom việc, lập kế hoạch) chạy bằng khóa của đại ca."""
    with for_chat(db, settings.AGENT_TELEGRAM_CHAT_ID) as key:
        yield key


# ---------------------------------------------------------------------------
# Sổ khóa
# ---------------------------------------------------------------------------
def active_row(db: Session, user_id: int) -> AgentUserKey | None:
    return db.scalar(select(AgentUserKey).where(
        AgentUserKey.user_id == user_id, AgentUserKey.provider == PROVIDER_GEMINI,
        AgentUserKey.revoked_at.is_(None)).order_by(AgentUserKey.id.desc()).limit(1))


def _probe(raw: str) -> int:
    """Một lượt GET không tốn token để biết khóa có được nhận không. Trả mã HTTP."""
    try:
        return requests.get(PROBE_URL, headers={"x-goog-api-key": raw}, timeout=PROBE_TIMEOUT).status_code
    except requests.RequestException as e:
        raise InvalidKey(f"Không gọi được Gemini để kiểm khóa: {e}") from e


def verify(raw: str) -> None:
    raw = (raw or "").strip()
    if len(raw) < 20 or " " in raw:
        raise InvalidKey("Khóa không đúng dạng.")
    code = _probe(raw)
    if code in (400, 401, 403):
        raise InvalidKey("Gemini không nhận khóa này (sai, đã thu hồi, hoặc dự án chưa bật Generative Language API).")
    if code != 200:
        raise InvalidKey(f"Gemini trả lỗi {code} khi kiểm khóa, thử lại sau.")


def set_key(db: Session, user_id: int, raw: str) -> AgentUserKey:
    """Kiểm khóa với Gemini rồi lưu mã hóa; dòng cũ đóng lại. Không bao giờ ghi khóa thô vào log/sổ."""
    raw = (raw or "").strip()
    verify(raw)
    now = datetime.now()
    for old in db.scalars(select(AgentUserKey).where(AgentUserKey.user_id == user_id,
                                                     AgentUserKey.provider == PROVIDER_GEMINI,
                                                     AgentUserKey.revoked_at.is_(None))):
        old.revoked_at = now
    row = AgentUserKey(user_id=user_id, provider=PROVIDER_GEMINI, key_enc=app_settings.encrypt(raw),
                       key_hint=raw[-4:], verified_at=now, created_by=user_id, updated_by=user_id)
    db.add(row)
    db.commit()
    return row


def revoke(db: Session, user_id: int) -> int:
    now = datetime.now()
    n = 0
    for old in db.scalars(select(AgentUserKey).where(AgentUserKey.user_id == user_id, AgentUserKey.revoked_at.is_(None))):
        old.revoked_at = now
        n += 1
    if n:
        db.commit()
    return n


def describe(db: Session, user_id: int) -> dict:
    row = active_row(db, user_id)
    return {"provider": PROVIDER_GEMINI, "has_key": row is not None, "hint": f"…{row.key_hint}" if row else "",
            "verified_at": row.verified_at.isoformat(timespec="seconds") if row and row.verified_at else None}
