"""Model lịch sử hội thoại Trợ lý AI (Phase 1).

Module MỚI -> cột kiểu/loại lưu SMALLINT theo IntEnum (R2/QĐ-11), không lưu chữ.
Mỗi hội thoại thuộc về MỘT tài khoản (created_by); danh sách/chi tiết lọc theo chính chủ.
"""
from datetime import datetime
from enum import IntEnum

from sqlalchemy import BigInteger, DateTime, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class MessageRole(IntEnum):
    """Vai trò của một lượt tin. Không lưu 'user'/'assistant' dạng chữ."""

    USER = 1
    ASSISTANT = 2


class AssistantConversation(Base, AuditMixin):
    """Một cuộc hội thoại với trợ lý. created_by = tài khoản chủ hội thoại."""

    __tablename__ = "tab_assistant_conversation"

    title: Mapped[str] = mapped_column(String(255), default="")
    # Nhà cung cấp + model dùng cho lượt gần nhất (để hiển thị lại, không ràng buộc lượt sau).
    provider: Mapped[str] = mapped_column(String(30), default="")
    model: Mapped[str] = mapped_column(String(80), default="")
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)


class AssistantMessage(Base, AuditMixin):
    """Một lượt tin trong hội thoại. role = MessageRole (SMALLINT)."""

    __tablename__ = "tab_assistant_message"

    conversation_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    role: Mapped[int] = mapped_column(SmallInteger, default=MessageRole.USER)  # MessageRole
    content: Mapped[str] = mapped_column(Text, default="")
    # Thông tin lượt gọi model (chỉ có ở tin của trợ lý) — để soi chi phí, không bắt buộc.
    provider: Mapped[str] = mapped_column(String(30), default="")
    model: Mapped[str] = mapped_column(String(80), default="")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    thinking_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(Integer, default=0)
