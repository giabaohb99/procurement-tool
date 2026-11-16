"""NẠP CA XẾP THEO NGÀY (duoc-CR-761) — MỘT truy vấn cho cả khoảng ngày × nhiều nhân sự.

Tách khỏi `resolver.py` / `resolver_many.py` để hai bản (một người / nhiều người) dùng chung đúng một câu truy vấn nên
không thể lệch nhau. Ngày xếp ca THẮNG mọi cấp gán lịch; ngày có dòng mà không khung = nghỉ do xếp ca.
"""
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from .day_rules import DaySpec, shift_spec
from .model import WorkShiftDay, WorkShiftSegment


SHIFT_SCHEDULE_NAME = "Xếp ca theo ngày"   # tên "lịch" hiện cho ngày xếp ca (không thuộc mẫu lịch nào)


@dataclass(frozen=True)
class ShiftRecord:
    """Một ngày xếp ca đã nạp: id dòng, ghi chú, các khung `(start_hour, end_hour)` đã sắp."""

    id: int
    employee_id: int
    work_date: date
    note: str
    segments: tuple[tuple[int, int], ...]


def load_shift_records(db: Session, employee_ids, from_date: date, to_date: date) -> dict[tuple[int, date], ShiftRecord]:
    """`{(employee_id, ngày): ShiftRecord}` — 1 truy vấn (OUTER JOIN khung: ngày không khung vẫn ra một dòng)."""
    ids = {int(i) for i in employee_ids if i}
    if not ids:
        return {}
    rows = (db.query(WorkShiftDay.id, WorkShiftDay.employee_id, WorkShiftDay.work_date, WorkShiftDay.note,
                     WorkShiftSegment.start_hour, WorkShiftSegment.end_hour)
            .outerjoin(WorkShiftSegment, WorkShiftSegment.shift_day_id == WorkShiftDay.id)
            .filter(WorkShiftDay.employee_id.in_(ids), WorkShiftDay.work_date >= from_date,
                    WorkShiftDay.work_date <= to_date)
            .order_by(WorkShiftDay.id, WorkShiftSegment.sort_order, WorkShiftSegment.start_hour).all())
    heads: dict[int, tuple] = {}
    segs: dict[int, list[tuple[int, int]]] = {}
    for day_id, emp_id, work_date, note, start, end in rows:
        heads[day_id] = (emp_id, work_date, note or "")
        segs.setdefault(day_id, [])
        if start is not None:
            segs[day_id].append((int(start), int(end)))
    return {(h[0], h[1]): ShiftRecord(day_id, h[0], h[1], h[2], tuple(sorted(segs[day_id])))
            for day_id, h in heads.items()}


def load_shift_specs(db: Session, employee_ids, from_date: date, to_date: date) -> dict[tuple[int, date], DaySpec]:
    """`{(employee_id, ngày): DaySpec}` của các ngày xếp ca — cho bộ phân giải lịch."""
    return {key: shift_spec(rec.segments) for key, rec in load_shift_records(db, employee_ids, from_date, to_date).items()}
