"""Nhật ký + trần tần suất của cổng MCP (ai-CR-209, K3 của doc/erp/21 §4.3 + §5.4).

- Mỗi lượt JSON-RPC một dòng `tab_agent_mcp_call`, kể cả `initialize` / `tools/list` / thông báo, lượt khóa sai và lượt
  bị chặn vì quá tần suất. Phòng ban / pháp nhân chụp từ hồ sơ nhân sự LÚC GỌI.
- Tên ứng dụng (`client_name`) chỉ có trong `initialize.clientInfo` — nhớ theo khóa (bộ nhớ tiến trình, hụt thì tra dòng
  `initialize` gần nhất của khóa đó) để gắn cho các lượt sau.
- Trần tần suất hai lớp, cửa sổ một phút: theo khóa (`AGENT_MCP_RATE_PER_KEY`) và theo IP (`AGENT_MCP_RATE_PER_IP`);
  lượt khóa sai có trần riêng chặt hơn theo IP (`AGENT_MCP_BAD_KEY_PER_IP`). Đếm ở Redis (chung mọi worker), Redis hỏng
  thì đếm trong bộ nhớ tiến trình — thà chặn lỏng hơn chứ không làm sập cổng.
- Chống dội đầy bảng: lượt khóa sai / quá tần suất chỉ GHI tối đa `LOG_CAP_PER_MIN` dòng mỗi phút cho mỗi IP / khóa; quá
  nữa vẫn từ chối nhưng không ghi.
- Dọn: giữ chi tiết `AGENT_MCP_LOG_RETENTION_DAYS` (180) ngày; quá hạn gom vào `tab_agent_mcp_call_daily` rồi xóa.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import date, datetime, timedelta
from enum import IntEnum

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings

from .model import AgentMcpCall, AgentMcpCallDaily

log = logging.getLogger("app.agent_hub.mcp_log")

WINDOW_SEC = 60
LOG_CAP_PER_MIN = 10        # trần số dòng ghi mỗi phút cho lượt khóa sai / quá tần suất (mỗi IP hoặc mỗi khóa)
CLIENT_TTL_SEC = 30 * 60
PURGE_BATCH_DAYS = 31       # mỗi lượt dọn gom tối đa bao nhiêu ngày (lần đầu chạy trên dữ liệu cũ không kéo cả năm)


class CallStatus(IntEnum):
    OK = 1
    DENIED = 2
    ERROR = 3


CALL_STATUS_LABELS = {CallStatus.OK: "Thành công", CallStatus.DENIED: "Bị từ chối", CallStatus.ERROR: "Lỗi"}

REASON_BAD_KEY = "Khóa sai"
REASON_EXPIRED = "Khóa đã hết hạn"
REASON_REVOKED = "Khóa đã bị thu hồi"
REASON_INACTIVE = "Tài khoản đã bị khóa"
REASON_RATE_KEY = "Quá tần suất (khóa)"
REASON_RATE_IP = "Quá tần suất (IP)"
REASON_RATE_BAD = "Quá tần suất (khóa sai liên tục)"


# --- IP ------------------------------------------------------------------------------------------------------------
def client_ip(request) -> str:
    """IP người gọi. Cổng đứng sau Cloudflare tunnel + ERP proxy (chép nguyên header) nên `request.client` là máy trung
    gian: ưu tiên `CF-Connecting-IP` (Cloudflare tự đặt), rồi `X-Real-IP`, rồi IP đầu của `X-Forwarded-For`."""
    h = request.headers
    for name in ("cf-connecting-ip", "x-real-ip"):
        if h.get(name):
            return h[name].strip()[:45]
    if h.get("x-forwarded-for"):
        return h["x-forwarded-for"].split(",")[0].strip()[:45]
    return (request.client.host if request.client else "")[:45]


# --- đếm theo phút -------------------------------------------------------------------------------------------------
_mem_lock = threading.Lock()
_mem: dict[str, int] = {}
_redis_client = None


def _redis():
    global _redis_client
    if _redis_client is None:
        import redis

        _redis_client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.3, socket_timeout=0.3)
    return _redis_client


def _count(bucket: str, now: float | None = None) -> int:
    """Tăng bộ đếm của `bucket` trong phút hiện tại, trả giá trị sau khi tăng."""
    slot = int((now or time.time()) // WINDOW_SEC)
    key = f"mcp:rl:{bucket}:{slot}"
    try:
        r = _redis()
        n = int(r.incr(key))
        if n == 1:
            r.expire(key, WINDOW_SEC + 5)
        return n
    except Exception:  # noqa: BLE001 — Redis hỏng: đếm trong tiến trình
        with _mem_lock:
            for k in [k for k in _mem if not k.endswith(f":{slot}")]:
                del _mem[k]
            _mem[key] = _mem.get(key, 0) + 1
            return _mem[key]


def over_limit(bucket: str, limit: int, now: float | None = None) -> bool:
    return limit > 0 and _count(bucket, now) > limit


def may_log(bucket: str, now: float | None = None) -> bool:
    """Lượt bị từ chối hàng loạt: chỉ ghi `LOG_CAP_PER_MIN` dòng đầu mỗi phút."""
    return _count(f"log:{bucket}", now) <= LOG_CAP_PER_MIN


# --- tên ứng dụng theo khóa -----------------------------------------------------------------------------------------
_clients: dict[int, tuple[str, float]] = {}


def client_from_initialize(params: dict) -> str:
    info = params.get("clientInfo") if isinstance(params, dict) else None
    if not isinstance(info, dict):
        return ""
    name = str(info.get("name") or "").strip()
    version = str(info.get("version") or "").strip()
    return (f"{name} {version}".strip() if name else "")[:100]


def remember_client(key_id: int, name: str) -> None:
    if key_id and name:
        _clients[int(key_id)] = (name, time.time())


def client_of(db: Session, key_id: int) -> str:
    if not key_id:
        return ""
    hit = _clients.get(int(key_id))
    if hit and time.time() - hit[1] < CLIENT_TTL_SEC:
        return hit[0]
    name = db.scalar(select(AgentMcpCall.client_name).where(AgentMcpCall.key_id == key_id, AgentMcpCall.client_name != "")
                     .order_by(AgentMcpCall.id.desc()).limit(1)) or ""
    _clients[int(key_id)] = (name, time.time())
    return name


# --- ghi -----------------------------------------------------------------------------------------------------------
def who(db: Session, user) -> dict:
    """Chụp người gọi: nhân sự + phòng ban + pháp nhân (ErpUser ở chế độ tách dịch vụ, ORM User ở chế độ nhúng)."""
    if user is None:
        return {"user_id": 0, "employee_id": 0, "department_id": 0, "company_id": 0}
    dept, comp = getattr(user, "department_id", None), getattr(user, "company_id", None)
    if dept is None or comp is None:
        from .erp import _Local

        dept, comp = _Local.org_of(db, user)
    return {"user_id": int(user.id or 0), "employee_id": int(getattr(user, "employee_id", 0) or 0),
            "department_id": int(dept or 0), "company_id": int(comp or 0)}


def new_row(*, key_id: int = 0, person: dict | None = None, client_name: str = "", method: str = "", tool: str = "",
            status: int = CallStatus.OK, reason: str = "", duration_ms: int = 0, ip: str = "") -> AgentMcpCall:
    return AgentMcpCall(key_id=int(key_id or 0), **(person or who(None, None)), client_name=(client_name or "")[:100],
                        method=(method or "")[:40], tool=(tool or "")[:80], status=int(status),
                        deny_reason=(reason or "")[:200], duration_ms=max(0, int(duration_ms or 0)), ip=(ip or "")[:45],
                        created_at=datetime.now())


def save(db: Session, rows: list[AgentMcpCall]) -> None:
    """Ghi nhật ký — hỏng thì chỉ mất dòng nhật ký, KHÔNG làm hỏng lượt gọi."""
    if not rows:
        return
    try:
        db.add_all(rows)
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        log.warning("mcp_log: không ghi được %d dòng nhật ký", len(rows), exc_info=True)


# --- dọn -----------------------------------------------------------------------------------------------------------
def _as_date(v) -> date:
    return v if isinstance(v, date) and not isinstance(v, datetime) else date.fromisoformat(str(v)[:10])


def purge(db: Session, now: datetime | None = None) -> dict:
    """Gom dòng chi tiết quá hạn vào bảng đếm theo ngày rồi xóa. Chạy lại cũng không đếm trùng (cộng rồi xóa trong cùng
    một giao dịch, theo từng ngày)."""
    now = now or datetime.now()
    cutoff = datetime.combine((now - timedelta(days=int(settings.AGENT_MCP_LOG_RETENTION_DAYS))).date(), datetime.min.time())
    first = db.scalar(select(func.min(AgentMcpCall.created_at)).where(AgentMcpCall.created_at < cutoff))
    if first is None:
        return {"days": 0, "deleted": 0}
    days = deleted = 0
    day = first.date()
    while day < cutoff.date() and days < PURGE_BATCH_DAYS:
        start, end = datetime.combine(day, datetime.min.time()), datetime.combine(day + timedelta(days=1), datetime.min.time())
        rng = (AgentMcpCall.created_at >= start, AgentMcpCall.created_at < end)
        groups = db.execute(select(AgentMcpCall.user_id, AgentMcpCall.key_id, AgentMcpCall.method, AgentMcpCall.tool,
                                   AgentMcpCall.status, func.count(AgentMcpCall.id),
                                   func.coalesce(func.sum(AgentMcpCall.duration_ms), 0))
                            .where(*rng).group_by(AgentMcpCall.user_id, AgentMcpCall.key_id, AgentMcpCall.method,
                                                  AgentMcpCall.tool, AgentMcpCall.status)).all()
        for uid, kid, method, tool, status, n, ms in groups:
            row = db.scalar(select(AgentMcpCallDaily).where(
                AgentMcpCallDaily.day == day, AgentMcpCallDaily.user_id == uid, AgentMcpCallDaily.key_id == kid,
                AgentMcpCallDaily.method == method, AgentMcpCallDaily.tool == tool, AgentMcpCallDaily.status == status))
            if row is None:
                row = AgentMcpCallDaily(day=day, user_id=uid, key_id=kid, method=method, tool=tool, status=status,
                                        calls=0, total_ms=0)
                db.add(row)
            row.calls = int(row.calls or 0) + int(n)
            row.total_ms = int(row.total_ms or 0) + int(ms or 0)
        deleted += db.query(AgentMcpCall).filter(*rng).delete(synchronize_session=False)
        db.commit()
        days += 1
        day += timedelta(days=1)
    return {"days": days, "deleted": deleted}


# --- đọc (màn G1 / G6) ---------------------------------------------------------------------------------------------
def _filtered(stmt, *, user_id: int | None, key_id: int | None = None, tool: str = "", status: int | None = None,
              d_from: date | None = None, d_to: date | None = None, model=AgentMcpCall):
    col_day = model.created_at if model is AgentMcpCall else model.day
    if user_id is not None:
        stmt = stmt.where(model.user_id == user_id)
    if key_id is not None:
        stmt = stmt.where(model.key_id == key_id)
    if tool:
        stmt = stmt.where(model.tool == tool)
    if status is not None:
        stmt = stmt.where(model.status == status)
    if d_from is not None:
        stmt = stmt.where(col_day >= (datetime.combine(d_from, datetime.min.time()) if model is AgentMcpCall else d_from))
    if d_to is not None:
        stmt = stmt.where(col_day < (datetime.combine(d_to + timedelta(days=1), datetime.min.time())
                                     if model is AgentMcpCall else d_to + timedelta(days=1)))
    return stmt


def list_calls(db: Session, *, page: int = 1, size: int = 50, **flt) -> tuple[int, list[AgentMcpCall]]:
    base = _filtered(select(AgentMcpCall), **flt)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = list(db.scalars(base.order_by(AgentMcpCall.id.desc()).offset((page - 1) * size).limit(size)))
    return int(total), rows


def serialize(row: AgentMcpCall) -> dict:
    status = int(row.status or 0)
    return {"id": row.id, "created_at": row.created_at.isoformat(timespec="seconds") if row.created_at else None,
            "key_id": row.key_id, "user_id": row.user_id, "employee_id": row.employee_id,
            "department_id": row.department_id, "company_id": row.company_id, "client_name": row.client_name,
            "method": row.method, "tool": row.tool, "skill_id": row.skill_id, "status": status,
            "status_label": CALL_STATUS_LABELS.get(status, "?"), "deny_reason": row.deny_reason,
            "duration_ms": row.duration_ms, "ip": row.ip}


def daily_totals(db: Session, *, days: int = 14, today: date | None = None, user_id: int | None = None) -> list[dict]:
    """Tổng theo ngày `days` ngày gần nhất (đủ mọi ngày, ngày không có lượt = 0), tách theo trạng thái. Cộng cả bảng chi
    tiết lẫn bảng đếm đã gom — kỳ dài hơn hạn giữ vẫn đúng số."""
    today = today or date.today()
    d_from = today - timedelta(days=days - 1)
    out = {d_from + timedelta(days=i): {int(s): 0 for s in CallStatus} for i in range(days)}
    day_expr = func.date(AgentMcpCall.created_at)
    detail = db.execute(_filtered(select(day_expr, AgentMcpCall.status, func.count(AgentMcpCall.id)), user_id=user_id,
                                  d_from=d_from, d_to=today).group_by(day_expr, AgentMcpCall.status)).all()
    rolled = db.execute(_filtered(select(AgentMcpCallDaily.day, AgentMcpCallDaily.status,
                                         func.sum(AgentMcpCallDaily.calls)), user_id=user_id, d_from=d_from, d_to=today,
                                  model=AgentMcpCallDaily).group_by(AgentMcpCallDaily.day, AgentMcpCallDaily.status)).all()
    for d, status, n in [*detail, *rolled]:
        bucket = out.get(_as_date(d))
        if bucket is not None and int(status) in bucket:
            bucket[int(status)] += int(n or 0)
    return [{"day": d.isoformat(), "total": sum(v.values()), "ok": v[CallStatus.OK], "denied": v[CallStatus.DENIED],
             "error": v[CallStatus.ERROR]} for d, v in sorted(out.items())]


def top(db: Session, *, by: str = "tool", days: int = 14, limit: int = 10, today: date | None = None,
        user_id: int | None = None) -> list[dict]:
    """Top công cụ (`by=tool`, chỉ lượt tools/call) hoặc top người gọi (`by=user`) trong `days` ngày gần nhất."""
    today = today or date.today()
    d_from = today - timedelta(days=days - 1)
    col = AgentMcpCall.tool if by == "tool" else AgentMcpCall.user_id
    col_daily = AgentMcpCallDaily.tool if by == "tool" else AgentMcpCallDaily.user_id
    totals: dict = {}
    q1 = _filtered(select(col, func.count(AgentMcpCall.id)), user_id=user_id, d_from=d_from, d_to=today)
    q2 = _filtered(select(col_daily, func.sum(AgentMcpCallDaily.calls)), user_id=user_id, d_from=d_from, d_to=today,
                   model=AgentMcpCallDaily)
    if by == "tool":
        q1, q2 = q1.where(AgentMcpCall.tool != ""), q2.where(AgentMcpCallDaily.tool != "")
    else:
        q1, q2 = q1.where(AgentMcpCall.user_id != 0), q2.where(AgentMcpCallDaily.user_id != 0)
    for k, n in [*db.execute(q1.group_by(col)).all(), *db.execute(q2.group_by(col_daily)).all()]:
        totals[k] = totals.get(k, 0) + int(n or 0)
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], str(kv[0])))[:limit]
    return [{"key": k, "calls": n} for k, n in ranked]
