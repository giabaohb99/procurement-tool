"""BỘ PHÂN GIẢI LỊCH — «ngày D của nhân sự X làm theo lịch nào?».

Thứ tự thắng: NHÂN SỰ > PHÒNG BAN > PHÁP NHÂN > HỆ THỐNG > `FALLBACK_WEEK`
(`LEVEL_PRECEDENCE`). Phòng ban/pháp nhân là phòng CHÍNH và pháp nhân HIỆN TẠI
của hồ sơ (chốt 05/10/2026) — không tra quá trình công tác, phòng kiêm nhiệm bỏ qua.

⚠️ Số truy vấn CỐ ĐỊNH (tối đa 2: dòng gán + ngày của các mẫu được trỏ) bất kể
khoảng 1 hay 400 ngày — báo cáo/form gọi liên tục, không được N+1.
"""
import logging
from collections import defaultdict
from datetime import date, time
from typing import Callable

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.work_schedule_codes import (LEVEL_PRECEDENCE, WORK_DAY_KIND_LABELS,
                                          WORK_SCHEDULE_LEVEL_LABELS, WorkDayKind,
                                          WorkScheduleLevel)

from .day_rules import FALLBACK_NAME, FALLBACK_WEEK, DaySpec, weekly_workdays
from .model import WorkSchedule, WorkScheduleAssignment, WorkScheduleDay

logger = logging.getLogger("app.work_schedule")


def _candidate_pairs(employee_id: int, department_id: int, company_id: int) -> list[tuple[int, int]]:
    """Cặp (cấp, đối tượng) cần hỏi. KHÔNG BAO GIỜ hỏi `(cấp ≠ SYSTEM, 0)`: nhân sự chưa
    khai pháp nhân sẽ dính dòng rác `(COMPANY, 0)` nếu có ai cài tay vào DB."""
    pairs = [(int(WorkScheduleLevel.SYSTEM), 0)]
    for level, target in ((WorkScheduleLevel.COMPANY, company_id),
                          (WorkScheduleLevel.DEPARTMENT, department_id),
                          (WorkScheduleLevel.EMPLOYEE, employee_id)):
        if target and target > 0:
            pairs.append((int(level), int(target)))
    return pairs


def _load_rows(db: Session, pairs, from_date: date, to_date: date) -> list[WorkScheduleAssignment]:
    """Truy vấn 1 — mọi dòng gán khớp một cặp và giao với khoảng đang hỏi."""
    match = or_(*[and_(WorkScheduleAssignment.target_level == lv,
                       WorkScheduleAssignment.target_id == tid) for lv, tid in pairs])
    return (db.query(WorkScheduleAssignment)
            .filter(match, WorkScheduleAssignment.effective_from <= to_date,
                    or_(WorkScheduleAssignment.effective_to.is_(None),
                        WorkScheduleAssignment.effective_to >= from_date))
            .all())


def _load_days(db: Session, schedule_ids: set[int]) -> dict[int, dict[int, DaySpec]]:
    """Truy vấn 2 — `{schedule_id: {weekday: DaySpec}}`."""
    out: dict[int, dict[int, DaySpec]] = defaultdict(dict)
    if not schedule_ids:
        return out
    for r in db.query(WorkScheduleDay).filter(WorkScheduleDay.schedule_id.in_(schedule_ids)).all():
        out[r.schedule_id][r.weekday] = row_to_spec(r)
    return out


def row_to_spec(r: WorkScheduleDay) -> DaySpec:
    try:
        kind = WorkDayKind(r.day_kind)
    except ValueError:
        logger.warning("Mẫu lịch %s thứ %s có day_kind lạ %s — coi như nghỉ",
                       r.schedule_id, r.weekday, r.day_kind)
        kind = WorkDayKind.OFF
    return DaySpec(kind, r.start_time, r.end_time, r.lunch_start, r.lunch_end)


def _pick(by_level: dict[int, list[WorkScheduleAssignment]], day: date):
    """Dòng gán thắng cho `day`: cấp hẹp nhất; hòa → `effective_from` muộn, rồi `id` lớn."""
    for level in LEVEL_PRECEDENCE:
        hits = [a for a in by_level.get(int(level), ())
                if a.effective_from <= day and (a.effective_to is None or a.effective_to >= day)]
        if hits:
            return max(hits, key=lambda a: (a.effective_from, a.id))
    return None


def _group(rows) -> dict[int, list[WorkScheduleAssignment]]:
    by_level: dict[int, list[WorkScheduleAssignment]] = defaultdict(list)
    for a in rows:
        by_level[a.target_level].append(a)
    return by_level


def load_day_plans(db: Session, *, employee_id: int = 0, department_id: int = 0,
                   company_id: int = 0, from_date: date, to_date: date) -> Callable[[date], DaySpec]:
    """Nạp lịch cho cả khoảng rồi trả hàm `plan(day) -> DaySpec` thuần bộ nhớ."""
    rows = _load_rows(db, _candidate_pairs(employee_id, department_id, company_id),
                      from_date, to_date)
    by_level = _group(rows)
    weeks = _load_days(db, {a.schedule_id for a in rows})

    def plan(day: date) -> DaySpec:
        hit = _pick(by_level, day)
        if hit is None:
            return FALLBACK_WEEK[day.weekday()]
        spec = weeks.get(hit.schedule_id, {}).get(day.weekday())
        if spec is None:
            logger.warning("Mẫu lịch %s thiếu thứ %s — dùng lịch mặc định ngày đó",
                           hit.schedule_id, day.weekday())
            return FALLBACK_WEEK[day.weekday()]
        return spec

    return plan


def schedule_name_on(db: Session, employee, on_date: date) -> str:
    """Tên mẫu lịch áp cho nhân sự vào một ngày (fallback → `FALLBACK_NAME`)."""
    hit = _winner(db, employee, on_date)
    if hit is None:
        return FALLBACK_NAME
    sched = db.get(WorkSchedule, hit.schedule_id)
    return sched.name if sched else FALLBACK_NAME


def _winner(db: Session, employee, on_date: date):
    pairs = _candidate_pairs(int(employee.id or 0), int(employee.department_id or 0),
                             int(employee.company_id or 0))
    return _pick(_group(_load_rows(db, pairs, on_date, on_date)), on_date)


def _hhmm(v: time | None) -> str | None:
    return v.strftime("%H:%M") if v else None


def spec_to_day_out(weekday: int, spec: DaySpec) -> dict:
    return {"weekday": weekday, "day_kind": int(spec.kind),
            "day_kind_label": WORK_DAY_KIND_LABELS.get(spec.kind, ""),
            "start_time": _hhmm(spec.start), "end_time": _hhmm(spec.end),
            "lunch_start": _hhmm(spec.lunch_start), "lunch_end": _hhmm(spec.lunch_end)}


def effective_for_employee(db: Session, employee, on_date: date) -> dict:
    """Lịch hiệu lực của một nhân sự vào `on_date` — cho thẻ «Lịch làm việc» ở hồ sơ."""
    hit = _winner(db, employee, on_date)
    sched = db.get(WorkSchedule, hit.schedule_id) if hit else None
    if hit is None or sched is None:
        specs = list(FALLBACK_WEEK)
        return {"schedule_id": 0, "schedule_name": FALLBACK_NAME, "is_fallback": True,
                "days": [spec_to_day_out(i, s) for i, s in enumerate(specs)],
                "weekly_workdays": weekly_workdays(specs), "level": 0, "level_label": "",
                "target_name": "", "assignment_id": 0,
                "effective_from": None, "effective_to": None}
    week = _load_days(db, {sched.id})[sched.id]
    specs = [week.get(i, FALLBACK_WEEK[i]) for i in range(7)]
    from .assignment_service import target_names
    names = target_names(db, [hit])
    level = WorkScheduleLevel(hit.target_level)
    return {"schedule_id": sched.id, "schedule_name": sched.name, "is_fallback": False,
            "days": [spec_to_day_out(i, s) for i, s in enumerate(specs)],
            "weekly_workdays": weekly_workdays(specs), "level": int(level),
            "level_label": WORK_SCHEDULE_LEVEL_LABELS[level],
            "target_name": names.get((hit.target_level, hit.target_id), ""),
            "assignment_id": hit.id, "effective_from": hit.effective_from,
            "effective_to": hit.effective_to}
