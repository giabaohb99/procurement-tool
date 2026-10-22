"""Đề xuất kế hoạch do AI soạn, chờ người duyệt (kh-AI1-3, doc/erp/tai-lieu-ai/22 §5.2) — DB ERP.

AI chỉ đề xuất, người quyết: `plan_ai` là bản AI soạn, KHÔNG BAO GIỜ sửa sau khi lưu; người sửa thì ghi `plan_final`;
duyệt mới dựng bảng Dự án (`list_id`). Giữ cả hai bản + `diff` để vòng học (đợt A3) so ước lượng với thực tế.
"""
from datetime import date, datetime

from sqlalchemy import JSON, BigInteger, Date, DateTime, Index, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class AiPlanProposal(Base, AuditMixin):
    __tablename__ = "tab_ai_plan_proposal"
    __table_args__ = (Index("ix_ai_plan_owner_status", "owner_user_id", "status"),)

    status: Mapped[int] = mapped_column(SmallInteger, default=1)                  # ai_plan_codes.AiPlanStatus
    owner_user_id: Mapped[int] = mapped_column(BigInteger, default=0)             # người hỏi AI = người duyệt (A1 22/10)
    owner_employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)             # phòng của chủ lúc lập — để lọc
    channel: Mapped[int] = mapped_column(SmallInteger, default=0)                 # logging_codes.AI_CHANNEL_*
    title: Mapped[str] = mapped_column(String(200), default="")
    goal: Mapped[str] = mapped_column(Text, default="")
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    plan_ai: Mapped[dict] = mapped_column(JSON, default=dict)
    plan_final: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    diff: Mapped[dict | None] = mapped_column(JSON, nullable=True)               # khác nhau AI ↔ người, tính lúc duyệt
    list_id: Mapped[int] = mapped_column(BigInteger, default=0)                   # bảng Dự án tạo ra (0 = chưa)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decided_by: Mapped[int] = mapped_column(BigInteger, default=0)
    reject_reason: Mapped[str] = mapped_column(String(500), default="")
