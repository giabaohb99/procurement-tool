from sqlalchemy import BigInteger, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.core.base_model import Base, AuditMixin


class Notification(Base, AuditMixin):
    """In-app notifications."""
    __tablename__ = "tab_notification"

    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    link: Mapped[str] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class EmailLog(Base, AuditMixin):
    """Logs of sent emails."""
    __tablename__ = "tab_email_log"

    event: Mapped[str] = mapped_column(String(100))
    to_email: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / sent / failed
    error: Mapped[str] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    #  HỘP THƯ GỬI DANH NGHĨA (26/08/2026) — rỗng = gửi bằng SMTP dùng chung như
    #  trước. Ghi lại địa chỉ ĐÃ GỬI chứ không chỉ trỏ khóa ngoại: hộp thư đổi
    #  địa chỉ hay bị xóa về sau thì nhật ký vẫn phải trả lời được câu "thư này
    #  người nhận thấy nó đến từ đâu".
    mailbox_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)
    from_email: Mapped[str] = mapped_column(String(255), default="")
