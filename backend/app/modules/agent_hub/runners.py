"""Sổ MÁY SỬA MÃ (ai-CR-054, D-03 + D-05 của `doc/agent-hub/04`).

Đại ca chốt 24/09/2026: phần chạy Claude Code tách khỏi bot thành «runner», đặt trên máy đại ca (máy số 1)
và máy nào đại ca đăng ký thêm. Bot (trên dev) chỉ xếp việc; máy nối lên, kéo việc về, ghi kết quả lên.

  - Mỗi máy = một dòng `tab_agent_runner`: tên, chủ máy (tài khoản ERP), mã máy (chỉ giữ băm), cờ được deploy
    dev, lần liên lạc cuối. Đăng ký/gỡ bằng CÂU NHẮN ở chat đại ca («thêm máy của anh Được», «tắt máy …»),
    giống K-01. Gỡ là máy bị từ chối ngay ở lượt tiếp theo — không build, không khởi động lại gì.
  - Mỗi máy nghe hàng đợi RIÊNG `agent_code.<tên máy>`. Vé nằm trong Redis tới khi máy nối vào, nên máy tắt
    thì việc chờ, không mất. Việc DÍNH máy đã bắt đầu nó (`AgentTask.runner_id`): worktree và phiên Claude
    Code chỉ có trên máy đó. Việc mới → máy đang bật ít việc nhất; đại ca chỉ định được («AI-0012 cho máy anh
    Được làm»). Không có máy nào bật → máy mặc định (`AGENT_DEFAULT_RUNNER`) hoặc máy liên lạc gần nhất,
    bot nói rõ đang chờ máy nào.
  - Chưa đăng ký máy nào (phase 0/1, bot và runner cùng máy) → hàng đợi cũ `agent_code`, y như trước.

Máy tự xưng bằng `AGENT_RUNNER_NAME` + `AGENT_RUNNER_TOKEN` trong `.env` của runner; mỗi 30 giây ghi «tôi còn
sống». Bot coi máy «đang bật» khi liên lạc trong `AGENT_RUNNER_ONLINE_SEC` gần nhất.
"""
from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings

from .constants import RUN_RUNNING
from .model import AgentRun, AgentRunner, AgentTask

LEGACY_QUEUE = "agent_code"
HEARTBEAT_SEC = 30


def hash_token(raw: str) -> str:
    return hashlib.sha256(f"agent-runner:{raw}".encode()).hexdigest()


def queue_name(runner_name: str) -> str:
    return f"{LEGACY_QUEUE}.{runner_name}" if runner_name else LEGACY_QUEUE


def slug(name: str) -> str:
    """«máy của anh Được» → `may-cua-anh-duoc`: tên hàng đợi và tên container không có dấu/khoảng trắng."""
    import unicodedata

    s = (name or "").replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:40]


# ---------------------------------------------------------------------------
# Sổ máy
# ---------------------------------------------------------------------------
def active(db: Session) -> list[AgentRunner]:
    return list(db.scalars(select(AgentRunner).where(AgentRunner.revoked_at.is_(None)).order_by(AgentRunner.id)))


def by_name(db: Session, name: str) -> AgentRunner | None:
    return db.scalar(select(AgentRunner).where(AgentRunner.name == name, AgentRunner.revoked_at.is_(None)))


def find(db: Session, text: str) -> list[AgentRunner]:
    """Máy khớp tên máy hoặc tên chủ máy (không dấu, chuỗi con)."""
    from .grants import fold, _names_of

    key = fold(text)
    if not key:
        return []
    from app.modules.user.model import User

    out = []
    for r in active(db):
        hay = [r.name, r.note]
        owner = db.get(User, r.owner_user_id) if r.owner_user_id else None
        if owner is not None:
            hay += _names_of(db, owner)
        if any(key == fold(h) or (len(key) >= 3 and key in fold(h)) for h in hay if h):
            out.append(r)
    return out


def is_online(runner: AgentRunner | None, *, now: datetime | None = None) -> bool:
    if runner is None or runner.revoked_at is not None or runner.last_seen_at is None:
        return False
    now = now or datetime.now()
    return runner.last_seen_at >= now - timedelta(seconds=settings.AGENT_RUNNER_ONLINE_SEC)


def register(db: Session, name: str, *, owner_user_id: int = 0, note: str = "", by_chat: str = "",
             can_deploy: bool = False) -> tuple[AgentRunner, str]:
    """Thêm máy, trả (dòng, MÃ MÁY THÔ — chỉ hiện đúng một lần). Trùng tên máy đang sống thì lỗi."""
    name = slug(name)
    if not name:
        raise ValueError("Tên máy trống.")
    if by_name(db, name) is not None:
        raise ValueError(f"Đã có máy tên «{name}».")
    raw = secrets.token_urlsafe(24)
    row = AgentRunner(name=name, owner_user_id=owner_user_id, token_hash=hash_token(raw), note=note[:255],
                      can_deploy=bool(can_deploy), registered_by_chat=str(by_chat)[:50], created_by=0, updated_by=0)
    db.add(row)
    db.commit()
    return row, raw


def revoke(db: Session, runner: AgentRunner) -> None:
    runner.revoked_at = datetime.now()
    db.commit()


def authenticate(db: Session, name: str, raw_token: str) -> AgentRunner | None:
    """Máy tự xưng lúc nhịp tim và lúc nhận việc. Sai tên/mã hoặc đã gỡ → None."""
    if not name or not raw_token:
        return None
    row = by_name(db, name)
    if row is None or row.token_hash != hash_token(raw_token):
        return None
    return row


def beat(db: Session, name: str, raw_token: str, *, version: str = "") -> AgentRunner | None:
    row = authenticate(db, name, raw_token)
    if row is None:
        return None
    row.last_seen_at = datetime.now()
    if version:
        row.version = version[:50]
    db.commit()
    return row


# ---------------------------------------------------------------------------
# Chia việc (D-05)
# ---------------------------------------------------------------------------
def running_count(db: Session, runner_id: int) -> int:
    return int(db.scalar(select(func.count(AgentRun.id)).join(AgentTask, AgentTask.id == AgentRun.task_id).where(
        AgentTask.runner_id == runner_id, AgentRun.status == RUN_RUNNING)) or 0)


def pick(db: Session, task: AgentTask) -> AgentRunner | None:
    """Máy cho việc này. Dính máy cũ nếu có; không thì máy đang bật ít việc nhất; không máy nào bật thì máy mặc
    định hoặc máy liên lạc gần nhất (vé chờ trong hàng đợi). Sổ trống → None = hàng đợi cũ."""
    if task.runner_id:
        cur = db.get(AgentRunner, task.runner_id)
        if cur is not None and cur.revoked_at is None:
            return cur
    rows = active(db)
    if not rows:
        return None
    online = [r for r in rows if is_online(r)]
    if online:
        return min(online, key=lambda r: (running_count(db, r.id), r.id))
    default = by_name(db, settings.AGENT_DEFAULT_RUNNER) if settings.AGENT_DEFAULT_RUNNER else None
    if default is not None:
        return default
    return max(rows, key=lambda r: (r.last_seen_at or datetime.min, -r.id))


def assign(db: Session, task: AgentTask, runner: AgentRunner | None) -> str:
    """Ghi máy vào việc (dính từ đây) và trả tên hàng đợi."""
    if runner is None:
        return LEGACY_QUEUE
    if task.runner_id != runner.id:
        task.runner_id = runner.id
        db.commit()
    return queue_name(runner.name)


def queue_for_task(db: Session, task_id: int) -> str:
    task = db.get(AgentTask, task_id)
    if task is None:
        return LEGACY_QUEUE
    return assign(db, task, pick(db, task))


def describe(db: Session, runner: AgentRunner) -> str:
    from .service import describe_user
    from app.modules.user.model import User

    owner = describe_user(db, db.get(User, runner.owner_user_id))[0] if runner.owner_user_id else ""
    return f"{runner.name}" + (f" ({owner})" if owner else "")


# ---------------------------------------------------------------------------
# Câu nhắn của đại ca
# ---------------------------------------------------------------------------
_TAIL = r"(\s+(nhé|nha|đi|luôn|giúp em|giúp anh))*[.!]*"
_ADD = re.compile(rf"^(thêm|đăng ký|dang ky|đăng kí)\s+máy(\s+sửa mã)?(\s+(của|cho))?\s+(?P<name>.+?){_TAIL}$")
_REMOVE = re.compile(rf"^(tắt|gỡ|bỏ|xóa|thu hồi)\s+máy(\s+sửa mã)?(\s+của)?\s+(?P<name>.+?){_TAIL}$")
_LIST = re.compile(r"^(máy nào (đang )?(bật|sống|chạy|online)|(danh sách|ds|xem)\s+máy(\s+sửa mã)?|các máy( sửa mã)?)")
_ASSIGN = re.compile(rf"^(?P<code>ai[-\s]?\d+)\s+(cho|giao|để)\s+máy(\s+(của|cho))?\s+(?P<name>.+?)\s+làm{_TAIL}$"
                     rf"|^(cho|giao)\s+(?P<code2>ai[-\s]?\d+)\s+cho\s+máy(\s+của)?\s+(?P<name2>.+?){_TAIL}$")
_DEPLOY_ON = re.compile(rf"^(cho|mở)\s+máy(\s+của)?\s+(?P<name>.+?)\s+(được\s+)?deploy(\s+dev)?{_TAIL}$")
_DEPLOY_OFF = re.compile(rf"^(cấm|tắt|không cho)\s+máy(\s+của)?\s+(?P<name>.+?)\s+deploy(\s+dev)?{_TAIL}$")


def parse(text: str) -> dict | None:
    low = text.strip().lower()
    if "máy" not in low:
        return None
    if _LIST.match(low):
        return {"op": "list"}
    if m := _ASSIGN.match(low):
        code = m.group("code") or m.group("code2")
        return {"op": "assign", "code": code, "name": (m.group("name") or m.group("name2") or "").strip()}
    if m := _DEPLOY_ON.match(low):
        return {"op": "deploy_on", "name": m.group("name").strip()}
    if m := _DEPLOY_OFF.match(low):
        return {"op": "deploy_off", "name": m.group("name").strip()}
    if m := _ADD.match(low):
        return {"op": "add", "name": m.group("name").strip()}
    if m := _REMOVE.match(low):
        return {"op": "remove", "name": m.group("name").strip()}
    return None
