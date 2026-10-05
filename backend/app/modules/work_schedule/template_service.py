"""Nghiệp vụ MẪU LỊCH TUẦN: đọc (gom truy vấn), tạo, sửa trọn 7 dòng, xóa có chốt.

Mẫu ghi KÈM 7 dòng ngày nên viết tay thay vì `make_crud_router`. Hình dạng trả về
vẫn là `{total, items}` để màn CRUD khai báo dùng được nguyên.
"""
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.crud import commit_or_conflict
from app.core.work_schedule_codes import WorkDayKind

from .day_rules import weekly_workdays
from .model import WorkSchedule, WorkScheduleAssignment, WorkScheduleDay
from .resolver import row_to_spec, spec_to_day_out
from .template_schema import DayIn, ScheduleCreate, ScheduleUpdate

ENTITY = "work_schedule"


def assignment_counts(db: Session, schedule_ids: list[int]) -> dict[int, int]:
    """Số dòng gán của từng mẫu — GOM 1 truy vấn."""
    if not schedule_ids:
        return {}
    rows = (db.query(WorkScheduleAssignment.schedule_id, func.count(WorkScheduleAssignment.id))
            .filter(WorkScheduleAssignment.schedule_id.in_(schedule_ids))
            .group_by(WorkScheduleAssignment.schedule_id).all())
    return {sid: n for sid, n in rows}


def serialize_many(db: Session, schedules: list[WorkSchedule]) -> list[dict]:
    """Chuyển nhiều mẫu ra JSON bằng đúng 2 truy vấn (ngày + đếm gán)."""
    ids = [s.id for s in schedules]
    days: dict[int, dict[int, object]] = defaultdict(dict)
    if ids:
        for r in db.query(WorkScheduleDay).filter(WorkScheduleDay.schedule_id.in_(ids)).all():
            days[r.schedule_id][r.weekday] = row_to_spec(r)
    counts = assignment_counts(db, ids)
    out = []
    for s in schedules:
        week = days.get(s.id, {})
        specs = [week[i] for i in sorted(week)]
        out.append({
            "id": s.id, "name": s.name, "note": s.note or "", "is_active": bool(s.is_active),
            "days": [spec_to_day_out(i, week[i]) for i in sorted(week)],
            "weekly_workdays": weekly_workdays(specs),
            "assignment_count": counts.get(s.id, 0),
            "created_at": s.created_at, "updated_at": s.updated_at,
        })
    return out


def serialize_one(db: Session, schedule: WorkSchedule) -> dict:
    return serialize_many(db, [schedule])[0]


def _check_name_free(db: Session, name: str, exclude_id: int = 0) -> None:
    q = db.query(WorkSchedule).filter(WorkSchedule.name == name)
    if exclude_id:
        q = q.filter(WorkSchedule.id != exclude_id)
    if q.first():
        raise HTTPException(400, f"Đã có mẫu lịch tên «{name}»")


def _day_row(schedule_id: int, d: DayIn, user_id: int) -> WorkScheduleDay:
    return WorkScheduleDay(
        schedule_id=schedule_id, weekday=d.weekday, day_kind=int(WorkDayKind(d.day_kind)),
        start_time=d.start_time, end_time=d.end_time,
        lunch_start=d.lunch_start, lunch_end=d.lunch_end,
        created_by=user_id, updated_by=user_id)


def create_schedule(db: Session, data: ScheduleCreate, user) -> WorkSchedule:
    _check_name_free(db, data.name)
    obj = WorkSchedule(name=data.name, note=data.note, is_active=data.is_active,
                       created_by=user.id, updated_by=user.id)
    db.add(obj)
    db.flush()
    db.add_all([_day_row(obj.id, d, user.id) for d in data.days])
    commit_or_conflict(db, "Mẫu lịch bị trùng tên")
    db.refresh(obj)
    record(db, user.id, ENTITY, obj.id, "create", f"Tạo mẫu lịch «{obj.name}»")
    return obj


def update_schedule(db: Session, obj: WorkSchedule, data: ScheduleUpdate, user) -> WorkSchedule:
    values = data.model_dump(exclude_unset=True, exclude={"days"})
    if values.get("name") is None:
        values.pop("name", None)
    for key in ("note", "is_active"):
        if key in values and values[key] is None:
            values.pop(key)
    if "name" in values:
        _check_name_free(db, values["name"], obj.id)
    for k, v in values.items():
        setattr(obj, k, v)
    obj.updated_by = user.id
    if data.days is not None:
        #  Thay TRỌN 7 dòng: xóa + flush trước khi chèn để không đụng UNIQUE (schedule, weekday).
        db.query(WorkScheduleDay).filter(WorkScheduleDay.schedule_id == obj.id).delete()
        db.flush()
        db.add_all([_day_row(obj.id, d, user.id) for d in data.days])
    commit_or_conflict(db, "Mẫu lịch bị trùng tên")
    db.refresh(obj)
    record(db, user.id, ENTITY, obj.id, "update", f"Sửa mẫu lịch «{obj.name}»")
    return obj


def delete_schedule(db: Session, obj: WorkSchedule, user) -> None:
    #  Khóa dòng mẫu trước khi đếm: tạo gán (`_check_schedule`) cũng khóa dòng này (bug L4).
    db.query(WorkSchedule).filter(WorkSchedule.id == obj.id).with_for_update().first()
    used = assignment_counts(db, [obj.id]).get(obj.id, 0)
    if used:
        raise HTTPException(
            400, f"«{obj.name}» đang được gán {used} lần nên không xóa được. "
                 "Bỏ tick «Đang dùng» để ẩn khỏi ô chọn thay vì xóa.")
    name, oid = obj.name, obj.id
    db.query(WorkScheduleDay).filter(WorkScheduleDay.schedule_id == oid).delete()
    db.delete(obj)
    db.commit()
    record(db, user.id, ENTITY, oid, "delete", f"Xóa mẫu lịch «{name}»")
