"""Schema XẾP CA THEO NGÀY — `/api/work-shifts` (duoc-CR-761).

`test/backend` chạy SQLite không ép độ dài VARCHAR, nên mọi trần đều khai ở ĐÂY (`max_length`) và được kiểm bằng
`pytest.raises(ValidationError)`. Trần mỗi lượt ghi hàng loạt: ≤ 50 người, ≤ 42 ngày, ≤ 500 ô.
"""
from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

from .assignment_schema import MAX_ID, YEAR_MAX, YEAR_MIN
from .shift_rules import MAX_SEGMENTS, normalize_segments

MAX_NOTE = 255                 # = String(255) của `tab_work_shift_day.note`
MAX_RANGE_DAYS = 42            # khoảng xem / số ngày một lượt ghi hàng loạt
MAX_BULK_EMPLOYEES = 50
MAX_BULK_CELLS = 500           # người × ngày một lượt


def check_year(value: date) -> date:
    if not (YEAR_MIN <= value.year <= YEAR_MAX):
        raise ValueError(f"Ngày phải nằm trong năm {YEAR_MIN}–{YEAR_MAX}")
    return value


class SegmentIn(BaseModel):
    """Một khung giờ tròn `[start_hour, end_hour)`; 24 = hết ngày."""

    start_hour: int = Field(ge=0, le=23)
    end_hour: int = Field(ge=1, le=24)

    @model_validator(mode="after")
    def _ordered(self) -> "SegmentIn":
        if self.start_hour >= self.end_hour:
            raise ValueError("Giờ bắt đầu của khung phải nhỏ hơn giờ kết thúc")
        return self


class _ShiftBody(BaseModel):
    """Phần chung: các khung của một ngày + ghi chú. Danh sách rỗng = NGHỈ cả ngày do xếp ca."""

    segments: list[SegmentIn] = Field(default_factory=list, max_length=MAX_SEGMENTS)
    note: str = Field("", max_length=MAX_NOTE)

    @field_validator("note")
    @classmethod
    def _strip_note(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def _no_overlap(self) -> "_ShiftBody":
        #  Sắp + chống chồng; thay danh sách bằng bản đã sắp để service ghi đúng thứ tự.
        pairs = normalize_segments((s.start_hour, s.end_hour) for s in self.segments)
        self.segments = [SegmentIn(start_hour=a, end_hour=b) for a, b in pairs]
        return self

    def pairs(self) -> list[tuple[int, int]]:
        return [(s.start_hour, s.end_hour) for s in self.segments]


class ShiftPut(_ShiftBody):
    """Body của `PUT /{employee_id}/{work_date}` — thay cả danh sách khung của ngày đó."""


class ShiftBulk(_ShiftBody):
    """Body của `POST /bulk` — áp CÙNG một bộ khung cho nhiều người × nhiều ngày."""

    employee_ids: list[int] = Field(min_length=1, max_length=MAX_BULK_EMPLOYEES)
    dates: list[date] = Field(min_length=1, max_length=MAX_RANGE_DAYS)

    @field_validator("employee_ids")
    @classmethod
    def _ids(cls, value: list[int]) -> list[int]:
        if any(i < 1 or i > MAX_ID for i in value):
            raise ValueError("Mã nhân sự không hợp lệ")
        return list(dict.fromkeys(value))   # bỏ trùng, giữ thứ tự

    @field_validator("dates")
    @classmethod
    def _dates(cls, value: list[date]) -> list[date]:
        return sorted({check_year(d) for d in value})

    @model_validator(mode="after")
    def _cell_cap(self) -> "ShiftBulk":
        if len(self.employee_ids) * len(self.dates) > MAX_BULK_CELLS:
            raise ValueError(f"Mỗi lượt tối đa {MAX_BULK_CELLS} ô (người × ngày)")
        return self


class ShiftCopyWeek(BaseModel):
    """Body của `POST /copy-week` — chép ca của tuần nguồn sang tuần đích cho các nhân sự đã chọn."""

    employee_ids: list[int] = Field(min_length=1, max_length=MAX_BULK_EMPLOYEES)
    source_week_start: date
    target_week_start: date
    overwrite: bool = False

    @field_validator("employee_ids")
    @classmethod
    def _ids(cls, value: list[int]) -> list[int]:
        if any(i < 1 or i > MAX_ID for i in value):
            raise ValueError("Mã nhân sự không hợp lệ")
        return list(dict.fromkeys(value))

    @field_validator("source_week_start", "target_week_start")
    @classmethod
    def _monday(cls, value: date) -> date:
        check_year(value)
        if value.weekday() != 0:
            raise ValueError("Ngày đầu tuần phải là thứ Hai")
        return value

    @model_validator(mode="after")
    def _different_weeks(self) -> "ShiftCopyWeek":
        if self.source_week_start == self.target_week_start:
            raise ValueError("Tuần đích phải khác tuần nguồn")
        return self
