"""NƠI NHẬN và XÁC NHẬN ĐÃ ĐỌC — bảng **cố ý để rỗng** ở bản 1 (J06, J07).

Phase 1 yêu cầu dựng sẵn bảng, màn hình để phase sau (`02` mục 5: *"chỉ bảng,
chưa màn hình"*). Không có service, không có router — chưa dòng nào ghi vào đây.

Hai điểm thiết kế đã chốt ở `04` mục 7.1, đừng đổi lại:

1. **Gắn vào PHIÊN BẢN, không gắn vào văn bản.** Quy chế lên bản 2.0 thì mọi
   người phải xác nhận lại. Gắn vào `document_id` thì người đã xác nhận bản 1.0
   vẫn hiện là "đã đọc" trong khi họ chưa từng đọc nội dung mới.
2. **Một người nhận = MỘT dòng, gửi mấy kênh thì cộng vào `channels`.** Bản 1.0
   tách `tab_distribution` (gửi cho ai) và `tab_read_receipt` (ai đã đọc) thành
   hai bảng; gộp lại vì cùng một hạt dữ liệu, và vì câu hỏi hay gặp nhất của văn
   thư — *"gửi 240 người, bao nhiêu người đã đọc, ai chưa"* — nối hai bảng thì
   phải nối bằng cặp khóa không khớp hẳn nhau.

Quan hệ với `tab_email_log` đang có bên Thu mua: bảng này ghi **đã định gửi cho
ai và người đó đọc chưa**; `tab_email_log` ghi **lần gửi thư đó ra sao**.
`send_status` ở đây là kết quả gần nhất, chi tiết vì sao lỗi thì tra sang đó.
"""
from datetime import date, datetime

from sqlalchemy import (BigInteger, Boolean, Date, DateTime, Index,
                        SmallInteger, String, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

RECIPIENT_EMPLOYEE = 1    # một nhân sự đích danh
RECIPIENT_DEPARTMENT = 2  # cả phòng ban
RECIPIENT_COMPANY = 3     # cả pháp nhân
RECIPIENT_EXTERNAL = 4    # đơn vị bên ngoài — đọc `external_party_id`

#  Kênh gửi là TẬP HỢP cộng dồn, không phải mỗi kênh một dòng: gửi cả chuông lẫn
#  thư thì ghi 3. Mỗi kênh một dòng thì ràng buộc duy nhất bên dưới vỡ ngay, kéo
#  theo việc đếm "bao nhiêu người đã đọc" đếm trùng.
CHANNEL_BELL = 1
CHANNEL_EMAIL = 2
CHANNEL_PAPER = 4
CHANNEL_EXTERNAL = 8

SEND_PENDING = 1
SEND_SENT = 2
SEND_FAILED = 3


class DocumentRecipient(Base, AuditMixin):
    __tablename__ = "tab_document_recipient"
    __table_args__ = (
        #  Một người nhận chỉ có một dòng trên mỗi phiên bản.
        UniqueConstraint(
            "version_id", "recipient_kind", "recipient_id", name="uq_document_recipient",
        ),
        #  Màn "văn bản tôi phải xác nhận" tra ngược từ người nhận.
        Index("ix_document_recipient_person", "recipient_kind", "recipient_id", "confirmed_at"),
        Index("ix_document_recipient_doc", "document_id", "version_id"),
    )

    #  Giữ cả hai: `version_id` là hạt dữ liệu thật, `document_id` để đếm theo
    #  văn bản mà không phải nối bảng phiên bản.
    document_id: Mapped[int] = mapped_column(BigInteger)
    version_id: Mapped[int] = mapped_column(BigInteger)

    recipient_kind: Mapped[int] = mapped_column(SmallInteger, default=RECIPIENT_EMPLOYEE)
    #  Id nhân sự / phòng ban / pháp nhân tùy `recipient_kind`. Để 0 khi gửi ra
    #  ngoài — lúc đó đọc `external_party_id`.
    recipient_id: Mapped[int] = mapped_column(BigInteger, default=0)
    external_party_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    channels: Mapped[int] = mapped_column(SmallInteger, default=CHANNEL_BELL)
    send_status: Mapped[int] = mapped_column(SmallInteger, default=SEND_PENDING)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error: Mapped[str] = mapped_column(String(500), default="")

    #  Bắt buộc bấm xác nhận, hay chỉ cần nhận thông báo.
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    #  Lần MỞ đầu tiên — khác với lúc bấm nút xác nhận. Tách hai cột vì "đã mở
    #  ra xem" và "đã cam kết là đọc rồi" là hai sự thật khác nhau.
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    #  IPv6 dài nhất 45 ký tự.
    ip: Mapped[str] = mapped_column(String(45), default="")
