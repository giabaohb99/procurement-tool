"""Số dùng AI theo người × ngày × kênh (ai-CR-230, doc/erp/22 §5) — bảng ĐÍCH phía ERP.

Dịch vụ AI (DB `agent_hub` khi chạy tách) gom số đếm mỗi đêm rồi đẩy sang đây qua cổng B `POST /api/agent-gw/ai-usage`
(chế độ nhúng ghi thẳng), để bộ chỉ số hồ sơ cách làm việc (`modules/usage_profile`) đọc như các nguồn khác. CHỈ số đếm
+ mã, KHÔNG có nội dung câu hỏi hay câu trả lời. Ghi lại được: gom lại một ngày thì dòng (ngày, người, kênh) bị thay.
Bảng hệ thống ghi, không dùng `AuditMixin` (cùng tiền lệ `tab_usage_daily`).
"""
from datetime import date, datetime

from sqlalchemy import JSON, BigInteger, Date, DateTime, Integer, SmallInteger, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base


class AiUsageDaily(Base):
    __tablename__ = "tab_ai_usage_daily"
    __table_args__ = (UniqueConstraint("day", "user_id", "channel", name="uq_ai_usage_daily_day_user_channel"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    day: Mapped[date] = mapped_column(Date, index=True)                       # ngày theo giờ Việt Nam
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)   # ERP điền lúc nhận (0 = không có hồ sơ)
    channel: Mapped[int] = mapped_column(SmallInteger)                        # logging_codes.AI_CHANNEL_* (1..4)
    turns: Mapped[int] = mapped_column(Integer, default=0)                    # số câu hỏi (web / bot) · số lượt gọi công cụ (MCP)
    tool_calls: Mapped[int] = mapped_column(Integer, default=0)
    denied: Mapped[int] = mapped_column(Integer, default=0)                   # lượt công cụ bị từ chối quyền
    errors: Mapped[int] = mapped_column(Integer, default=0)
    drafts_created: Mapped[int] = mapped_column(Integer, default=0)           # gọi công cụ draft_*
    drafts_confirmed: Mapped[int] = mapped_column(Integer, default=0)         # commit_draft / confirm_draft thành công
    clients: Mapped[dict] = mapped_column(JSON, default=dict)                 # {tên ứng dụng: số lượt} — chỉ kênh MCP
    tool_groups: Mapped[dict] = mapped_column(JSON, default=dict)                # {mã nhóm công cụ: số lượt} — mcp_settings.GROUPS
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
