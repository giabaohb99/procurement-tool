"""Nguồn của nhóm chỉ số 3.8 "Dùng AI" (duoc-CR-655, D0d) — đúng 3 truy vấn SELECT cố định (+1 lần kiểm bảng tồn tại), KHÔNG phụ thuộc số người.

(1) `tab_ai_usage_daily` (ai-CR-230) trong cửa sổ — số đếm theo người × ngày × kênh, không có nội dung câu hỏi.
(2) mốc bắt đầu thu = ngày sớm nhất của bảng đó — phân biệt "chưa thu" (không ghi 0) với "thu rồi mà người này không dùng".
(3) `tab_audit_log` các dòng LẬP phiếu có `ai_channel > 0` (AI làm hộ) — nguồn chính xác nhất cho "phiếu do AI soạn",
    đúng hơn `tab_assistant_change` vì mang kênh thật (MCP không bị ghi nhầm thành Telegram).
Bảng chưa tồn tại (ERP cũ chưa chạy migration `aiusage01`) → coi như chưa thu thập.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.modules.audit.model import AuditLog
from app.modules.ai_usage.model import AiUsageDaily

from .daily_docs import TRACKED_DOC_ENTITIES

if TYPE_CHECKING:   # tránh vòng import: `Window` nằm ở snapshot_sources, chính nó gọi tệp này
    from .snapshot_sources import Window


@dataclass
class AiSources:
    since: date | None = None   # ngày sớm nhất có số dùng AI (None = chưa từng thu)
    # (user_id, day, channel, turns, tool_calls, denied, drafts_confirmed, clients, tool_groups)
    usage: list = field(default_factory=list)
    drafted: dict = field(default_factory=dict)   # user_id -> số phiếu khác nhau do AI lập (entity, entity_id)

    def collecting(self, window: "Window") -> bool:
        return self.since is not None and self.since < window.hi


def load_ai_sources(db: Session, w: "Window") -> AiSources:
    s = AiSources()
    if not inspect(db.get_bind()).has_table(AiUsageDaily.__tablename__):
        return s
    U = AiUsageDaily
    s.since = db.execute(select(func.min(U.day))).scalar()
    s.usage = [tuple(r) for r in db.execute(
        select(U.user_id, U.day, U.channel, U.turns, U.tool_calls, U.denied, U.drafts_confirmed, U.clients,
               U.tool_groups).where(U.day >= w.lo, U.day < w.hi)).all()]
    docs: dict[int, set] = {}
    for uid, entity, entity_id in db.execute(
            select(AuditLog.created_by, AuditLog.entity, AuditLog.entity_id)
            .where(AuditLog.ai_channel > 0, AuditLog.action == "create", AuditLog.entity.in_(TRACKED_DOC_ENTITIES),
                   AuditLog.created_at >= w.utc_lo, AuditLog.created_at < w.utc_hi)).all():
        docs.setdefault(uid, set()).add((entity, entity_id))
    s.drafted = {uid: len(v) for uid, v in docs.items()}
    return s
