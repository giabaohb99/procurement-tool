"""Kỳ báo cáo + kỳ so sánh — nền mọi `/summary` kiểu Haravan (P01 khung báo cáo).

`parse_period` đọc `preset/date_from/date_to/compare` -> `Period` đã chốt đủ ngày (kỳ này +
kỳ so sánh) + độ hạt biểu đồ, tính theo giờ VN (container chạy UTC — xem `to_local_date`).
Hàm thuần, không đụng DB, test bằng cách truyền `today` giả.
So sánh (chốt 28/09/2026, `plan.md` mục "Quyết định đã chốt"): `previous` + preset LỊCH lùi
ĐÚNG một đơn vị lịch, cắt về cuối tháng nếu ngắn hơn (31/03→28-29/02); `previous` + preset
CUỘN lùi cùng số ngày liền trước; `year` trừ đúng 1 năm (29/02→28/02), áp cho MỌI preset.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Mapping

from fastapi import HTTPException
from sqlalchemy import and_
from app.core.export_xlsx import VN_OFFSET

PRESET_KEYS = ("today", "yesterday", "last_7_days", "last_30_days", "this_month",
               "last_month", "this_quarter", "this_year", "last_year", "custom")
COMPARE_MODES = ("previous", "year", "none")
MAX_RANGE_DAYS = 1096  # ~3 năm kể cả năm nhuận — chặn kéo cả kỳ khổng lồ vào Python
#  L2 — dải năm hợp lý cho preset `custom`, chặn `0001-01-01`/`9999-12-31` lộ 500 (Overflow/
#  ValueError ở `_shift_years`/`range_filter`) thay vì 422. Hẹp hơn `MIN/MAX_PROFILE_YEAR` của
#  hồ sơ nhân sự vì đây là ngày NGHIỆP VỤ, không phải ngày sinh.
MIN_REPORT_YEAR = 2000
MAX_REPORT_YEAR = 2100

_CALENDAR_UNIT_MONTHS = {"this_month": 1, "last_month": 1, "this_quarter": 3,   # preset LỊCH:
                          "this_year": 12, "last_year": 12}                     # lùi theo ĐƠN VỊ LỊCH


def _shift_months(d: date, months: int) -> date:
    """Lùi `d` đúng `months` tháng, giữ SỐ NGÀY, cắt về ngày cuối tháng đích nếu ngắn hơn."""
    total = d.month - 1 - months
    year, month = d.year + total // 12, total % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def _shift_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year - years)
    except ValueError:
        return date(d.year - years, 2, 28)  # 29/02 -> năm đích không nhuận


def _bounds_for_preset(preset: str, today: date) -> tuple[date, date]:
    """Biên [từ, đến] của một preset — "Tháng này/Quý này/Năm nay" chạy TỚI HÔM NAY."""
    if preset in ("today", "yesterday"):
        d = today - timedelta(days=1) if preset == "yesterday" else today
        return d, d
    if preset == "last_7_days":
        return today - timedelta(days=6), today
    if preset == "last_30_days":
        return today - timedelta(days=29), today
    if preset == "this_month":
        return today.replace(day=1), today
    if preset == "last_month":
        last_end = today.replace(day=1) - timedelta(days=1)
        return last_end.replace(day=1), last_end
    if preset == "this_quarter":
        q_month = (today.month - 1) // 3 * 3 + 1
        return date(today.year, q_month, 1), today
    if preset == "this_year":
        return date(today.year, 1, 1), today
    return date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)  # last_year


def resolve_granularity(d_from: date, d_to: date) -> str:
    """≤31 ngày → ngày; ≤92 → tuần; còn lại → tháng (ngưỡng chốt trong plan)."""
    days = (d_to - d_from).days + 1
    if days <= 31:
        return "day"
    if days <= 92:
        return "week"
    return "month"


def bucket_axis(d_from: date, d_to: date, granularity: str) -> list[dict]:
    """Danh sách mốc ĐỦ (mốc rỗng vẫn có mặt = 0) — trục cho biểu đồ xu hướng."""
    if granularity == "day":
        n = (d_to - d_from).days
        return [{"key": (d_from + timedelta(days=i)).isoformat(),
                 "label": (d_from + timedelta(days=i)).strftime("%d/%m")} for i in range(n + 1)]
    if granularity == "week":
        out, monday = [], d_from - timedelta(days=d_from.weekday())  # tuần bắt đầu thứ Hai
        while monday <= d_to:
            start, end = max(monday, d_from), min(monday + timedelta(days=6), d_to)  # cắt theo biên kỳ
            out.append({"key": monday.isoformat(), "label": f"{start:%d/%m}-{end:%d/%m}"})
            monday += timedelta(days=7)
        return out
    out, y, m = [], d_from.year, d_from.month  # month
    while date(y, m, 1) <= d_to:
        out.append({"key": f"{y:04d}-{m:02d}", "label": f"{m:02d}/{y:04d}"})
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def bucket_of(d: date, granularity: str) -> str:
    """Khóa mốc của một ngày — PHẢI khớp key do `bucket_axis` sinh ra, dùng để gom hàng."""
    if granularity == "day":
        return d.isoformat()
    if granularity == "week":
        return (d - timedelta(days=d.weekday())).isoformat()
    return f"{d.year:04d}-{d.month:02d}"


def to_local_date(value) -> date | None:
    """`str 'YYYY-MM-DD'/ISO | date | datetime(UTC)` -> `date` giờ VN. Giá trị lạ -> None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return (value + VN_OFFSET).date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def range_filter(col, kind: str, d_from: date, d_to: date):
    """Điều kiện SQL cận NỬA MỞ `[d_from, d_to]` giờ VN — chỉ dùng `>=`/`<` nên chạy giống
    nhau trên SQLite (test) và MySQL (prod). `kind`: 'str' (chuỗi 'YYYY-MM-DD'/ISO) ·
    'date' (cột Date) · 'datetime_utc' (cột DateTime UTC — quy cận bằng trừ `VN_OFFSET`).
    """
    upper = d_to + timedelta(days=1)
    if kind == "str":
        return and_(col >= d_from.isoformat(), col < upper.isoformat())
    if kind == "date":
        return and_(col >= d_from, col < upper)
    if kind == "datetime_utc":
        lo = datetime.combine(d_from, time.min) - VN_OFFSET
        hi = datetime.combine(upper, time.min) - VN_OFFSET
        return and_(col >= lo, col < hi)
    raise ValueError(f"range_filter: kind không hỗ trợ: {kind}")


@dataclass(frozen=True)
class Period:
    preset: str
    date_from: date
    date_to: date
    compare: str
    compare_from: date | None
    compare_to: date | None
    granularity: str

    def as_dict(self) -> dict:
        return {"preset": self.preset, "date_from": self.date_from.isoformat(),
                "date_to": self.date_to.isoformat(), "compare": self.compare,
                "compare_from": self.compare_from.isoformat() if self.compare_from else None,
                "compare_to": self.compare_to.isoformat() if self.compare_to else None,
                "granularity": self.granularity}


def _parse_date_param(value, name: str) -> date:
    if not value:
        raise HTTPException(422, f"Thiếu tham số {name} (bắt buộc khi preset=custom)")
    try:
        d = date.fromisoformat(str(value)[:10])
    except ValueError:
        raise HTTPException(422, f"{name} sai định dạng, cần YYYY-MM-DD")
    if not (MIN_REPORT_YEAR <= d.year <= MAX_REPORT_YEAR):
        raise HTTPException(422, f"{name} phải trong khoảng năm {MIN_REPORT_YEAR}-{MAX_REPORT_YEAR}")
    return d


def parse_period(params: Mapping, today: date | None = None) -> Period:
    """Query params -> `Period` đã chốt đủ ngày. Mặc định: preset=`this_month`, compare=`previous`.
    `today` truyền tay để test cố định ngày, bỏ trống thì lấy giờ hệ thống quy sang giờ VN.
    """
    today = today or (datetime.utcnow() + VN_OFFSET).date()
    preset = (params.get("preset") or "this_month").strip()
    if preset not in PRESET_KEYS:
        raise HTTPException(422, f"Kỳ báo cáo không hợp lệ: {preset}")
    compare = (params.get("compare") or "previous").strip()
    if compare not in COMPARE_MODES:
        raise HTTPException(422, f"Kiểu so sánh không hợp lệ: {compare}")
    if preset == "custom":
        d_from = _parse_date_param(params.get("date_from"), "date_from")
        d_to = _parse_date_param(params.get("date_to"), "date_to")
    else:
        d_from, d_to = _bounds_for_preset(preset, today)
    if d_to < d_from:
        raise HTTPException(422, "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu")
    if (d_to - d_from).days + 1 > MAX_RANGE_DAYS:
        raise HTTPException(422, f"Khoảng thời gian tối đa {MAX_RANGE_DAYS} ngày")

    if compare == "none":
        cmp_from = cmp_to = None
    elif compare == "year":
        cmp_from, cmp_to = _shift_years(d_from, 1), _shift_years(d_to, 1)
    elif preset in _CALENDAR_UNIT_MONTHS:  # compare == "previous", preset LỊCH
        months = _CALENDAR_UNIT_MONTHS[preset]
        cmp_from, cmp_to = _shift_months(d_from, months), _shift_months(d_to, months)
    else:  # compare == "previous", preset CUỘN/custom — cùng số ngày ngay trước
        n = (d_to - d_from).days + 1
        cmp_to = d_from - timedelta(days=1)
        cmp_from = cmp_to - timedelta(days=n - 1)

    return Period(preset, d_from, d_to, compare, cmp_from, cmp_to, resolve_granularity(d_from, d_to))
