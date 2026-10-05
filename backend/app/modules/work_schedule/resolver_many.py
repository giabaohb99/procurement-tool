"""BẢN GOM của bộ phân giải lịch — cho màn «Ai làm / ai nghỉ» (một trang nhân sự × nhiều ngày).

Tách khỏi `resolver.py` cho gọn tệp; dùng lại đúng `_pick` / `_candidate_pairs` / `_load_days`
của bản một người nên hai bản không thể lệch luật thắng.
"""
from collections import defaultdict
from datetime import date

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.work_schedule_codes import WorkScheduleLevel

from .day_rules import FALLBACK_NAME, FALLBACK_WEEK, DaySpec
from .model import WorkSchedule, WorkScheduleAssignment
from .resolver import _candidate_pairs, _load_days, _pick


class DayPlansMany:
    """Kết quả `load_day_plans_many` — tra thuần bộ nhớ, không chạm DB nữa."""

    def __init__(self, by_emp: dict, weeks: dict, names: dict[int, str]):
        self._by_emp, self._weeks, self.names = by_emp, weeks, names

    def at(self, employee_id: int, day: date) -> tuple[DaySpec, int]:
        """`(DaySpec, schedule_id)` của nhân sự vào `day`; fallback → `schedule_id = 0`."""
        hit = _pick(self._by_emp.get(employee_id, {}), day)
        if hit is None:
            return FALLBACK_WEEK[day.weekday()], 0
        spec = self._weeks.get(hit.schedule_id, {}).get(day.weekday())
        if spec is None:
            return FALLBACK_WEEK[day.weekday()], 0
        return spec, hit.schedule_id

    def name_of(self, schedule_id: int) -> str:
        return self.names.get(schedule_id, FALLBACK_NAME) if schedule_id else FALLBACK_NAME


def load_day_plans_many(db: Session, employees, from_date: date, to_date: date) -> DayPlansMany:
    """BẢN GOM của `load_day_plans` cho cả một trang nhân sự — **3 truy vấn cố định**
    (dòng gán · ngày của các mẫu · tên mẫu) bất kể bao nhiêu người × bao nhiêu ngày.

    `employees`: các đối tượng có `id`, `department_id`, `company_id`. Cùng luật thắng
    `_pick` với bản một người nên hai bản không thể lệch nhau.
    """
    emps = list(employees)
    companies = {int(e.company_id or 0) for e in emps} - {0}
    depts = {int(e.department_id or 0) for e in emps} - {0}
    ids = {int(e.id) for e in emps}
    conds = [and_(WorkScheduleAssignment.target_level == int(WorkScheduleLevel.SYSTEM),
                  WorkScheduleAssignment.target_id == 0)]
    for level, targets in ((WorkScheduleLevel.COMPANY, companies),
                           (WorkScheduleLevel.DEPARTMENT, depts),
                           (WorkScheduleLevel.EMPLOYEE, ids)):
        if targets:
            conds.append(and_(WorkScheduleAssignment.target_level == int(level),
                              WorkScheduleAssignment.target_id.in_(targets)))
    rows = (db.query(WorkScheduleAssignment)
            .filter(or_(*conds), WorkScheduleAssignment.effective_from <= to_date,
                    or_(WorkScheduleAssignment.effective_to.is_(None),
                        WorkScheduleAssignment.effective_to >= from_date))
            .all()) if emps else []
    index: dict[tuple[int, int], list[WorkScheduleAssignment]] = defaultdict(list)
    for a in rows:
        index[(a.target_level, a.target_id)].append(a)
    by_emp = {}
    for e in emps:
        by_level = {}
        for level, target in _candidate_pairs(int(e.id), int(e.department_id or 0),
                                              int(e.company_id or 0)):
            if (level, target) in index:
                by_level[level] = index[(level, target)]
        by_emp[int(e.id)] = by_level
    sched_ids = {a.schedule_id for a in rows}
    names = ({r.id: r.name for r in db.query(WorkSchedule.id, WorkSchedule.name)
              .filter(WorkSchedule.id.in_(sched_ids)).all()} if sched_ids else {})
    return DayPlansMany(by_emp, _load_days(db, sched_ids), names)
