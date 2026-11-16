"""LUẬT MỘT NGÀY LÀM VIỆC — thuần (không đụng DB), dùng cho bộ phân giải và tính ngày nghỉ.

Nửa ngày là LOẠI NGÀY (`WorkDayKind`), không suy từ giờ. Mỗi ngày biểu diễn bằng
bitmask nửa buổi: `AM = 1`, `PM = 2`. Công của một ngày nghỉ = 0.5 × số nửa buổi
vừa nghỉ vừa phải làm (xem `leave/workday_service.py`).

`FALLBACK_WEEK` là NGUỒN DUY NHẤT của giờ mặc định (T2–T7 08:00–17:00, trưa 12–13,
CN nghỉ) — thay cho các hằng `WORK_DAY_*` cũ ở `leave/constants.py`. Chưa gán lịch
nào thì mọi số ngày nghỉ phép phải ra đúng như trước khi có Lịch làm việc.

duoc-CR-761: ngày XẾP CA (`DaySpec.segments` khác None) là ngày theo khung giờ tròn do người xếp, thắng mọi mẫu lịch. Mọi hàm
dưới đây (`work_mask`, `day_capacity`, `day_hours`, `worked_hours`) đã biết cả hai loại ngày; công TRỪ PHÉP chỉ tính ở
`leave_credit` — các nơi đếm ngày nghỉ phải gọi nó thay vì tự nhân `0.5 × bit`.
"""
from dataclasses import dataclass
from datetime import time
from typing import Iterable

from app.core.work_schedule_codes import WorkDayKind

AM = 1
PM = 2


@dataclass(frozen=True)
class DaySpec:
    """Một ngày làm việc. Ngày OFF thì bốn ô giờ là None.

    `segments` (duoc-CR-761): `None` = ngày theo MẪU LỊCH TUẦN (mọi luật cũ giữ nguyên). Khác `None` = ngày XẾP CA —
    dãy khung giờ TRÒN `(start_hour, end_hour)` đã sắp, 0 ≤ start < end ≤ 24 (24 = hết ngày; dùng SỐ NGUYÊN GIỜ chứ không
    dùng `time` vì `time` không biểu diễn được 24:00). `segments == ()` = ngày NGHỈ do xếp ca. Với ngày xếp ca, `kind` là
    dẫn xuất (OFF / FULL / MORNING / AFTERNOON theo `shift_mask`), `start` = giờ đầu khung đầu, `end` = giờ cuối khung cuối
    (`time.max` khi là 24:00, xem `minutes_of`), hai ô nghỉ trưa luôn None — chỉ để các nơi chỉ cần "giờ vào / giờ ra" đọc được.
    """

    kind: WorkDayKind
    start: time | None = None
    end: time | None = None
    lunch_start: time | None = None
    lunch_end: time | None = None
    segments: tuple[tuple[int, int], ...] | None = None


_OFF = DaySpec(WorkDayKind.OFF)
_FULL = DaySpec(WorkDayKind.FULL, time(8, 0), time(17, 0), time(12, 0), time(13, 0))

#  Index = `date.weekday()` (0 = Thứ hai … 6 = Chủ nhật). DEGO làm cả thứ Bảy.
FALLBACK_WEEK: tuple[DaySpec, ...] = (_FULL,) * 6 + (_OFF,)
#  Ngày làm trọn chuẩn — dùng khi bỏ qua lịch (loại nghỉ `exclude_holiday=False`).
FULL_DAY_SPEC = _FULL
FALLBACK_NAME = "Mặc định hệ thống (T2–T7, 08:00–17:00)"

_MASKS = {WorkDayKind.OFF: 0, WorkDayKind.FULL: AM | PM,
          WorkDayKind.MORNING: AM, WorkDayKind.AFTERNOON: PM}


NOON = 12 * 60          # mốc 12:00 tính bằng phút: khung trước mốc là SÁNG, từ mốc là CHIỀU (Q3, duoc-CR-761)
DAY_MINUTES = 24 * 60   # `time.max` được hiểu là 24:00 (xem `minutes_of`)


def is_shift(spec: DaySpec) -> bool:
    """Ngày này là ngày XẾP CA (kể cả ngày nghỉ do xếp ca)?"""
    return spec.segments is not None


def shift_mask(segments) -> int:
    """Nửa buổi của ngày xếp ca: SÁNG nếu có giờ trước 12:00, CHIỀU nếu có giờ từ 12:00 (khung 10–14 = cả hai)."""
    mask = 0
    for lo, hi in segments:
        if lo < 12:
            mask |= AM
        if hi > 12:
            mask |= PM
    return mask


_SHIFT_KIND = {0: WorkDayKind.OFF, AM: WorkDayKind.MORNING, PM: WorkDayKind.AFTERNOON,
               AM | PM: WorkDayKind.FULL}


def shift_spec(segments: Iterable[tuple[int, int]]) -> DaySpec:
    """Dựng `DaySpec` cho một ngày xếp ca từ các khung `(start_hour, end_hour)` (đã kiểm hợp lệ ở `shift_rules`)."""
    segs = tuple(sorted((int(a), int(b)) for a, b in segments))
    if not segs:
        return DaySpec(WorkDayKind.OFF, segments=())
    last = segs[-1][1]
    return DaySpec(_SHIFT_KIND[shift_mask(segs)], time(segs[0][0]), time.max if last >= 24 else time(last),
                   segments=segs)


def work_mask(spec: DaySpec) -> int:
    """Bitmask nửa buổi phải đi làm: OFF=0, FULL=3, MORNING=1, AFTERNOON=2."""
    if spec.segments is not None:
        return shift_mask(spec.segments)
    return _MASKS.get(spec.kind, 0)


def day_capacity(spec: DaySpec) -> float:
    """Công tối đa của ngày: 1.0 (cả ngày) · 0.5 (nửa ngày) · 0 (nghỉ). Ngày xếp ca có khung = 1.0 (Q3)."""
    if spec.segments is not None:
        return 1.0 if spec.segments else 0.0
    return 0.5 * bin(work_mask(spec)).count("1")


def minutes_of(value: time) -> int:
    """Phút kể từ 00:00; `time.max` (23:59:59.999999) là cách DaySpec ghi 24:00 → 1440."""
    return DAY_MINUTES if value == time.max else value.hour * 60 + value.minute


def worked_hours(spec: DaySpec, start: time, end: time) -> float:
    """Số GIỜ CÔNG trong `[start, end)` của ngày này.

    Cắt theo khung giờ làm của ngày rồi trừ phần chồng giờ nghỉ trưa. Ngày OFF hoặc
    thiếu giờ → 0. Khoảng ngoài khung (nghỉ 19:00) không tính: vắng ngoài giờ làm
    không phải nghỉ phép. Ngày xếp ca: phần giao với TỪNG khung (khe giữa các khung không tính).
    """
    if spec.segments is not None:
        lo, hi = minutes_of(start), minutes_of(end)
        return sum(max(0, min(hi, b * 60) - max(lo, a * 60)) for a, b in spec.segments) / 60.0
    if work_mask(spec) == 0 or spec.start is None or spec.end is None:
        return 0.0
    lo = max(minutes_of(start), minutes_of(spec.start))
    hi = min(minutes_of(end), minutes_of(spec.end))
    if hi <= lo:
        return 0.0
    lunch = 0
    if spec.lunch_start is not None and spec.lunch_end is not None:
        lunch = max(0, min(hi, minutes_of(spec.lunch_end)) - max(lo, minutes_of(spec.lunch_start)))
    return (hi - lo - lunch) / 60.0


def hourly_window(day, from_date, to_date, from_time: time, to_time: time) -> tuple[time, time]:
    """Khoảng giờ `[lo, hi)` của đơn nghỉ THEO GIỜ rơi vào `day` (MỘT luật cho mọi nơi đếm giờ nghỉ nhiều ngày).

    Ngày đầu từ `from_time`, ngày cuối tới `to_time`, ngày giữa trọn ngày (00:00–24:00, `time.max`); đơn một ngày =
    `[from_time, to_time)`. `worked_hours` tự cắt phần ngoài giờ làm / ngoài khung ca, nên không phải biết lịch ở đây.
    """
    return (from_time if day == from_date else time.min), (to_time if day == to_date else time.max)


def day_hours(spec: DaySpec) -> float:
    """Tổng giờ công của một ngày (đã trừ nghỉ trưa); OFF = 0. Ngày xếp ca: tổng độ dài các khung."""
    if spec.segments is not None:
        return float(sum(b - a for a, b in spec.segments))
    if spec.start is None or spec.end is None:
        return 0.0
    return worked_hours(spec, spec.start, spec.end)


def leave_credit(spec: DaySpec, mask: int) -> float:
    """Công TRỪ PHÉP của một ngày khi nghỉ nửa buổi `mask` (AM=1, PM=2) — MỘT công thức cho mọi nơi đếm ngày nghỉ.

    Ngày theo mẫu lịch: 0.5 × số nửa buổi vừa nghỉ vừa phải làm (như cũ). Ngày XẾP CA (Q3, duoc-CR-761): ngày có khung =
    1 ngày công — nghỉ cả ngày (cả hai nửa) trừ 1.0 dù ca chỉ nằm ở một nửa. Nghỉ MỘT nửa:
      * nửa đó chứa TOÀN BỘ giờ ca của ngày (nửa kia không có giờ) → trừ 1.0 (nghỉ hết ca = nghỉ cả ngày công);
      * ca nằm ở cả hai nửa → trừ 0.5;
      * nửa đó không có giờ ca → 0.
    Ngày nghỉ do xếp ca (không khung) = 0.
    """
    if spec.segments is None:
        return 0.5 * bin(mask & work_mask(spec)).count("1")
    mask &= AM | PM
    if not spec.segments or mask == 0:
        return 0.0
    if mask == AM | PM:
        return 1.0
    worked = shift_mask(spec.segments)
    if not worked & mask:
        return 0.0
    return 1.0 if worked == mask else 0.5


def shift_window_mask(spec: DaySpec, lo_min: int, hi_min: int) -> int:
    """Nửa buổi của ngày xếp ca bị khoảng giờ `[lo_min, hi_min)` (tính bằng phút) chạm vào (đơn nghỉ THEO GIỜ)."""
    mask = 0
    for a, b in spec.segments or ():
        if min(hi_min, b * 60, NOON) > max(lo_min, a * 60):
            mask |= AM
        if min(hi_min, b * 60) > max(lo_min, a * 60, NOON):
            mask |= PM
    return mask


def segment_label(segment: tuple[int, int]) -> str:
    """"08:00–10:00" (giờ cuối 24 hiện "24:00")."""
    return f"{segment[0]:02d}:00–{segment[1]:02d}:00"


def weekly_workdays(specs) -> float:
    """Số ngày công một tuần = tổng `day_capacity` (T2–T6 + sáng T7 = 5.5)."""
    return sum(day_capacity(s) for s in specs)
