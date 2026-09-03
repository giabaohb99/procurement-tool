"""Hình dạng dữ liệu vào/ra của phân hệ Nghỉ phép (Pydantic v2).

Quy ước chung của bộ ERP: cột trạng thái/loại/buổi ra API là **số kèm nhãn**
(`status` + `status_label`), tiếng Việt chỉ ở nhãn. Giao diện đọc số để so sánh,
đọc nhãn để hiện — không bao giờ so chuỗi tiếng Việt.
"""
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from .constants import (GENDER_LABELS, LEAVE_REQUEST_STATUS_LABELS,
                        LEAVE_SESSION_LABELS, LEAVE_UNIT_LABELS, SESSION_FULL,
                        UNIT_DAY, label)

#  Bí danh của `datetime.date`, dùng cho các lớp có TRƯỜNG TÊN LÀ `date`
#  (`HolidayBase`, `HolidayUpdate`). Trong thân lớp, Python gán tên đích TRƯỚC
#  khi tính chú thích kiểu, nên `date: date | None = None` biến `date` thành
#  `None` rồi mới đọc chú thích — ra `TypeError: unsupported operand |`. Bí danh
#  gỡ đúng chỗ đó mà không phải đổi tên cột cho khác đi.
DateOnly = date


# ── Loại nghỉ (V1-6) ────────────────────────────────────────────────────────────

class LeaveTypeBase(BaseModel):
    code: str = Field(..., max_length=30)
    name: str = Field(..., max_length=100)
    is_paid: bool = True
    counts_balance: bool = False
    annual_quota_days: float = 0.0
    max_days_per_request: float = 0.0
    carry_over: bool = False
    carry_over_max_days: float = 0.0
    carry_over_expire_month: int = 3
    gender: int = 0
    min_notice_days: int = 0
    require_attachment: bool = False
    exclude_holiday: bool = True
    sort_order: int = 0
    is_active: bool = True
    note: str = Field("", max_length=500)

    @field_validator("code")
    @classmethod
    def _upper_code(cls, v: str) -> str:
        #  Mã đi vào metadata của giấy GNP và vào seed — chuẩn hóa một lần ở đây
        #  còn hơn để «Annual» và «annual» thành hai loại nghỉ khác nhau.
        return (v or "").strip().lower()


class LeaveTypeCreate(LeaveTypeBase):
    pass


class LeaveTypeUpdate(BaseModel):
    #  `code` KHÔNG sửa được: nó là mối nối sang giấy GNP và sang seed. Đổi mã
    #  thì mọi giấy đã phát hành trỏ vào một loại không còn tồn tại.
    name: str | None = None
    is_paid: bool | None = None
    counts_balance: bool | None = None
    annual_quota_days: float | None = None
    max_days_per_request: float | None = None
    carry_over: bool | None = None
    carry_over_max_days: float | None = None
    carry_over_expire_month: int | None = None
    gender: int | None = None
    min_notice_days: int | None = None
    require_attachment: bool | None = None
    exclude_holiday: bool | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    note: str | None = None


class LeaveTypeResponse(LeaveTypeBase):
    id: int

    @property
    def gender_label(self) -> str:
        return label(GENDER_LABELS, self.gender)

    class Config:
        from_attributes = True


class SeniorityTierBase(BaseModel):
    leave_type_id: int
    years_from: int = 0
    #  `0` = bậc cuối, không có trần trên.
    years_to: int = 0
    extra_days: float = 0.0
    note: str = Field("", max_length=255)


class SeniorityTierCreate(SeniorityTierBase):
    pass


class SeniorityTierUpdate(BaseModel):
    years_from: int | None = None
    years_to: int | None = None
    extra_days: float | None = None
    note: str | None = None


class SeniorityTierResponse(SeniorityTierBase):
    id: int

    class Config:
        from_attributes = True


# ── Lịch ngày lễ ────────────────────────────────────────────────────────────────

class HolidayBase(BaseModel):
    #  `0` = áp cho MỌI pháp nhân — xem `workday_service.holiday_dates`.
    company_id: int = 0
    date: DateOnly
    name: str = Field("", max_length=150)
    is_recurring: bool = False
    is_active: bool = True


class HolidayCreate(HolidayBase):
    pass


class HolidayUpdate(BaseModel):
    company_id: int | None = None
    date: DateOnly | None = None
    name: str | None = None
    is_recurring: bool | None = None
    is_active: bool | None = None


class HolidayResponse(HolidayBase):
    id: int

    class Config:
        from_attributes = True


# ── Quỹ phép ────────────────────────────────────────────────────────────────────

class LeaveBalanceResponse(BaseModel):
    id: int
    employee_id: int
    year: int
    leave_type_id: int
    company_id: int
    allocated_days: float
    seniority_days: float
    carried_days: float
    adjusted_days: float
    used_days: float
    pending_days: float
    note: str
    #  Hai số DẪN XUẤT, tính ở model. Trả kèm để màn hình không phải cộng trừ lại
    #  — cộng trừ ở hai đầu là hai công thức, và cái thứ hai sẽ lệch.
    total_days: float = 0.0
    remaining_days: float = 0.0

    class Config:
        from_attributes = True


class LeaveBalanceAdjust(BaseModel):
    """Nhân sự chỉnh tay. Cột duy nhất nhận số ÂM — xem `balance_model`."""

    adjusted_days: float
    note: str = Field("", max_length=500)


class LeaveBalanceAllocate(BaseModel):
    """Cấp phát quỹ hàng loạt cho một năm."""

    year: int
    #  Bỏ trống = mọi loại nghỉ CÓ trừ quỹ. Khai rõ thì chỉ cấp các loại đó.
    leave_type_ids: list[int] = Field(default_factory=list)
    #  Bỏ trống = mọi nhân sự đang làm việc trong phạm vi người bấm.
    employee_ids: list[int] = Field(default_factory=list)


# ── Đơn nghỉ phép (V1-7) ────────────────────────────────────────────────────────

class HandoverItem(BaseModel):
    employee_id: int
    content: str = Field("", max_length=500)


class LeaveRequestBase(BaseModel):
    #  Bỏ trống = người đang lập đơn. Lập hộ vẫn được — hành chính lập hộ là việc
    #  có thật, cùng luật với `_check_leave` của giấy GNP.
    employee_id: int = 0
    leave_type_id: int
    from_date: date
    to_date: date
    from_session: int = SESSION_FULL
    to_session: int = SESSION_FULL
    unit: int = UNIT_DAY
    #  `0` = để backend tự tính bằng `workday_service`. Nhập khác 0 là sửa đè.
    total_days: float = 0.0
    reason: str = Field("", max_length=1000)
    contact_phone: str = Field("", max_length=30)
    contact_address: str = Field("", max_length=255)
    handovers: list[HandoverItem] = Field(default_factory=list)


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestUpdate(BaseModel):
    employee_id: int | None = None
    leave_type_id: int | None = None
    from_date: date | None = None
    to_date: date | None = None
    from_session: int | None = None
    to_session: int | None = None
    unit: int | None = None
    total_days: float | None = None
    reason: str | None = None
    contact_phone: str | None = None
    contact_address: str | None = None
    handovers: list[HandoverItem] | None = None


class HandoverResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str = ""
    content: str
    sort_order: int

    class Config:
        from_attributes = True


class LeaveRequestResponse(BaseModel):
    id: int
    code: str
    company_id: int
    department_id: int
    employee_id: int
    leave_type_id: int
    from_date: date
    to_date: date
    from_session: int
    to_session: int
    unit: int
    total_days: float
    reason: str
    contact_phone: str
    contact_address: str
    status: int
    approval_instance_id: int
    document_id: int
    submitted_at: datetime | None = None
    decided_at: datetime | None = None
    decision_note: str

    class Config:
        from_attributes = True


def request_labels(obj) -> dict:
    """Nhãn tiếng Việt kèm theo — R2: số ở cột, chữ ở tầng hiển thị."""
    return {
        "status_label": label(LEAVE_REQUEST_STATUS_LABELS, obj.status),
        "from_session_label": label(LEAVE_SESSION_LABELS, obj.from_session),
        "to_session_label": label(LEAVE_SESSION_LABELS, obj.to_session),
        "unit_label": label(LEAVE_UNIT_LABELS, obj.unit),
    }
