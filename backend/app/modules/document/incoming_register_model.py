"""SỔ VĂN BẢN ĐẾN — bảng **cố ý để rỗng** ở bản 1 (S02).

Phase 1 dựng sẵn bảng, màn hình thuộc phase 9 (`02` mục 5, `04` mục 9.2).

**Vì sao không gom vào `tab_document` với `origin = 3`** — đã cân nhắc và bỏ.
Văn bản đến có vòng đời khác hẳn: không phiên bản, không duyệt, không phạm vi,
không ban hành; đổi lại có giao người xử lý và hạn xử lý. Gom vào nghĩa là nhét
bốn cột chết vào bảng nóng nhất của cả phân hệ. Hằng `ORIGIN_INCOMING = 3` vẫn
giữ ở `model.py` để sau này văn bản đến làm được đích của quan hệ "căn cứ theo".

**Vì sao có UNIQUE ở đây mà sổ văn bản ĐI thì không**: số đến dùng khóa
`in:{mã pháp nhân}:{năm}` — một sổ duy nhất cho cả pháp nhân, nên bộ ba
(pháp nhân × năm × số thứ tự) là duy nhất thật. Số đi đếm lại từ 1 theo TỪNG
loại văn bản, nên Thông báo số 8 và Quyết định số 8 cùng năm là chuyện bình
thường — ràng buộc tương tự đặt bên đó sẽ chặn đúng chuyện bình thường ấy. Vì
vậy sổ văn bản đi là một TRUY VẤN trên `tab_document`, không phải một bảng.
"""
from datetime import date, datetime

from sqlalchemy import (BigInteger, Date, DateTime, Index, Integer,
                        SmallInteger, String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

INCOMING_RECEIVED = 1   # mới nhận, chưa giao ai
INCOMING_ASSIGNED = 2   # đã giao người xử lý
INCOMING_HANDLED = 3    # đã xử lý xong
INCOMING_CLOSED = 4     # đóng, không cần xử lý

INCOMING_STATUS_LABELS = {
    INCOMING_RECEIVED: "Mới nhận",
    INCOMING_ASSIGNED: "Đã giao",
    INCOMING_HANDLED: "Đã xử lý",
    INCOMING_CLOSED: "Đóng",
}


class IncomingRegister(Base, AuditMixin):
    __tablename__ = "tab_incoming_register"
    __table_args__ = (
        UniqueConstraint("company_id", "year", "seq_no", name="uq_incoming_seq"),
        Index("ix_incoming_assignee", "assigned_employee_id", "status", "due_date"),
    )

    company_id: Mapped[int] = mapped_column(BigInteger)
    year: Mapped[int] = mapped_column(SmallInteger)
    #  Cấp qua `number_service.next_number()` với khóa `in:{mã pháp nhân}:{năm}`,
    #  không được lấy `MAX(seq_no) + 1`.
    seq_no: Mapped[int] = mapped_column(Integer)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    #  Bên gửi — trỏ `tab_external_party` (danh mục đối tác, A07).
    sender_party_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    #  Số hiệu và ngày ghi TRÊN BẢN GIẤY của bên gửi, không phải số ta cấp.
    sender_doc_number: Mapped[str] = mapped_column(String(100), default="")
    sender_doc_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    title: Mapped[str] = mapped_column(String(500), default="")
    file_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    assigned_employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    status: Mapped[int] = mapped_column(SmallInteger, default=INCOMING_RECEIVED)
    note: Mapped[str] = mapped_column(Text, default="")
