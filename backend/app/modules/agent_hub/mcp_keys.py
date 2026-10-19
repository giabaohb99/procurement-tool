"""KHÓA KẾT NỐI MCP cá nhân (ai-CR-063, M-02 của `doc/agent-hub/04`).

Mỗi người tự tạo khóa ở Trang cá nhân → «Khóa AI» → «Kết nối MCP», dán vào ứng dụng AI của mình (Claude
Desktop, Cursor, ChatGPT…) để ứng dụng đó gọi bộ tool ERP DƯỚI ĐÚNG QUYỀN của người đó. Khóa:
  - gác bằng băm SHA-256; ai-CR-221 (đại ca chốt 19/10): giữ thêm bản MÃ HÓA HAI CHIỀU (`raw_view`, Fernet suy từ
    JWT_SECRET như `app_settings.encrypt`) để CHỦ KHÓA xem lại / chép đoạn cấu hình đã điền khóa. Quản trị không xem được;
    đổi JWT_SECRET thì bản xem lại hỏng (khóa vẫn chạy, chỉ phải tạo lại mới xem được);
  - bật / tắt tạm được (`disabled_at`, khác thu hồi);
  - có hạn (mặc định 90 ngày), gỡ được, mỗi lượt gọi ghi `last_used_at`;
  - hai mức: CHỈ ĐỌC (tra cứu) · ĐƯỢC GHI (thêm soạn nháp + tạo/gửi duyệt hai bước + báo lỗi).
Nghỉ việc thì đóng cùng lúc phiên (employee.service._revoke_bot_access).
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from enum import IntEnum

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
#  ai-CR-218 (K14 OAuth): loại khóa — dán tay (tự tạo / phát hộ) hay kết nối OAuth của một ứng dụng AI. Mã truy cập OAuth
#  cũng mang tiền tố PREFIX nên cổng MCP phân giải chung một đường; trần MAX_KEYS chỉ tính khóa dán tay.
KIND_MANUAL = 1
KIND_OAUTH = 2
KIND_LABELS = {KIND_MANUAL: "Khóa dán tay", KIND_OAUTH: "Kết nối OAuth"}


def hash_token(raw: str) -> str:
    return hashlib.sha256(f"agent-mcp:{raw}".encode()).hexdigest()


def list_for_user(db: Session, user_id: int) -> list[AgentMcpKey]:
    return list(db.scalars(select(AgentMcpKey).where(AgentMcpKey.user_id == user_id, AgentMcpKey.revoked_at.is_(None))
                           .order_by(AgentMcpKey.id.desc())))


def create(db: Session, user_id: int, *, name: str = "", scope: int = SCOPE_READ, days: int = DEFAULT_DAYS) -> tuple[AgentMcpKey, str]:
    """Tạo khóa, trả (dòng, KHÓA THÔ — chỉ hiện một lần)."""
    if len([k for k in list_for_user(db, user_id) if int(k.kind or KIND_MANUAL) != KIND_OAUTH]) >= MAX_KEYS:
        raise ValueError(f"Mỗi tài khoản tối đa {MAX_KEYS} khóa MCP đang hiệu lực; gỡ bớt rồi tạo.")
    days = max(1, min(int(days or DEFAULT_DAYS), MAX_DAYS))
    raw = PREFIX + secrets.token_urlsafe(30)
    from app.core import app_settings

    row = AgentMcpKey(user_id=user_id, name=(name or "").strip()[:80] or "MCP", token_hash=hash_token(raw),
                      key_hint=raw[-4:], scope=SCOPE_WRITE if int(scope) == SCOPE_WRITE else SCOPE_READ,
                      expires_at=datetime.now() + timedelta(days=days), raw_view=app_settings.encrypt(raw),
                      created_by=user_id, updated_by=user_id)
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
    if is_unclaimed(row):          # ai-CR-212: khóa phát hộ chưa nhận thì chưa dùng được
        return None
    if row.disabled_at is not None:      # ai-CR-221: chủ khóa tắt tạm
        return None
    if oauth_access_expired(row, now):   # ai-CR-218: mã truy cập OAuth hạn ngắn, hết thì ứng dụng tự làm mới
        return None
    return row


def why_rejected(db: Session, raw: str, *, now: datetime | None = None) -> tuple[int, str]:
    """Khóa bị từ chối vì sao — cho nhật ký MCP (ai-CR-209). Trả (id khóa nếu có thật, lý do). Không nói gì cho người gọi:
    câu trả về ngoài vẫn chung một câu, chỉ nhật ký biết khóa hết hạn hay bị thu hồi."""
    from .mcp_log import REASON_BAD_KEY, REASON_EXPIRED, REASON_REVOKED

    raw = (raw or "").strip()
    if not raw.startswith(PREFIX):
        return 0, REASON_BAD_KEY
    row = db.scalar(select(AgentMcpKey).where(AgentMcpKey.token_hash == hash_token(raw)))
    if row is None:
        return 0, REASON_BAD_KEY
    if row.revoked_at is not None:
        return int(row.id), REASON_REVOKED
    if row.expires_at is not None and row.expires_at <= (now or datetime.now()):
        return int(row.id), REASON_EXPIRED
    if is_unclaimed(row):
        from .mcp_log import REASON_UNCLAIMED

        return int(row.id), REASON_UNCLAIMED
    if row.disabled_at is not None:
        from .mcp_log import REASON_DISABLED

        return int(row.id), REASON_DISABLED
    if oauth_access_expired(row, now):
        from .mcp_log import REASON_OAUTH_EXPIRED

        return int(row.id), REASON_OAUTH_EXPIRED
    return int(row.id), REASON_BAD_KEY


def touch(db: Session, row: AgentMcpKey) -> None:
    row.last_used_at = datetime.now()
    db.commit()


def revoke(db: Session, row: AgentMcpKey) -> None:
    revoke_rows(db, [row])


def revoke_all(db: Session, user_id: int) -> int:
    return revoke_rows(db, list_for_user(db, user_id))


def serialize(row: AgentMcpKey) -> dict:
    iso = lambda d: d.isoformat(timespec="seconds") if d else None  # noqa: E731
    st = state_of(row)
    return {"id": row.id, "name": row.name, "hint": f"…{row.key_hint}", "scope": int(row.scope or 0),
            "scope_label": SCOPE_LABELS.get(int(row.scope or 0), "?"), "expires_at": iso(row.expires_at),
            "last_used_at": iso(row.last_used_at), "created_at": iso(row.created_at),
            "state": int(st), "state_label": STATE_LABELS[st], "issued_by": int(row.issued_by or 0),
            "claimed_at": iso(row.claimed_at), "batch_id": row.batch_id or "", "user_id": int(row.user_id or 0),
            "kind": int(row.kind or KIND_MANUAL), "kind_label": KIND_LABELS.get(int(row.kind or KIND_MANUAL), "?"),
            #  ai-CR-221: `enabled` = công tắc của chủ khóa; `revealable` = xem lại được (khóa tạo trước ai-CR-221, kết nối
            #  OAuth hay khóa chưa nhận thì không — màn hiện «tạo lại để xem»). KHÔNG bao giờ trả khóa thô ở đây.
            "enabled": row.disabled_at is None, "disabled_at": iso(row.disabled_at),
            "revealable": bool(row.raw_view) and st in (KeyState.ACTIVE, KeyState.DISABLED)}


# ---------------------------------------------------------------------------------------------------------------------
# ai-CR-212 (K4 doc/erp/21 §5.3): PHÁT KHÓA HỘ — quản trị phát cho một người / cả phòng, khóa «chờ nhận» tới khi chủ khóa
# bấm Nhận ở Trang cá nhân (xem được đúng MỘT lần). Chỉ phát mức CHỈ ĐỌC (khóa được ghi chỉ người dùng tự tạo — Q5).
# ---------------------------------------------------------------------------------------------------------------------
class KeyState(IntEnum):
    PENDING = 1      # chờ nhận
    ACTIVE = 2       # đang dùng
    EXPIRED = 3      # hết hạn
    REVOKED = 4      # đã thu hồi (giữ dòng để đối soát)
    DISABLED = 5     # ai-CR-221: chủ khóa tắt tạm — bật lại được, khác thu hồi


STATE_LABELS = {KeyState.PENDING: "Chờ nhận", KeyState.ACTIVE: "Đang dùng", KeyState.EXPIRED: "Hết hạn",
                KeyState.REVOKED: "Đã thu hồi", KeyState.DISABLED: "Đang tắt"}
ISSUE_DAYS = (7, 30, 90, 180, 365)
BATCH_MAX = 50


def is_unclaimed(row: AgentMcpKey) -> bool:
    return bool(row.issued_by) and row.claimed_at is None


def oauth_access_expired(row: AgentMcpKey, now: datetime | None = None) -> bool:
    """Kết nối OAuth: mã truy cập hiện hành đã hết hạn (khác hạn của cả kết nối ở `expires_at`)."""
    if int(row.kind or KIND_MANUAL) != KIND_OAUTH:
        return False
    return row.access_expires_at is None or row.access_expires_at <= (now or datetime.now())


def state_of(row: AgentMcpKey, now: datetime | None = None) -> KeyState:
    if row.revoked_at is not None:
        return KeyState.REVOKED
    if row.expires_at is not None and row.expires_at <= (now or datetime.now()):
        return KeyState.EXPIRED
    if is_unclaimed(row):
        return KeyState.PENDING
    return KeyState.DISABLED if row.disabled_at is not None else KeyState.ACTIVE


def live_count(db: Session, user_id: int, now: datetime | None = None) -> int:
    """Số khóa còn hiệu lực (đang dùng + chờ nhận + đang tắt — tắt rồi bật lại được) — trần `MAX_KEYS` tính trên số này."""
    return sum(1 for k in list_for_user(db, user_id)
               if int(k.kind or KIND_MANUAL) != KIND_OAUTH
               and state_of(k, now) in (KeyState.PENDING, KeyState.ACTIVE, KeyState.DISABLED))


def issue(db: Session, owner_id: int, issued_by: int, *, days: int, name: str = "", batch_id: str = "") -> AgentMcpKey:
    """Phát hộ một khóa CHỈ ĐỌC ở trạng thái chờ nhận. Khóa thô chỉ nằm trong `raw_sealed` (Fernet) tới khi nhận."""
    from app.core import app_settings

    if int(days) not in ISSUE_DAYS:
        raise ValueError(f"Hạn khóa chỉ chọn: {', '.join(map(str, ISSUE_DAYS))} ngày.")
    if live_count(db, owner_id) >= MAX_KEYS:
        raise ValueError(f"đã đủ {MAX_KEYS} khóa còn hiệu lực")
    raw = PREFIX + secrets.token_urlsafe(30)
    row = AgentMcpKey(user_id=owner_id, name=(name or "").strip()[:80] or "Khóa AI do quản trị phát",
                      token_hash=hash_token(raw), key_hint=raw[-4:], scope=SCOPE_READ,
                      expires_at=datetime.now() + timedelta(days=int(days)), issued_by=int(issued_by),
                      raw_sealed=app_settings.encrypt(raw), batch_id=(batch_id or "")[:32],
                      created_by=int(issued_by), updated_by=int(issued_by))
    db.add(row)
    db.flush()
    return row


def pending_for_user(db: Session, user_id: int) -> list[AgentMcpKey]:
    return [k for k in list_for_user(db, user_id) if state_of(k) == KeyState.PENDING]


def claim(db: Session, user_id: int, key_id: int) -> str | None:
    """Chủ khóa nhận khóa phát hộ: trả KHÓA THÔ đúng một lần, xóa trắng bản niêm phong. Lần hai / không phải của mình /
    hết hạn / thu hồi → None."""
    from app.core import app_settings

    row = db.get(AgentMcpKey, int(key_id))
    if row is None or int(row.user_id) != int(user_id) or state_of(row) != KeyState.PENDING or not row.raw_sealed:
        return None
    raw = app_settings._decrypt(row.raw_sealed)
    if not raw:
        return None
    row.claimed_at = datetime.now()
    row.raw_view = row.raw_sealed      # ai-CR-221: nhận xong chủ khóa vẫn xem lại được (cùng một bản Fernet)
    row.raw_sealed = ""
    row.updated_by = int(user_id)
    db.commit()
    return raw


def revoke_rows(db: Session, rows: list[AgentMcpKey], by_user_id: int = 0) -> int:
    n = 0
    now = datetime.now()
    for row in rows:
        if row.revoked_at is None:
            row.revoked_at = now
            row.raw_sealed = ""            # khóa chưa nhận mà bị thu hồi: bỏ luôn bản niêm phong
            row.raw_view = ""              # ai-CR-221: thu hồi là xóa luôn bản xem lại
            row.refresh_hash = ""          # ai-CR-218: kết nối OAuth bị thu hồi thì mã làm mới cũng chết ngay
            row.updated_by = int(by_user_id)
            n += 1
    if n:
        db.commit()
    return n


# ---------------------------------------------------------------------------------------------------------------------
# ai-CR-221 (đại ca chốt 19/10): CHỦ KHÓA xem lại khóa + bật / tắt. Chỉ người sở hữu, đăng nhập web — không qua MCP, quản
# trị không xem được. Mỗi lần xem / bật / tắt ghi một dòng nhật ký cổng MCP (controller).
# ---------------------------------------------------------------------------------------------------------------------
class KeyNotFound(LookupError):
    """Không có khóa này trong khóa của người gọi (của người khác cũng báo y vậy — không lộ id)."""


def _own_row(db: Session, user_id: int, key_id: int) -> AgentMcpKey:
    row = db.get(AgentMcpKey, int(key_id))
    if row is None or int(row.user_id) != int(user_id) or row.revoked_at is not None:
        raise KeyNotFound(key_id)
    return row


def reveal(db: Session, user_id: int, key_id: int) -> tuple[AgentMcpKey, str]:
    """(dòng, KHÓA THÔ) cho chủ khóa. Không xem được → ValueError kèm câu cho người dùng."""
    from app.core import app_settings

    row = _own_row(db, user_id, key_id)
    if int(row.kind or KIND_MANUAL) == KIND_OAUTH:
        raise ValueError("Kết nối OAuth không có khóa để xem — ứng dụng AI tự giữ mã truy cập.")
    st = state_of(row)
    if st == KeyState.PENDING:
        raise ValueError("Khóa phát hộ chưa nhận — bấm Nhận để lấy khóa.")
    if st == KeyState.EXPIRED:
        raise ValueError("Khóa đã hết hạn — tạo khóa mới.")
    raw = app_settings._decrypt(row.raw_view) if row.raw_view else ""
    if not raw:
        raise ValueError("Khóa này tạo trước khi có chức năng xem lại (hoặc bí mật máy chủ đã đổi) — tạo khóa mới để xem.")
    return row, raw


def set_enabled(db: Session, user_id: int, key_id: int, enabled: bool) -> AgentMcpKey:
    """Bật / tắt tạm khóa của chính mình (cả kết nối OAuth). Khóa chờ nhận / hết hạn → ValueError."""
    row = _own_row(db, user_id, key_id)
    st = state_of(row)
    if st == KeyState.PENDING:
        raise ValueError("Khóa phát hộ chưa nhận thì chưa dùng được — không cần bật / tắt.")
    if st == KeyState.EXPIRED:
        raise ValueError("Khóa đã hết hạn — tạo khóa mới.")
    if bool(enabled) == (row.disabled_at is None):
        return row
    row.disabled_at = None if enabled else datetime.now()
    row.updated_by = int(user_id)
    db.commit()
    return row


def keys_of_users(db: Session, user_ids: set[int]) -> list[AgentMcpKey]:
    if not user_ids:
        return []
    return list(db.scalars(select(AgentMcpKey).where(AgentMcpKey.user_id.in_(user_ids)).order_by(AgentMcpKey.id.desc())))


def owner_ids(db: Session) -> set[int]:
    return {int(u) for u in db.scalars(select(AgentMcpKey.user_id).distinct())}
