"""KHÓA KẾT NỐI MCP cá nhân (ai-CR-063, M-02 của `doc/agent-hub/04`).

Mỗi người tự tạo khóa ở Trang cá nhân → «Khóa AI» → «Kết nối MCP», dán vào ứng dụng AI của mình (Claude
Desktop, Cursor, ChatGPT…) để ứng dụng đó gọi bộ tool ERP DƯỚI ĐÚNG QUYỀN của người đó. Khóa:
  - chỉ giữ băm SHA-256, hiện đúng một lần lúc tạo;
  - có hạn (mặc định 90 ngày), gỡ được, mỗi lượt gọi ghi `last_used_at`;
  - hai mức: CHỈ ĐỌC (tra cứu) · ĐƯỢC GHI (thêm soạn nháp + tạo/gửi duyệt hai bước + báo lỗi).
Nghỉ việc thì đóng cùng lúc phiên (employee.service._revoke_bot_access).
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .model import AgentMcpKey

SCOPE_READ = 0
SCOPE_WRITE = 1
SCOPE_LABELS = {SCOPE_READ: "chỉ đọc", SCOPE_WRITE: "được ghi"}
DEFAULT_DAYS = 90
MAX_DAYS = 365
MAX_KEYS = 5
PREFIX = "dego_mcp_"


def hash_token(raw: str) -> str:
    return hashlib.sha256(f"agent-mcp:{raw}".encode()).hexdigest()


def list_for_user(db: Session, user_id: int) -> list[AgentMcpKey]:
    return list(db.scalars(select(AgentMcpKey).where(AgentMcpKey.user_id == user_id, AgentMcpKey.revoked_at.is_(None))
                           .order_by(AgentMcpKey.id.desc())))


def create(db: Session, user_id: int, *, name: str = "", scope: int = SCOPE_READ, days: int = DEFAULT_DAYS) -> tuple[AgentMcpKey, str]:
    """Tạo khóa, trả (dòng, KHÓA THÔ — chỉ hiện một lần)."""
    if len(list_for_user(db, user_id)) >= MAX_KEYS:
        raise ValueError(f"Mỗi tài khoản tối đa {MAX_KEYS} khóa MCP đang hiệu lực; gỡ bớt rồi tạo.")
    days = max(1, min(int(days or DEFAULT_DAYS), MAX_DAYS))
    raw = PREFIX + secrets.token_urlsafe(30)
    row = AgentMcpKey(user_id=user_id, name=(name or "").strip()[:80] or "MCP", token_hash=hash_token(raw),
                      key_hint=raw[-4:], scope=SCOPE_WRITE if int(scope) == SCOPE_WRITE else SCOPE_READ,
                      expires_at=datetime.now() + timedelta(days=days), created_by=user_id, updated_by=user_id)
    db.add(row)
    db.commit()
    return row, raw


def authenticate(db: Session, raw: str, *, now: datetime | None = None) -> AgentMcpKey | None:
    raw = (raw or "").strip()
    if not raw.startswith(PREFIX):
        return None
    now = now or datetime.now()
    row = db.scalar(select(AgentMcpKey).where(AgentMcpKey.token_hash == hash_token(raw), AgentMcpKey.revoked_at.is_(None)))
    if row is None or (row.expires_at is not None and row.expires_at <= now):
        return None
    return row


def touch(db: Session, row: AgentMcpKey) -> None:
    row.last_used_at = datetime.now()
    db.commit()


def revoke(db: Session, row: AgentMcpKey) -> None:
    row.revoked_at = datetime.now()
    db.commit()


def revoke_all(db: Session, user_id: int) -> int:
    n = 0
    for row in list_for_user(db, user_id):
        row.revoked_at = datetime.now()
        n += 1
    if n:
        db.commit()
    return n


def serialize(row: AgentMcpKey) -> dict:
    iso = lambda d: d.isoformat(timespec="seconds") if d else None  # noqa: E731
    return {"id": row.id, "name": row.name, "hint": f"…{row.key_hint}", "scope": int(row.scope or 0),
            "scope_label": SCOPE_LABELS.get(int(row.scope or 0), "?"), "expires_at": iso(row.expires_at),
            "last_used_at": iso(row.last_used_at), "created_at": iso(row.created_at)}
