"""Hình dạng dữ liệu vào/ra của phân hệ Nghỉ phép (Pydantic v2).

Quy ước chung của bộ ERP: cột trạng thái/loại/buổi ra API là **số kèm nhãn**
(`status` + `status_label`), tiếng Việt chỉ ở nhãn. Giao diện đọc số để so sánh,
đọc nhãn để hiện — không bao giờ so chuỗi tiếng Việt.
"""
from datetime import date, datetime, time

from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.employee.field_limits import Str30, Str100, Str150, Str255, Str500, Str1000
from .constants import (GENDER_LABELS, LEAVE_REQUEST_STATUS_LABELS,
                        LEAVE_SESSION_LABELS, LEAVE_UNIT_LABELS, SESSION_FULL,
                        UNIT_DAY, YEAR_END_DROP, YEAR_END_MODE_LABELS, label)

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
    #  ⚠️ KHÔNG khai `carry_over`: công tắc hai nước đó đã thay bằng
    #  `year_end_mode` (07/09/2026). Cột còn trong bảng nhưng không đọc, không
    #  sửa, không trả về — cùng luật với `min_notice_days` bên dưới.
    year_end_mode: int = YEAR_END_DROP
    carry_over_max_days: float = 0.0
    carry_over_expire_month: int = 3
    convert_to_type_id: int = 0
    convert_ratio: float = 1.0
    gender: int = 0
    #  ⚠️ KHÔNG khai `min_notice_days`: luật "phải nộp trước N ngày" đã bỏ
    #  (05/09/2026). Cột còn trong bảng nhưng không đọc, không sửa, không trả về.
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
    name: Str100 | None = None
    is_paid: bool | None = None
    counts_balance: bool | None = None
    annual_quota_days: float | None = None
    max_days_per_request: float | None = None
    year_end_mode: int | None = None
    carry_over_max_days: float | None = None
    carry_over_expire_month: int | None = None
    convert_to_type_id: int | None = None
    convert_ratio: float | None = None
    gender: int | None = None
    require_attachment: bool | None = None
    exclude_holiday: bool | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    note: Str500 | None = None


class LeaveTypeResponse(LeaveTypeBase):
    id: int

    @property
    def gender_label(self) -> str:
        return label(GENDER_LABELS, self.gender)

    @property
    def year_end_mode_label(self) -> str:
        return label(YEAR_END_MODE_LABELS, self.year_end_mode)

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
    note: Str255 | None = None


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
    name: Str150 | None = None
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
    #  Đã mang khỏi dòng này lúc kết sổ; `carried_expired_days` là phần mang
    #  sang đã hết hạn. Cái đầu vào công thức còn lại, cái sau chỉ để giải thích.
    carried_out_days: float = 0.0
    carried_expired_days: float = 0.0
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


class LeaveBalanceCloseYear(BaseModel):
    """Kết sổ cuối năm — đẩy số dư sang năm sau theo luật của từng loại nghỉ.

    Khai `year` là năm ĐANG kết, phần nhận rơi vào `year + 1`. Không có
    `leave_type_ids`: luật nằm ở chính loại nghỉ (`year_end_mode`), chọn tay ở
    đây thì có đường bỏ sót một loại mà không ai biết là đã bỏ.
    """

    year: int
    #  Bỏ trống = mọi nhân sự trong phạm vi người bấm.
    employee_ids: list[int] = Field(default_factory=list)


# ── Đơn nghỉ phép (V1-7) ────────────────────────────────────────────────────────

class HandoverItem(BaseModel):
    employee_id: int
    content: str = Field("", max_length=500)


class LeaveLineItem(BaseModel):
    """Một loại nghỉ trong đơn (07/09/2026).

    `days = 0` chỉ hợp lệ khi đơn có ĐÚNG MỘT dòng — lúc đó máy tự tính từ
    khoảng ngày, đúng hành vi của `total_days = 0` thời một loại. Nhiều dòng thì
    phải gõ rõ từng con số: máy không đoán được chia 4 ngày thành 3+1 hay 2+2.
    """

    leave_type_id: int
    days: float = 0.0


#  Trần số khoảng ngày của một đơn (duoc-CR-683) — danh sách con phải có trần số dòng.
MAX_PERIODS = 20
#  Dải năm hợp lý cho ngày nghỉ; MySQL nhận tới 9999 nhưng gõ nhầm năm là lỗi phổ biến.
LeaveDate = Annotated[date, Field(ge=date(2000, 1, 1), le=date(2100, 12, 31))]
SessionCode = Annotated[int, Field(ge=1, le=4)]


class LeavePeriodItem(BaseModel):
    """Một khoảng ngày liền của đơn. Luật buổi y như hai ô buổi ở đầu đơn."""

    from_date: LeaveDate
    to_date: LeaveDate
    from_session: SessionCode = SESSION_FULL
    to_session: SessionCode = SESSION_FULL


class LeaveEstimateIn(BaseModel):
    """Body của đường ước lượng số ngày theo nhiều khoảng (phase 2)."""

    employee_id: int = 0
    leave_type_id: int = 0
    periods: list[LeavePeriodItem] = Field(..., min_length=1, max_length=MAX_PERIODS)
    from_time: time | None = None
    to_time: time | None = None


class LeaveRequestBase(BaseModel):
    #  Bỏ trống = người đang lập đơn. Lập hộ vẫn được — hành chính lập hộ là việc
    #  có thật, cùng luật với `_check_leave` của giấy GNP.
    employee_id: int = 0
    #  ⚠️ **Còn nhận `leave_type_id` là CỐ Ý.** Từ 07/09/2026 nguồn thật là
    #  `lines`, nhưng bỏ ô này thì mọi đường gọi cũ (gói tri thức Trợ lý AI, bài
    #  kiểm, kịch bản seed) gãy cùng lúc mà chẳng đổi lấy gì. Không gửi `lines`
    #  thì backend dựng một dòng từ đúng cặp `leave_type_id` + `total_days` cũ —
    #  xem `request_service.build_lines`.
    leave_type_id: int = 0
    lines: list[LeaveLineItem] = Field(default_factory=list)
    #  Không gửi `periods` thì backend dựng MỘT khoảng từ cặp `from_date`/`to_date`
    #  (đường tương thích: Trợ lý AI, agent_hub, bài kiểm cũ). Có `periods` thì
    #  hai ô ngày này bị bỏ qua — đầu đơn là dẫn xuất của danh sách khoảng.
    periods: list[LeavePeriodItem] = Field(default_factory=list, max_length=MAX_PERIODS)
    from_date: date | None = None
    to_date: date | None = None
    from_session: int = SESSION_FULL
    to_session: int = SESSION_FULL
    #  Chỉ khai khi buổi là «Theo giờ» (`SESSION_HOURLY`). `None` = không nghỉ
    #  theo giờ — xem `request_service.check_hourly`.
    from_time: time | None = None
    to_time: time | None = None
    unit: int = UNIT_DAY
    #  `0` = để backend tự tính bằng `workday_service`. Nhập khác 0 là sửa đè.
    total_days: float = 0.0
    reason: str = Field("", max_length=1000)
    contact_phone: str = Field("", max_length=30)
    contact_address: str = Field("", max_length=255)
    handovers: list[HandoverItem] = Field(default_factory=list)


class LeaveRequestCreate(LeaveRequestBase):
    @model_validator(mode="after")
    def _need_periods_or_dates(self):
        if not self.periods and (self.from_date is None or self.to_date is None):
            raise ValueError("Cần khai danh sách khoảng ngày (periods) hoặc cặp from_date + to_date")
        return self


class LeaveRequestUpdate(BaseModel):
    employee_id: int | None = None
    leave_type_id: int | None = None
    #  `None` = không đụng tới danh sách dòng; gửi lên là GHI ĐÈ cả danh sách,
    #  cùng quy ước với `handovers`.
    lines: list[LeaveLineItem] | None = None
    #  `None` = không gửi. Gửi lên là GHI ĐÈ cả danh sách khoảng (đầu đơn tự tính lại).
    periods: list[LeavePeriodItem] | None = Field(None, max_length=MAX_PERIODS)
    from_date: date | None = None
    to_date: date | None = None
    from_session: int | None = None
    to_session: int | None = None
    from_time: time | None = None
    to_time: time | None = None
    unit: int | None = None
    total_days: float | None = None
    reason: Str1000 | None = None
    contact_phone: Str30 | None = None
    contact_address: Str255 | None = None
    handovers: list[HandoverItem] | None = None


class HandoverResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str = ""
    content: str
    sort_order: int

    class Config:
        from_attributes = True


class LeaveLineResponse(BaseModel):
    id: int
    leave_type_id: int
    leave_type_name: str = ""
    days: float
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
    from_time: time | None = None
    to_time: time | None = None
    unit: int
    total_days: float
    reason: str
    contact_phone: str
    contact_address: str
    status: int
    approval_instance_id: int
    document_id: int
    #  Thời điểm LẬP đơn. Trả ra để dòng thời gian phê duyệt có mốc đầu tiên:
    #  dấu vết của bộ máy duyệt bắt đầu từ lúc GỬI, nên thiếu cột này thì màn
    #  chi tiết kể chuyện từ giữa — người xem không thấy đơn ra đời lúc nào,
    #  cũng không thấy nó nằm nháp bao lâu trước khi trình.
    created_at: datetime | None = None
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
