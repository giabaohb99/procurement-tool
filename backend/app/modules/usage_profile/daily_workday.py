"""Lịch của một người trong một ngày + «ngoài giờ» (thuần, nhận DaySpec) — duoc-CR-641, phase 02.

`work_capacity`/`leave_days` là mẫu số của «ngày làm việc ròng»: công của ngày theo Lịch làm việc (mặc định
T2–T7 08–17), 0 nếu ngày lễ/nghỉ; `leave_days` chỉ tính nửa buổi vừa nghỉ (đơn ĐÃ DUYỆT) vừa phải làm.
"""
from dataclasses import dataclass
from datetime import date, datetime

from app.modules.work_schedule.day_rules import DaySpec, day_capacity, work_mask
from app.modules.work_schedule.roster_leave import leave_mask_on

from .daily_window import minute_of_day


@dataclass(frozen=True)
class DayCalendar:
    spec: DaySpec
    is_workday: bool
    is_holiday: bool
    work_capacity: float
    leave_days: float


def build_calendar(plans, holidays: dict, leaves_by_emp: dict, employee_id: int, company_id: int,
                   day: date) -> DayCalendar:
    spec, _ = plans.at(int(employee_id or 0), day)
    company_id = int(company_id or 0)
    is_holiday = day in holidays.get(company_id, holidays.get(0, {}))
    capacity = day_capacity(spec)
    is_workday = capacity > 0 and not is_holiday
    leave_days = 0.0
    if is_workday:
        mask = 0
        for req in leaves_by_emp.get(int(employee_id or 0), ()):
            mask |= leave_mask_on(req, day, spec)
        leave_days = min(capacity, 0.5 * bin(mask & work_mask(spec)).count("1"))
    return DayCalendar(spec, is_workday, is_holiday, capacity if is_workday else 0.0, leave_days)


def is_offhours(cal: DayCalendar, moment_utc: datetime) -> bool:
    """Lượt ghi lúc `moment_utc` có NGOÀI giờ làm của người này không (giờ trưa tính trong giờ)."""
    if not cal.is_workday or cal.spec.start is None or cal.spec.end is None:
        return True
    m = minute_of_day(moment_utc)
    start = cal.spec.start.hour * 60 + cal.spec.start.minute
    end = cal.spec.end.hour * 60 + cal.spec.end.minute
    return m < start or m >= end
