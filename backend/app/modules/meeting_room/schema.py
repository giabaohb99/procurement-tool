"""Schema Pydantic của Đặt phòng họp."""
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field


def _reject_timezone(value: datetime) -> datetime:
    """Chặn giờ có KÈM MÚI GIỜ ngay ở cổng vào.

    ⚠️ Cả hệ lưu **giờ trần** (naive) theo giờ Việt Nam — cột `DATETIME` của
    MySQL không mang múi giờ, và mọi chỗ so sánh đều so giờ trần với giờ trần.
    Nhận một giá trị có múi giờ thì Python **ném `TypeError`** ngay ở phép so
    đầu tiên (`can't compare offset-naive and offset-aware datetimes`) và người
    gọi nhận **HTTP 500** thay vì một câu nói rõ mình sai chỗ nào. Đo được ngày
    04/09/2026 bằng đợt bắn dữ liệu rác: `start_at = 12345` (Pydantic hiểu là
    dấu thời gian Unix nên tự gắn UTC vào) làm sập cả `create`, `update`,
    `reschedule` lẫn `/availability`.

    Chọn CHẶN chứ không tự quy đổi, vì quy đổi kiểu nào cũng đoán mò: container
    chạy UTC nên `astimezone()` biến 10:00+07:00 thành 03:00, còn cắt phăng múi
    giờ thì `10:00+00:00` (tức 17:00 giờ ta) lại bị hiểu thành 10:00. Đoán sai
    giờ họp thì không ai phát hiện ra cho tới lúc không có ai đến phòng.
    """
    if value.tzinfo is not None:
        raise ValueError(
            "Gửi giờ địa phương, KHÔNG kèm múi giờ (vd «2026-09-20T09:00:00»).")
    return value


#  Mọi ô giờ của phân hệ này dùng kiểu đó — khai lẻ từng chỗ là chắc chắn sót.
LocalDateTime = Annotated[datetime, AfterValidator(_reject_timezone)]


# ── Danh mục phòng ─────────────────────────────────────────────────────────────

class MeetingRoomCreate(BaseModel):
    code: str = Field(..., max_length=30)
    name: str = Field(..., max_length=255)
    company_id: int = 0
    location: str = ""
    capacity: int = 0
    equipment: str = ""
    is_active: bool = True
    sort_order: int = 0
    note: str = ""


class MeetingRoomUpdate(BaseModel):
    #  `code` KHÔNG có ở đây: mã phòng đi vào mọi phiếu đã đặt và vào cách người
    #  ta gọi nhau ("họp ở P301"). Đổi mã là mọi thứ đã in ra trỏ vào chỗ khác.
    name: str | None = Field(None, max_length=255)
    company_id: int | None = None
    location: str | None = None
    capacity: int | None = None
    equipment: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None
    note: str | None = None


class MeetingRoomResponse(BaseModel):
    id: int
    code: str
    name: str
    company_id: int
    location: str
    capacity: int
    equipment: str
    is_active: bool
    sort_order: int
    note: str

    class Config:
        from_attributes = True


# ── Phiếu đặt ──────────────────────────────────────────────────────────────────

class AttendeeItem(BaseModel):
    employee_id: int
    role: str = ""


class RoomBookingCreate(BaseModel):
    room_id: int
    title: str = Field(..., max_length=255)
    start_at: LocalDateTime
    end_at: LocalDateTime
    #  Trần ô ghi chú. Cột là `Text` nên không có ràng buộc ở tầng dữ liệu, mà
    #  một lệnh gọi API thẳng có thể nhồi hàng megabyte vào đây — mỗi lần mở
    #  danh sách là kéo nguyên chỗ đó về trình duyệt.
    purpose: str = Field("", max_length=5000)
    #  `ge=0`: số người dự ÂM lọt qua mọi chốt vì `check_capacity` chỉ so với
    #  trần trên (-5 < sức chứa nên hợp lệ). Đo được 04/09/2026 — phiếu lưu
    #  «-5 người» và màn tóm tắt hiện đúng con số đó.
    attendee_count: int = Field(0, ge=0)
    #  Người ĐẶT. Bỏ trống = chính người đang lập phiếu (thư ký đặt hộ sếp thì
    #  điền id của sếp vào đây).
    requester_employee_id: int = 0
    attendees: list[AttendeeItem] = []


class RoomBookingUpdate(BaseModel):
    room_id: int | None = None
    title: str | None = Field(None, max_length=255)
    start_at: LocalDateTime | None = None
    end_at: LocalDateTime | None = None
    purpose: str | None = Field(None, max_length=5000)
    attendee_count: int | None = Field(None, ge=0)
    requester_employee_id: int | None = None
    attendees: list[AttendeeItem] | None = None


class RoomBookingReschedule(BaseModel):
    """Dời giờ / đổi phòng bằng KÉO THẢ trên lịch.

    Tách khỏi `RoomBookingUpdate` vì hai đường khác nhau về quyền sửa: `update`
    chỉ nhận phiếu chưa vào luồng, còn kéo thả thì thứ người ta kéo hầu hết là
    phiếu **đang giữ phòng**. Ba ô, không hơn — kéo trên lịch chỉ đổi được chỗ và
    giờ; mọi thứ khác vẫn phải mở phiếu ra sửa.
    """
    #  `0` = giữ nguyên phòng cũ (kéo ngang trong cùng một hàng).
    room_id: int = 0
    start_at: LocalDateTime
    end_at: LocalDateTime


class RoomBookingResponse(BaseModel):
    id: int
    code: str
    room_id: int
    room_name: str = ""
    room_code: str = ""
    company_id: int
    department_id: int
    requester_employee_id: int
    requester_name: str = ""
    title: str
    purpose: str
    start_at: datetime
    end_at: datetime
    attendee_count: int
    status: int
    status_label: str = ""
    approval_instance_id: int
    submitted_at: datetime | None = None
    decided_at: datetime | None = None
    decision_note: str

    class Config:
        from_attributes = True
