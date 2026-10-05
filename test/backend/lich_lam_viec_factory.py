"""Khung dựng dữ liệu Lịch làm việc cho các bài kiểm — không phải bài kiểm (tên không bắt đầu `test_`)."""
from datetime import date, time

from app.core.work_schedule_codes import WorkDayKind, WorkScheduleLevel
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.work_schedule.day_rules import DaySpec
from app.modules.work_schedule.model import (WorkSchedule, WorkScheduleAssignment,
                                             WorkScheduleDay)

OFF = DaySpec(WorkDayKind.OFF)
FULL = DaySpec(WorkDayKind.FULL, time(8, 0), time(17, 0), time(12, 0), time(13, 0))
FULL_7H = DaySpec(WorkDayKind.FULL, time(8, 0), time(16, 0), time(12, 0), time(13, 0))
SAT_AM = DaySpec(WorkDayKind.MORNING, time(8, 0), time(12, 0))
SAT_PM = DaySpec(WorkDayKind.AFTERNOON, time(13, 0), time(17, 0))

#  Mốc ngày cố định: 05/01/2026 là thứ Hai (không phụ thuộc "hôm nay").
MON = date(2026, 1, 5)
SAT = date(2026, 1, 10)
SUN = date(2026, 1, 11)


def week_t2_t6_sat_am() -> list[DaySpec]:
    """T2–T6 cả ngày, T7 sáng, CN nghỉ — tuần 5.5 công."""
    return [FULL] * 5 + [SAT_AM, OFF]


def make_schedule(db, name: str, specs: list[DaySpec], is_active: bool = True) -> WorkSchedule:
    sched = WorkSchedule(name=name, note="", is_active=is_active)
    db.add(sched)
    db.flush()
    for wd, s in enumerate(specs):
        db.add(WorkScheduleDay(schedule_id=sched.id, weekday=wd, day_kind=int(s.kind),
                               start_time=s.start, end_time=s.end,
                               lunch_start=s.lunch_start, lunch_end=s.lunch_end))
    db.flush()
    return sched


def assign(db, level: WorkScheduleLevel, target_id: int, schedule_id: int,
           start: date, end: date | None = None) -> WorkScheduleAssignment:
    row = WorkScheduleAssignment(target_level=int(level), target_id=target_id,
                                 schedule_id=schedule_id, effective_from=start,
                                 effective_to=end, note="")
    db.add(row)
    db.flush()
    return row


def make_world(db, code: str = "NV001"):
    """Pháp nhân + phòng ban + nhân sự thuộc cả hai. Trả (company, dept, employee)."""
    company = Company(name=f"Cty {code}", code=f"C{code}", is_active=True)
    db.add(company)
    db.flush()
    dept = Department(code=f"D{code}", name=f"Phòng {code}", company_id=company.id, is_active=True)
    db.add(dept)
    db.flush()
    emp = Employee(code=code, full_name=f"Người {code}", company_id=company.id,
                   department_id=dept.id, is_active=True)
    db.add(emp)
    db.flush()
    return company, dept, emp


def count_queries(db, fn):
    """Chạy `fn()`, trả (kết quả, danh sách câu SQL đã gửi)."""
    from sqlalchemy import event
    seen: list[str] = []

    def _on(conn, cursor, statement, *a):
        seen.append(statement)

    event.listen(db.get_bind(), "before_cursor_execute", _on)
    try:
        result = fn()
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", _on)
    return result, seen
