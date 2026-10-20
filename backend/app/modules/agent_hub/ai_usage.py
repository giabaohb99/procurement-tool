"""Gom số DÙNG AI theo người × ngày × kênh rồi đẩy sang ERP (ai-CR-230, doc/erp/22 §5).

Nguồn (đều ở DB của dịch vụ AI — `agent_hub` khi chạy tách):
  - `tab_agent_intent` (sổ ý định): mỗi câu hỏi Trợ lý web (kênh 1) và bot Telegram / Zalo (kênh 2 / 4) một dòng, có tên
    công cụ đã gọi, số lượt gọi, số lượt bị từ chối, kết cục;
  - `tab_agent_mcp_call` (nhật ký cổng MCP): mỗi lượt `tools/call` của ứng dụng AI ngoài (kênh 3), có tên ứng dụng.
Chỉ số đếm + mã, KHÔNG chuyển nội dung câu hỏi. Ngày tính theo giờ Việt Nam; cột thời gian của sổ là UTC.
Đẩy qua `agent_hub.erp.push_ai_usage` (cổng B khi tách, ghi thẳng khi nhúng) — gom lại một ngày bao nhiêu lần cũng được.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging_codes import AI_CHANNEL_MCP, AI_CHANNEL_TELEGRAM, AI_CHANNEL_WEB, AI_CHANNEL_ZALO

from .model import AgentIntent, AgentMcpCall
from .timeutil import LOCAL_OFFSET

#  Sổ ý định → kênh AI (sổ dùng mã riêng: 1 web · 2 Telegram · 3 Zalo).
LEDGER_CHANNEL = {1: AI_CHANNEL_WEB, 2: AI_CHANNEL_TELEGRAM, 3: AI_CHANNEL_ZALO}
CONFIRM_TOOLS = frozenset({"commit_draft", "confirm_draft", "create_events_from_file"})
OTHER_GROUP = "khac"
MAX_BACKFILL_DAYS = 90


def _bounds(day: date) -> tuple[datetime, datetime]:
    """[đầu ngày, đầu ngày sau) theo giờ Việt Nam, đổi ra UTC để so với cột của sổ."""
    start = datetime.combine(day, datetime.min.time()) - LOCAL_OFFSET
    return start, start + timedelta(days=1)


def _group(tool: str) -> str:
    from .mcp_settings import GROUP_OF

    g = GROUP_OF.get(tool)
    return g.key if g is not None else OTHER_GROUP


def _blank() -> dict:
    return {"turns": 0, "tool_calls": 0, "denied": 0, "errors": 0, "drafts_created": 0, "drafts_confirmed": 0,
            "clients": Counter(), "tool_groups": Counter()}


def collect(db: Session, day: date) -> list[dict]:
    """Các dòng số của MỘT ngày (giờ Việt Nam)."""
    from .intent_ledger import Outcome
    from .mcp_log import CallStatus

    start, end = _bounds(day)
    acc: dict[tuple[int, int], dict] = defaultdict(_blank)
    for r in db.scalars(select(AgentIntent).where(AgentIntent.created_at >= start, AgentIntent.created_at < end,
                                                  AgentIntent.user_id > 0)):
        channel = LEDGER_CHANNEL.get(int(r.channel or 0))
        if channel is None:
            continue
        a = acc[(int(r.user_id), channel)]
        tools = [str(t) for t in (r.tools or [])]
        a["turns"] += 1
        a["tool_calls"] += int(r.tool_calls_n or 0) or len(tools)
        a["denied"] += int(r.denied_n or 0)
        a["errors"] += 1 if int(r.outcome or 0) == int(Outcome.ERROR) else 0
        a["drafts_created"] += sum(1 for t in tools if t.startswith("draft_"))
        a["drafts_confirmed"] += sum(1 for t in tools if t in CONFIRM_TOOLS)
        for t in tools:
            a["tool_groups"][_group(t)] += 1
    for r in db.scalars(select(AgentMcpCall).where(AgentMcpCall.created_at >= start, AgentMcpCall.created_at < end,
                                                   AgentMcpCall.method == "tools/call", AgentMcpCall.user_id > 0)):
        a = acc[(int(r.user_id), AI_CHANNEL_MCP)]
        tool = str(r.tool or "")
        status = int(r.status or 0)
        a["turns"] += 1
        a["tool_calls"] += 1
        a["denied"] += 1 if status == int(CallStatus.DENIED) else 0
        a["errors"] += 1 if status == int(CallStatus.ERROR) else 0
        a["drafts_created"] += 1 if tool.startswith("draft_") else 0
        a["drafts_confirmed"] += 1 if tool in CONFIRM_TOOLS and status == int(CallStatus.OK) else 0
        a["clients"][(r.client_name or "Không rõ")[:100]] += 1
        if tool:
            a["tool_groups"][_group(tool)] += 1
    out = []
    for (user_id, channel), a in sorted(acc.items()):
        out.append({"day": day.isoformat(), "user_id": user_id, "channel": channel,
                    **{k: v for k, v in a.items() if k not in ("clients", "tool_groups")},
                    "clients": dict(a["clients"]), "tool_groups": dict(a["tool_groups"])})
    return out


def push_days(db: Session, days: int = 2, today: date | None = None) -> dict:
    """Gom + đẩy `days` ngày gần nhất TÍNH ĐẾN HÔM QUA (giờ VN). Mặc định 2 để lượt chạy đêm vá luôn ngày hôm kia nếu
    đêm trước ERP đang khởi động lại. Trả số dòng đã gửi / ghi."""
    from . import erp
    from .timeutil import now_local

    today = today or now_local().date()
    days = max(1, min(int(days or 1), MAX_BACKFILL_DAYS))
    sent = written = 0
    for i in range(days, 0, -1):
        day = today - timedelta(days=i)
        rows = collect(db, day)
        res = erp.push_ai_usage(db, rows)
        sent += len(rows)
        written += int((res or {}).get("written") or 0)
    return {"days": days, "rows_sent": sent, "rows_written": written}


__all__ = ["collect", "push_days", "LEDGER_CHANNEL", "CONFIRM_TOOLS"]
