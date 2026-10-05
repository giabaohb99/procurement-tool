"""Schema MẪU LỊCH TUẦN — `/api/work-schedules`.

`test/backend` chạy SQLite không ép độ dài VARCHAR, nên mọi trần đều khai ở ĐÂY
(`max_length`) và được kiểm bằng `pytest.raises(ValidationError)`.
"""
from datetime import datetime, time

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.work_schedule_codes import WorkDayKind

VALID_KINDS = {int(k) for k in WorkDayKind}
WEEK_DAYS = 7


class DayIn(BaseModel):
    """Một dòng ngày của mẫu. Giờ nhận "HH:MM" (pydantic tự đọc ra `time`).

    Loại ngày nửa buổi (Sáng/Chiều) là ĐIỀU CHỈ ĐỊNH: loại ngày thắng giờ. Cố ý KHÔNG ràng
    giờ theo buổi (không bịa mốc 12:00/13:00): «Sáng» mà giờ làm 13:00–17:00 vẫn hợp lệ, khi đó
    đơn nghỉ bắt đầu «Chiều» của ngày ấy tính 0 vì mặt nạ buổi là Sáng. Chỉ cấm ô nghỉ trưa.
    """

    weekday: int = Field(ge=0, le=6)
    day_kind: int
    start_time: time | None = None
    end_time: time | None = None
    lunch_start: time | None = None
    lunch_end: time | None = None

    @field_validator("day_kind")
    @classmethod
    def _kind_in_enum(cls, v: int) -> int:
        if v not in VALID_KINDS:
            raise ValueError("Loại ngày không hợp lệ (1 Nghỉ, 2 Cả ngày, 3 Sáng, 4 Chiều)")
        return v

    @field_validator("start_time", "end_time", "lunch_start", "lunch_end")
    @classmethod
    def _clean_clock(cls, v: time | None) -> time | None:
        #  Bug M1: "08:00Z" ra `time` CÓ tzinfo, so với giờ không tz ném TypeError -> 500.
        #  Bug L2: "08:00:30" lọt kiểm `start < end` rồi `_minutes` bỏ giây -> ngày 0 giờ.
        if v is None:
            return v
        if v.tzinfo is not None:
            raise ValueError("Giờ không được kèm múi giờ, chỉ nhập dạng HH:MM")
        if v.second or v.microsecond:
            raise ValueError("Giờ chỉ nhập đến phút (HH:MM), không có giây")
        return v

    @model_validator(mode="after")
    def _check_hours(self) -> "DayIn":
        kind = WorkDayKind(self.day_kind)
        if kind is WorkDayKind.OFF:
            #  Ngày nghỉ: ép bốn ô giờ về null, khỏi rác lọt xuống DB.
            self.start_time = self.end_time = self.lunch_start = self.lunch_end = None
            return self
        if self.start_time is None or self.end_time is None or self.start_time >= self.end_time:
            raise ValueError("Ngày làm việc phải có giờ bắt đầu nhỏ hơn giờ kết thúc")
        has_lunch = (self.lunch_start, self.lunch_end)
        if kind is not WorkDayKind.FULL:
            if any(has_lunch):
                raise ValueError("Ngày làm nửa ngày không có giờ nghỉ trưa")
            return self
        if sum(x is not None for x in has_lunch) == 1:
            raise ValueError("Giờ nghỉ trưa phải nhập đủ cặp «từ — đến» hoặc bỏ trống cả hai")
        if self.lunch_start is not None and not (
                self.start_time < self.lunch_start < self.lunch_end < self.end_time):
            raise ValueError("Nghỉ trưa phải nằm trong giờ làm: bắt đầu < trưa từ < trưa đến < kết thúc")
        return self


def validate_week(days: list[DayIn]) -> list[DayIn]:
    """Đúng 7 dòng, `weekday` 0..6 không trùng."""
    if len(days) != WEEK_DAYS:
        raise ValueError("Mẫu lịch phải có đúng 7 dòng (Thứ hai đến Chủ nhật)")
    if {d.weekday for d in days} != set(range(WEEK_DAYS)):
        raise ValueError("Mỗi thứ trong tuần phải xuất hiện đúng một lần")
    return sorted(days, key=lambda d: d.weekday)


class ScheduleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    note: str = Field("", max_length=500)
    is_active: bool = True
    days: list[DayIn] = Field(max_length=WEEK_DAYS)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tên mẫu lịch không được để trống")
        return v

    @field_validator("days")
    @classmethod
    def _week(cls, v: list[DayIn]) -> list[DayIn]:
        return validate_week(v)


class ScheduleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    note: str | None = Field(None, max_length=500)
    is_active: bool | None = None
    days: list[DayIn] | None = Field(None, max_length=WEEK_DAYS)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Tên mẫu lịch không được để trống")
        return v

    @field_validator("days")
    @classmethod
    def _week(cls, v: list[DayIn] | None) -> list[DayIn] | None:
        return None if v is None else validate_week(v)


class DayOut(BaseModel):
    weekday: int
    day_kind: int
    day_kind_label: str
    start_time: str | None = None
    end_time: str | None = None
    lunch_start: str | None = None
    lunch_end: str | None = None


class ScheduleOut(BaseModel):
    id: int
    name: str
    note: str
    is_active: bool
    days: list[DayOut]
    weekly_workdays: float
    assignment_count: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
