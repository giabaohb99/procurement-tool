from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.core.base_model import Base, AuditMixin


class Notification(Base, AuditMixin):
    """In-app notifications."""
    __tablename__ = "tab_notification"
    __table_args__ = (Index("ix_tab_notification_created_at", "created_at"),)   # duoc-CR-641

    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    link: Mapped[str] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    #  duoc-CR-641: mốc đánh dấu đã đọc (chỉ từ ngày deploy, không bù) — đo "gửi → đọc mất bao lâu".
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


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

    #  NỘI DUNG THƯ + GỬI LẠI (bao-CR-727, 04/11/2026). Thư ghi trước đợt này để NULL — không bù được, nút
    #  "Gửi lại" trên màn Nhật ký email tắt kèm lý do. Chỉ ghi qua `keep_body`: thư mang liên kết đặt mật khẩu
    #  KHÔNG BAO GIỜ được lưu (ai đọc được nhật ký là chiếm được tài khoản người nhận).
    html_body: Mapped[str | None] = mapped_column(Text().with_variant(MEDIUMTEXT(), "mysql"), nullable=True)
    #  Dòng này là bản gửi lại của dòng nào (id dòng đã bấm Gửi lại). Rỗng = thư gốc của nghiệp vụ.
    resent_from_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)

    def keep_body(self, html_body: str | None) -> None:
        """Ghi nội dung thư để gửi lại được — trừ thư nhạy cảm và thư quá to (xem `can_keep_body`)."""
        if html_body and can_keep_body(self.event, html_body):
            self.html_body = html_body


#  Sự kiện chứa liên kết đặt mật khẩu / thông tin đăng nhập: KHÔNG lưu nội dung, KHÔNG gửi lại (bao-CR-727,
#  yêu cầu bảo mật). Thêm thư mới có mật khẩu tạm hay liên kết đăng nhập một lần thì khai vào đây.
SECRET_EMAIL_EVENTS = frozenset({"password_reset", "account_creation"})
#  Trần nội dung lưu (ký tự). Thư của hệ chỉ vài KB; quá trần là thư bất thường, không lưu cho đỡ phình bảng.
MAX_KEPT_BODY_CHARS = 1_000_000


def is_secret_email_event(event: str | None) -> bool:
    """Thư có liên kết đặt mật khẩu / thông tin đăng nhập — kể cả bản gửi thử `<sự kiện>_test`."""
    code = (event or "").strip()
    if code.endswith("_test"):
        code = code[: -len("_test")]
    return code in SECRET_EMAIL_EVENTS


def can_keep_body(event: str | None, html_body: str | None) -> bool:
    return bool(html_body) and not is_secret_email_event(event) and len(html_body) <= MAX_KEPT_BODY_CHARS
