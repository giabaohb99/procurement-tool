"""PHÒNG HỌP và PHIẾU ĐẶT PHÒNG — duoc-CR-279.

Ba bảng, tách vì ba vòng đời khác nhau:

* `tab_meeting_room`         — danh mục phòng, đổi vài lần một năm;
* `tab_room_booking`         — phiếu đặt, chứng từ chạy qua bộ máy duyệt;
* `tab_room_booking_attendee`— người được mời, bảng con của phiếu.

⚠️ **Thời gian lưu `DATETIME`, không lưu chuỗi ISO** như `tab_vehicle_booking`
đang làm. Cả phân hệ này sống bằng đúng một câu hỏi — *"phòng này khoảng giờ này
có ai giữ chưa"* — và câu đó là phép so khoảng trên hai cột thời gian, chạy mỗi
lần ai đó gửi duyệt. So trên `VARCHAR` thì đúng được nhờ ISO xếp thứ tự từ vựng,
nhưng mất chỉ mục theo kiểu, và chỉ cần một chỗ ghi thiếu số 0 đầu giờ là sai âm
thầm.
"""
from datetime import datetime

from sqlalchemy import (BigInteger, Boolean, DateTime, Index, Integer,
                        SmallInteger, String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import AuditMixin, Base

from .constants import RB_DRAFT


class MeetingRoom(Base, AuditMixin):
    """Một phòng họp — tài nguyên được đặt."""

    __tablename__ = "tab_meeting_room"

    #  Mã ngắn để gọi nhau ("đặt P.301 nhé"), duy nhất toàn hệ.
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(255), default="")

    #  Pháp nhân sở hữu phòng. `0` = phòng dùng chung cho mọi pháp nhân (toà nhà
    #  chung) — cùng quy ước với `tab_holiday.company_id` của Nghỉ phép.
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    #  Vị trí đọc được: "Tầng 3, toà A". Không tách thành cây địa điểm — công ty
    #  một trụ sở mà bắt khai ba cấp là ba ô trống trên mọi form.
    location: Mapped[str] = mapped_column(String(255), default="")
    capacity: Mapped[int] = mapped_column(Integer, default=0)
    #  Thiết bị sẵn có, ghi tự do ("máy chiếu, bảng trắng"). CHỈ để người đặt
    #  chọn đúng phòng — không đặt riêng được thiết bị, đó là phân hệ khác.
    equipment: Mapped[str] = mapped_column(String(500), default="")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    #  Thứ tự bày trên lịch và ô chọn. Phòng hay dùng để lên đầu.
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(String(500), default="")


class RoomBooking(Base, AuditMixin):
    """Một phiếu đặt phòng."""

    __tablename__ = "tab_room_booking"
    __table_args__ = (
        #  Chỉ mục của CHỐT CHẶN TRÙNG và của màn Lịch đặt phòng: cả hai đều hỏi
        #  "phòng này, khoảng thời gian này". Thiếu nó thì mỗi lần gửi duyệt là
        #  một lần quét toàn bảng.
        Index("ix_room_booking_room_time", "room_id", "start_at", "end_at"),
        Index("ix_room_booking_status", "status"),
        Index("ix_room_booking_requester", "requester_employee_id"),
    )

    code: Mapped[str] = mapped_column(String(30), unique=True)
    room_id: Mapped[int] = mapped_column(BigInteger, default=0)

    #  Chép từ hồ sơ NGƯỜI ĐẶT lúc lập phiếu — hai cột này là chiều lọc phạm vi
    #  (`SCOPE_FIELDS["room_booking"]`). Chép chứ không JOIN: người chuyển phòng
    #  ban giữa năm thì phiếu cũ phải ở lại phòng ban cũ.
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  NGƯỜI ĐẶT (chủ trì cuộc họp). Khác `created_by` — thư ký đặt hộ sếp là
    #  việc có thật, và cả hai đều phải thấy phiếu ở phạm vi `own`.
    requester_employee_id: Mapped[int] = mapped_column(BigInteger, default=0)

    title: Mapped[str] = mapped_column(String(255), default="")
    purpose: Mapped[str] = mapped_column(Text, default="")

    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[datetime] = mapped_column(DateTime)
    #  Số người dự DỰ KIẾN, người đặt tự gõ. Không suy từ số dòng người được mời:
    #  mời đích danh 5 người nhưng "cả phòng Kinh doanh cùng vào" là chuyện
    #  thường, mà sức chứa phòng phải khớp với con số thật.
    attendee_count: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[int] = mapped_column(SmallInteger, default=RB_DRAFT)

    #  Phiên duyệt đang/đã chạy trên bộ máy dùng chung. `0` = chưa gửi duyệt,
    #  hoặc môi trường chưa khai luồng nào (lúc đó duyệt thẳng — xem
    #  `approval_bridge`).
    approval_instance_id: Mapped[int] = mapped_column(BigInteger, default=0)

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    #  Lý do từ chối / trả về / hủy — chép từ phiếu duyệt để màn chi tiết không
    #  phải gọi thêm một lượt sang bộ máy duyệt chỉ để hiện một dòng chữ.
    decision_note: Mapped[str] = mapped_column(String(500), default="")

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    attendees = relationship(
        "RoomBookingAttendee",
        primaryjoin="foreign(RoomBookingAttendee.booking_id) == RoomBooking.id",
        order_by="RoomBookingAttendee.sort_order",
        uselist=True,
        viewonly=True,
    )


class RoomBookingAttendee(Base, AuditMixin):
    """Người được mời dự — bảng con của phiếu.

    Bảng con chứ không phải một cột JSON: người được mời sẽ nhận thông báo, và
    sau này còn phải trả lời được câu "tuần này tôi bị mời họp mấy cuộc" — cả
    hai đều cần một cột `employee_id` có chỉ mục, không phải một mảng trong ô
    văn bản.
    """

    __tablename__ = "tab_room_booking_attendee"
    __table_args__ = (
        Index("ix_room_attendee_booking", "booking_id"),
        Index("ix_room_attendee_employee", "employee_id"),
    )

    booking_id: Mapped[int] = mapped_column(BigInteger, default=0)
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Vai trong cuộc họp, ghi tự do ("chủ trì", "thư ký"). Bỏ trống được.
    role: Mapped[str] = mapped_column(String(100), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
