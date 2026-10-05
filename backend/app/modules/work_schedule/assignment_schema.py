"""Schema GÁN LỊCH — `/api/work-schedule-assignments`."""
from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.work_schedule_codes import WorkScheduleLevel

from .template_schema import DayOut

VALID_LEVELS = {int(k) for k in WorkScheduleLevel}
MAX_ID = 2**53   # trần an toàn cho id gửi từ JSON
YEAR_MIN, YEAR_MAX = 2000, 2100


def check_target(level: int, target_id: int) -> None:
    """SYSTEM ⇒ target_id == 0; cấp khác ⇒ target_id > 0. Ném ValueError nếu sai.

    `target_id = 0` ở cấp ≠ SYSTEM là dữ liệu hỏng (mọi NV chưa khai pháp nhân sẽ
    dính nó), nên chặn ngay lúc ghi.
    """
    if level == int(WorkScheduleLevel.SYSTEM):
        if target_id != 0:
            raise ValueError("Cấp «Toàn hệ thống» không có đối tượng (target_id phải bằng 0)")
    elif target_id <= 0:
        raise ValueError("Phải chọn đối tượng được gán lịch")


def check_period(start: date | None, end: date | None) -> None:
    if start and end and end < start:
        raise ValueError("«Đến ngày» không được trước «Từ ngày»")


def _year(v: date | None) -> date | None:
    if v is not None and not (YEAR_MIN <= v.year <= YEAR_MAX):
        raise ValueError(f"Ngày phải nằm trong năm {YEAR_MIN}–{YEAR_MAX}")
    return v


class _Fields(BaseModel):
    @field_validator("target_level", check_fields=False)
    @classmethod
    def _level(cls, v):
        if v is not None and v not in VALID_LEVELS:
            raise ValueError("Cấp gán lịch không hợp lệ (1 Hệ thống, 2 Pháp nhân, 3 Phòng ban, 4 Nhân sự)")
        return v

    @field_validator("effective_from", "effective_to", check_fields=False)
    @classmethod
    def _years(cls, v):
        return _year(v)


class AssignmentCreate(_Fields):
    target_level: int
    target_id: int = Field(0, ge=0, le=MAX_ID)
    schedule_id: int = Field(ge=1, le=MAX_ID)
    effective_from: date
    effective_to: date | None = None
    note: str = Field("", max_length=500)

    @model_validator(mode="after")
    def _cross(self) -> "AssignmentCreate":
        check_target(self.target_level, self.target_id)
        check_period(self.effective_from, self.effective_to)
        return self


class AssignmentUpdate(_Fields):
    """Mọi trường tùy chọn; ràng buộc chéo kiểm ở service trên giá trị đã gộp."""

    target_level: int | None = None
    target_id: int | None = Field(None, ge=0, le=MAX_ID)
    schedule_id: int | None = Field(None, ge=1, le=MAX_ID)
    effective_from: date | None = None
    effective_to: date | None = None
    note: str | None = Field(None, max_length=500)


class AssignmentOut(BaseModel):
    id: int
    target_level: int
    target_level_label: str
    target_id: int
    target_name: str
    schedule_id: int
    schedule_name: str
    effective_from: date
    effective_to: date | None = None
    note: str
    is_current: bool


class EffectiveOut(BaseModel):
    schedule_id: int
    schedule_name: str
    days: list[DayOut]
    weekly_workdays: float
    is_fallback: bool
    level: int
    level_label: str
    target_name: str
    assignment_id: int
    effective_from: date | None = None
    effective_to: date | None = None
