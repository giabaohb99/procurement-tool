"""Nhóm chỉ số 3.8 «Dùng AI» của MỘT người (thuần, duoc-CR-655, D0d). Chỉ SỐ và MÃ — không nội dung câu hỏi.

Chưa thu (bảng AI trống / chưa tồn tại / mốc thu sau cửa sổ) → mọi khóa `NOT_COLLECTED`, KHÔNG ghi 0. Đã thu mà người này
không dùng → 0 (đo được thật). Giá trị MÃ (kênh chính, ứng dụng AI, nhóm công cụ) đi vào `lists`, không thành khóa số: trung vị
của một mã kênh vô nghĩa nên không đưa qua thống kê nhóm so sánh.
"""
from collections import Counter

from app.core.ai_usage_codes import ai_client_code
from app.core.logging_codes import AI_CHANNEL_MCP, AI_CHANNEL_WEB
from app.core.usage_codes import UnmeasuredReason as Why

from .metric_partial import Partial
from .metric_stats import ratio
from .snapshot_sources import SnapshotSources

MAX_TOOL_GROUPS = 20
AI_KEYS = ("ai_uses", "ai_active_days", "ai_mcp_share", "ai_tool_groups_used", "ai_denied", "ai_drafts_confirmed",
           "ai_docs_drafted", "ai_docs_share")


def ai_metrics(src: SnapshotSources, uid: int, usage_rows: list, docs_created: float | int | None) -> Partial:
    """`usage_rows` = dòng `tab_ai_usage_daily` của người này trong cửa sổ (đã lọc theo `uid` ở bên gọi)."""
    p = Partial()
    if not src.ai.collecting(src.window):
        for key in AI_KEYS:
            p.put(key, None, Why.NOT_COLLECTED)
        return p
    channels: Counter = Counter()
    clients: Counter = Counter()
    groups: Counter = Counter()
    days, denied, confirmed = set(), 0, 0
    for _uid, day, channel, turns, tool_calls, den, conf, cli, grp in usage_rows:
        channels[channel] += turns or 0
        denied += den or 0
        confirmed += conf or 0
        if (turns or 0) + (tool_calls or 0) > 0:
            days.add(day)
        for name, n in (cli or {}).items():
            clients[ai_client_code(name)] += n
        for name, n in (grp or {}).items():
            groups[name] += n
    uses = sum(channels.values())
    drafted = src.ai.drafted.get(uid, 0)
    p.put("ai_uses", uses)
    p.put("ai_active_days", len(days))
    p.put("ai_mcp_share", ratio(channels.get(AI_CHANNEL_MCP, 0), uses))
    p.put("ai_tool_groups_used", len(groups))
    p.put("ai_denied", denied)
    p.put("ai_drafts_confirmed", confirmed)
    p.put("ai_docs_drafted", drafted)
    p.put("ai_docs_share", min(1.0, drafted / docs_created) if docs_created else None)
    #  Danh sách mã cho khối «Dùng AI» trên hồ sơ — {kênh: lượt}, {mã ứng dụng: lượt}, [[nhóm công cụ, lượt]].
    p.lists["ai_channels"] = {str(k): v for k, v in channels.items() if v}
    p.lists["ai_clients"] = {str(k): v for k, v in clients.items() if v}
    p.lists["ai_tool_groups"] = [[k, v] for k, v in groups.most_common(MAX_TOOL_GROUPS)]
    #  Số câu hỏi Trợ lý web: nguồn cũ (tin nhắn trong DB ERP) gần như về 0 từ khi hội thoại sang DB agent_hub → lấy số lớn hơn.
    p.put("assistant_questions", max(src.assistant_q.get(uid, 0), channels.get(AI_CHANNEL_WEB, 0)))
    return p
