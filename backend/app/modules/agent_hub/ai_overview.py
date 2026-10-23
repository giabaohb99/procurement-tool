"""Số liệu màn TỔNG QUAN Kho skill AI / cổng MCP (ai-CR-213, K6 doc/erp/21 §6.2 G1) — dựng từ nhật ký `tab_agent_mcp_call`
+ bảng khóa `tab_agent_mcp_key` (DB dịch vụ AI) + số bộ / skill đang dùng hỏi ERP qua cổng B.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import mcp_keys, mcp_log
from .model import AgentMcpCall, AgentMcpKey

log = logging.getLogger("app.agent_hub.ai_overview")
CONNECTED_DAYS = 30
EXPIRING_DAYS = 7
TOP_N = 5


def _count(db: Session, since: datetime, until: datetime, status: int | None = None, method: str = "") -> int:
    q = select(func.count(AgentMcpCall.id)).where(AgentMcpCall.created_at >= since, AgentMcpCall.created_at < until)
    if status is not None:
        q = q.where(AgentMcpCall.status == status)
    if method:
        q = q.where(AgentMcpCall.method == method)
    return int(db.scalar(q) or 0)


def build(db: Session, *, now: datetime | None = None, labels=None) -> dict:
    """`labels(db, ids) -> {id: nhãn}` để gắn tên người (controller truyền `_user_labels`)."""
    from . import erp

    now = now or datetime.now()
    week, prev = now - timedelta(days=7), now - timedelta(days=14)
    calls_7, calls_prev = _count(db, week, now), _count(db, prev, week)
    denied_7 = _count(db, week, now, mcp_log.CallStatus.DENIED)
    error_7 = _count(db, week, now, mcp_log.CallStatus.ERROR)

    keys = list(db.scalars(select(AgentMcpKey)))
    by_state = {int(s): 0 for s in mcp_keys.KeyState}
    for k in keys:
        by_state[int(mcp_keys.state_of(k, now))] += 1
    active_ids = {k.id for k in keys if mcp_keys.state_of(k, now) == mcp_keys.KeyState.ACTIVE}
    connected = 0
    if active_ids:
        connected = int(db.scalar(select(func.count(func.distinct(AgentMcpCall.user_id))).where(
            AgentMcpCall.key_id.in_(active_ids), AgentMcpCall.created_at >= now - timedelta(days=CONNECTED_DAYS),
            AgentMcpCall.user_id != 0)) or 0)
    expiring = sorted((k for k in keys if mcp_keys.state_of(k, now) in (mcp_keys.KeyState.ACTIVE, mcp_keys.KeyState.PENDING)
                       and k.expires_at is not None and k.expires_at <= now + timedelta(days=EXPIRING_DAYS)),
                      key=lambda k: k.expires_at)

    top_users = mcp_log.top(db, by="user", days=7, limit=TOP_N, today=now.date())
    names = labels(db, [u["key"] for u in top_users] + [k.user_id for k in expiring]) if labels else {}
    skill_rows = db.execute(select(AgentMcpCall.skill_id, func.count(AgentMcpCall.id))
                            .where(AgentMcpCall.skill_id != 0, AgentMcpCall.created_at >= week)
                            .group_by(AgentMcpCall.skill_id).order_by(func.count(AgentMcpCall.id).desc()).limit(TOP_N)).all()
    try:
        skills = erp.skill_stats(db)
    except Exception:  # noqa: BLE001 — ERP chưa trả lời thì màn vẫn hiện phần còn lại
        log.warning("ai_overview: không lấy được số skill từ ERP", exc_info=True)
        skills = None
    from . import service_health

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "service_health": service_health.snapshot(),         # kh-AI2-4: lỗi 5xx 24 giờ + hàng đợi việc nền
        "skills": skills,                                  # {skill_sets, skills} hoặc None khi ERP lỗi
        "connected_users": connected, "connected_days": CONNECTED_DAYS,
        "calls_7d": calls_7, "calls_prev_7d": calls_prev,
        #  ai-CR-219: chỉ lượt gọi công cụ (tools/call) — thẻ «Lượt gọi 7 ngày» khỏi lệch với «Công cụ dùng nhiều».
        "tool_calls_7d": _count(db, week, now, method="tools/call"),
        "tool_calls_prev_7d": _count(db, prev, week, method="tools/call"),
        "calls_change_pct": round((calls_7 - calls_prev) / calls_prev * 100, 1) if calls_prev else None,
        "denied_7d": denied_7, "error_7d": error_7,
        "daily": mcp_log.daily_totals(db, days=14, today=now.date()),
        "top_tools": mcp_log.top(db, by="tool", days=7, limit=TOP_N, today=now.date()),
        "top_users": [{**u, "label": names.get(u["key"], "")} for u in top_users],
        "top_skills": [{"skill_id": int(sid), "calls": int(n)} for sid, n in skill_rows],
        "keys_by_state": [{"state": s, "label": mcp_keys.STATE_LABELS[mcp_keys.KeyState(s)], "count": n}
                          for s, n in by_state.items()],
        "expiring_keys": [{"key_id": k.id, "user_id": k.user_id, "owner_label": names.get(k.user_id, ""), "name": k.name,
                           "expires_at": k.expires_at.isoformat(timespec="seconds"),
                           "state": int(mcp_keys.state_of(k, now))} for k in expiring[:50]],
        "expiring_days": EXPIRING_DAYS,
    }
