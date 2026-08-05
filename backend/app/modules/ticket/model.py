from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class Ticket(Base, AuditMixin):
    """Phiếu hỗ trợ nội bộ. Mọi nhân viên đăng nhập đều mở được; nhóm 'Hỗ trợ' xử lý tập trung.

    created_by = tài khoản người gửi (dùng cho phạm vi 'own').
    assignee_id = tài khoản người xử lý (tùy chọn, nhóm hỗ trợ nhận việc).
    """

    __tablename__ = "tab_ticket"

    code: Mapped[str] = mapped_column(String(50), unique=True, default="")
    subject: Mapped[str] = mapped_column(String(255), default="")
    department: Mapped[str] = mapped_column(String(255), default="", index=True)  # nhóm/bộ phận (nhãn)
    priority: Mapped[str] = mapped_column(String(20), default="normal", index=True)  # low|normal|high|urgent
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)  # open|in_progress|answered|closed
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    requester_id: Mapped[int] = mapped_column(BigInteger, default=0)  # id nhân sự người gửi (hiển thị)
    assignee_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)  # tài khoản người xử lý
    origin_url: Mapped[str] = mapped_column(String(500), default="")  # trang người gửi đang đứng lúc tạo (debug)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class TicketMessage(Base, AuditMixin):
    """Một tin nhắn trong luồng trao đổi của phiếu hỗ trợ.

    created_by = tài khoản người viết. is_staff = do nhóm hỗ trợ viết (True) hay người gửi (False).
    """

    __tablename__ = "tab_ticket_message"

    ticket_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    body: Mapped[str] = mapped_column(Text, default="")
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
