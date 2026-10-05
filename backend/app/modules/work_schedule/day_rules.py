"""LUẬT MỘT NGÀY LÀM VIỆC — thuần (không đụng DB), dùng cho bộ phân giải và tính ngày nghỉ.

Nửa ngày là LOẠI NGÀY (`WorkDayKind`), không suy từ giờ. Mỗi ngày biểu diễn bằng
bitmask nửa buổi: `AM = 1`, `PM = 2`. Công của một ngày nghỉ = 0.5 × số nửa buổi
vừa nghỉ vừa phải làm (xem `leave/workday_service.py`).

`FALLBACK_WEEK` là NGUỒN DUY NHẤT của giờ mặc định (T2–T7 08:00–17:00, trưa 12–13,
CN nghỉ) — thay cho các hằng `WORK_DAY_*` cũ ở `leave/constants.py`. Chưa gán lịch
nào thì mọi số ngày nghỉ phép phải ra đúng như trước khi có Lịch làm việc.
"""
from dataclasses import dataclass
from datetime import time

from app.core.work_schedule_codes import WorkDayKind

AM = 1
PM = 2


@dataclass(frozen=True)
class DaySpec:
    """Một ngày trong tuần của mẫu lịch. Ngày OFF thì bốn ô giờ là None."""

    kind: WorkDayKind
    start: time | None = None
    end: time | None = None
    lunch_start: time | None = None
    lunch_end: time | None = None


_OFF = DaySpec(WorkDayKind.OFF)
_FULL = DaySpec(WorkDayKind.FULL, time(8, 0), time(17, 0), time(12, 0), time(13, 0))

#  Index = `date.weekday()` (0 = Thứ hai … 6 = Chủ nhật). DEGO làm cả thứ Bảy.
FALLBACK_WEEK: tuple[DaySpec, ...] = (_FULL,) * 6 + (_OFF,)
#  Ngày làm trọn chuẩn — dùng khi bỏ qua lịch (loại nghỉ `exclude_holiday=False`).
FULL_DAY_SPEC = _FULL
FALLBACK_NAME = "Mặc định hệ thống (T2–T7, 08:00–17:00)"

_MASKS = {WorkDayKind.OFF: 0, WorkDayKind.FULL: AM | PM,
          WorkDayKind.MORNING: AM, WorkDayKind.AFTERNOON: PM}


def work_mask(spec: DaySpec) -> int:
    """Bitmask nửa buổi phải đi làm: OFF=0, FULL=3, MORNING=1, AFTERNOON=2."""
    return _MASKS.get(spec.kind, 0)


def day_capacity(spec: DaySpec) -> float:
    """Công tối đa của ngày: 1.0 (cả ngày) · 0.5 (nửa ngày) · 0 (nghỉ)."""
    return 0.5 * bin(work_mask(spec)).count("1")


def _minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def worked_hours(spec: DaySpec, start: time, end: time) -> float:
    """Số GIỜ CÔNG trong `[start, end)` của ngày này.

    Cắt theo khung giờ làm của ngày rồi trừ phần chồng giờ nghỉ trưa. Ngày OFF hoặc
    thiếu giờ → 0. Khoảng ngoài khung (nghỉ 19:00) không tính: vắng ngoài giờ làm
    không phải nghỉ phép.
    """
    if work_mask(spec) == 0 or spec.start is None or spec.end is None:
        return 0.0
    lo = max(_minutes(start), _minutes(spec.start))
    hi = min(_minutes(end), _minutes(spec.end))
    if hi <= lo:
        return 0.0
    lunch = 0
    if spec.lunch_start is not None and spec.lunch_end is not None:
        lunch = max(0, min(hi, _minutes(spec.lunch_end)) - max(lo, _minutes(spec.lunch_start)))
    return (hi - lo - lunch) / 60.0


def day_hours(spec: DaySpec) -> float:
    """Tổng giờ công của một ngày (đã trừ nghỉ trưa); OFF = 0."""
    if spec.start is None or spec.end is None:
        return 0.0
    return worked_hours(spec, spec.start, spec.end)


def weekly_workdays(specs) -> float:
    """Số ngày công một tuần = tổng `day_capacity` (T2–T6 + sáng T7 = 5.5)."""
    return sum(day_capacity(s) for s in specs)
