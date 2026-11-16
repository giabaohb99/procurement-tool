"""KHUÔN TRẢ RA của xếp ca theo ngày (duoc-CR-761) — danh sách ngày xếp ca, và "ca của tôi" (mẫu tuần + ca xếp gộp theo ngày).

`build_days_many` là MỘT chỗ dựng cho thẻ "Ca làm việc" ở Trang cá nhân (`build_my_days` = bản một người) lẫn các công cụ
trợ lý AI: số truy vấn cố định (4 truy vấn lịch + 1 ngày lễ), bất kể bao nhiêu người × bao nhiêu ngày.
"""
from datetime import date, time, timedelta

from sqlalchemy.orm import Session

from app.core.work_schedule_codes import WORK_DAY_KIND_LABELS
from app.modules.employee.model import Employee
from app.modules.leave.holiday_calendar import holiday_names_many

from .day_rules import DaySpec, day_hours, segment_label
from .resolver_many import load_day_plans_many
from .roster_service import shift_cell_info
from .shift_loader import SHIFT_SCHEDULE_NAME, ShiftRecord


def employee_of(db: Session, user) -> Employee | None:
    """Hồ sơ nhân sự gắn với tài khoản đang đăng nhập (None nếu chưa gắn) — hồ sơ CỦA CHÍNH MÌNH nên không cần phạm vi."""
    employee_id = int(getattr(user, "employee_id", 0) or 0)
    return db.get(Employee, employee_id) if employee_id else None


def shift_item(rec: ShiftRecord) -> dict:
    """Một ngày xếp ca cho API quản lý: id, người, ngày, ghi chú, các khung (`start_hour`/`end_hour`/`label`), tổng giờ."""
    info = shift_cell_info(rec)
    return {"id": rec.id, "employee_id": rec.employee_id, "work_date": rec.work_date.isoformat(), "note": rec.note,
            "segments": [{"start_hour": a, "end_hour": b, "label": segment_label((a, b))} for a, b in rec.segments],
            "hours": info["hours"], "is_day_off": info["is_day_off"]}


def _hhmm(value: time) -> str:
    return value.strftime("%H:%M")


def template_labels(spec: DaySpec) -> list[str]:
    """Khung giờ của ngày theo MẪU TUẦN, tách quanh giờ nghỉ trưa: "08:00–12:00", "13:00–17:00"."""
    if spec.start is None or spec.end is None or day_hours(spec) <= 0:
        return []
    if spec.lunch_start and spec.lunch_end and spec.start < spec.lunch_start < spec.lunch_end < spec.end:
        return [f"{_hhmm(spec.start)}–{_hhmm(spec.lunch_start)}", f"{_hhmm(spec.lunch_end)}–{_hhmm(spec.end)}"]
    return [f"{_hhmm(spec.start)}–{_hhmm(spec.end)}"]


def build_days_many(db: Session, employees, from_date: date, to_date: date) -> dict[int, list[dict]]:
    """`{employee_id: [ngày …]}` cho cả danh sách nhân sự: ca xếp riêng thắng mẫu tuần.

    Mỗi ngày: `date`, `weekday`, `is_shift`, `work_kind` (+ `work_kind_label`), `start_time`/`end_time`, `segments` (nhãn
    "HH:MM–HH:MM"), `ranges` ([[giờ đầu, giờ cuối], …] chỉ ngày xếp ca), `hours`, `note`, `is_day_off` (không phải đi làm:
    CN / nghỉ do xếp ca / mẫu nghỉ — KHÔNG tính ngày lễ), `is_holiday`, `holiday_name`, `schedule_name`.
    """
    emps = [e for e in employees if e is not None and e.id]
    if not emps:
        return {}
    plans = load_day_plans_many(db, emps, from_date, to_date)
    holidays = holiday_names_many(db, {int(e.company_id or 0) for e in emps} | {0}, from_date, to_date)
    out: dict[int, list[dict]] = {}
    for emp in emps:
        mine = holidays.get(int(emp.company_id or 0), holidays[0])
        rows = []
        for offset in range((to_date - from_date).days + 1):
            day = from_date + timedelta(days=offset)
            spec, sched_id = plans.at(emp.id, day)
            rec = plans.shift_at(emp.id, day)
            holiday = mine.get(day)
            if rec is not None:
                info = shift_cell_info(rec)
                segments, ranges, hours, note = info["segments"], info["ranges"], info["hours"], info["note"]
                start = f"{rec.segments[0][0]:02d}:00" if rec.segments else None
                end = f"{rec.segments[-1][1]:02d}:00" if rec.segments else None
                name = SHIFT_SCHEDULE_NAME
            else:
                segments, ranges, hours, note = template_labels(spec), [], day_hours(spec), ""
                start, end = (_hhmm(spec.start) if spec.start else None), (_hhmm(spec.end) if spec.end else None)
                name = plans.name_of(sched_id)
            rows.append({"date": day.isoformat(), "weekday": day.weekday(), "is_shift": rec is not None,
                         "work_kind": int(spec.kind), "work_kind_label": WORK_DAY_KIND_LABELS.get(spec.kind, ""),
                         "start_time": start, "end_time": end, "segments": segments, "ranges": ranges,
                         "hours": hours, "note": note, "is_day_off": not segments, "is_holiday": holiday is not None,
                         "holiday_name": holiday or "", "schedule_name": name})
        out[int(emp.id)] = rows
    return out


def build_my_days(db: Session, employee: Employee | None, from_date: date, to_date: date) -> list[dict]:
    """Từng ngày của `[from_date, to_date]` cho MỘT nhân sự — bản một người của `build_days_many` (cùng khuôn)."""
    if employee is None or not employee.id:
        return []
    return build_days_many(db, [employee], from_date, to_date).get(int(employee.id), [])
