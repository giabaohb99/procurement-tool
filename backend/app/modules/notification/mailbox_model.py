"""HỘP THƯ GỬI — gửi thông báo ban hành DANH NGHĨA MỘT ĐỊA CHỈ KHÁC (26/08/2026).

Ca nghiệp vụ dựng nên bảng này: nhân sự hành chính đăng nhập bằng tài khoản của
chính mình (`nhanvien@gmail.com`) nhưng phải ban hành *Thông báo nghỉ lễ* cho
toàn công ty **danh nghĩa `hr@gmail.com`** — người nhận mở hộp thư ra phải thấy
thư đến từ phòng Hành chính, không phải từ một cá nhân.

Trước đó cả hệ chỉ có MỘT tài khoản SMTP dùng chung và mọi thư đều mang
`From: smtp_from`, nên không có cách nào diễn đạt chuyện này.

**Mỗi hộp thư giữ bộ SMTP riêng của nó**, không chỉ đổi dòng `From`. Lý do rất
thực tế: Gmail **ghi đè** `From` về đúng tài khoản đã đăng nhập trừ khi địa chỉ
kia đã khai *Send mail as* trong chính hộp thư đó. Chỉ đổi tiêu đề thư thì người
nhận vẫn thấy địa chỉ cũ — tính năng coi như không chạy, mà lại chạy im lặng.

Mật khẩu ứng dụng **mã hóa bằng Fernet** dùng lại đúng khóa của `app_settings`
(suy từ `JWT_SECRET`), và API **không bao giờ trả ngược giá trị** — chỉ trả cờ
"đã cấu hình hay chưa", cùng quy ước với `smtp_password` ở màn Cấu hình hệ thống.

Ai được dùng hộp thư nào thì khai ĐÍCH DANH ở `tab_mailbox_member`. Cố ý không
suy theo phòng ban hay vai trò: quyền gửi thư danh nghĩa cả công ty là thứ phải
chỉ mặt đặt tên từng người, và phải kiểm toán được "ai đã từng gửi thay ai".
"""
from sqlalchemy import (BigInteger, Boolean, Index, Integer, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class Mailbox(Base, AuditMixin):
    """Một địa chỉ gửi đi, kèm đường SMTP của chính nó."""

    __tablename__ = "tab_mailbox"
    __table_args__ = (
        #  Màn chọn lúc ban hành luôn lọc "còn dùng" và thường lọc theo pháp nhân.
        Index("ix_mailbox_active", "is_active", "company_id"),
    )

    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    #  Địa chỉ hiện trên dòng «Từ». Duy nhất — hai dòng cùng địa chỉ mà khác mật
    #  khẩu thì không ai biết dòng nào đang thật sự gửi được.
    email: Mapped[str] = mapped_column(String(255), unique=True)
    #  Tên hiện trước địa chỉ: «Phòng Hành chính <hr@gmail.com>». Rỗng thì dùng `name`.
    display_name: Mapped[str] = mapped_column(String(200), default="")

    smtp_host: Mapped[str] = mapped_column(String(200), default="")
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_user: Mapped[str] = mapped_column(String(255), default="")
    #  Fernet, KHÔNG trả ngược qua API. Xem `mailbox_service.dat_mat_khau`.
    smtp_password_enc: Mapped[str] = mapped_column(Text, default="")
    use_tls: Mapped[bool] = mapped_column(Boolean, default=True)

    #  Giới hạn hộp thư trong một pháp nhân. Rỗng = dùng được ở mọi pháp nhân
    #  (hộp thư cấp Tập đoàn). Đây là bộ LỌC hiển thị, không phải chốt quyền —
    #  chốt quyền nằm ở `tab_mailbox_member`.
    company_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)

    note: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class MailboxMember(Base, AuditMixin):
    """Nhân sự nào được gửi danh nghĩa hộp thư này.

    Khai đích danh từng người. Bảng này chính là câu trả lời cho *"vì sao
    nhanvien@gmail.com gửi được thư của hr@gmail.com"* khi có ai đó hỏi lại sáu
    tháng sau.
    """

    __tablename__ = "tab_mailbox_member"
    __table_args__ = (
        UniqueConstraint("mailbox_id", "employee_id", name="uq_mailbox_member"),
    )

    mailbox_id: Mapped[int] = mapped_column(BigInteger, index=True)
    employee_id: Mapped[int] = mapped_column(BigInteger, index=True)
