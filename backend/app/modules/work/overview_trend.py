"""Phân hệ Dự án — DIỄN BIẾN THEO THỜI GIAN của MỘT dự án hoặc MỘT người trên màn Tổng quan (duoc-CR-782).

Anh Được hỏi: biểu đồ có theo dõi được từng dự án, hiệu suất từng người không. Các biểu đồ khác của màn là ảnh chụp tại
thời điểm này; khối này trả lời "dạo này dự án / người đó ra sao": mỗi ngày (kỳ ≤ 31 ngày) hoặc mỗi tuần (kỳ dài hơn)
có bao nhiêu việc MỚI GIAO và bao nhiêu việc XONG — tách xong đúng hạn / trễ hạn / không đặt hạn.

Số truy vấn CỐ ĐỊNH = 2 (gom theo ngày giờ VN ở SQL), không theo số ngày hay số việc; chia tuần làm ở Python.

Phạm vi: dự án phải nằm trong tập dự án màn Tổng quan được đếm (`overview_list_ids`), không thì trả chuỗi rỗng — gõ id
dự án khác vào URL không lộ được gì. Người: chỉ đếm việc họ PHỤ TRÁCH trong các dự án đó (người theo dõi không tính).
"""
from datetime import date, datetime, timedelta

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.modules.work.model import WorkAssigneeKind, WorkTaskStatus
from app.modules.work.report_sql_date import vn_date_str
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

KIND_PROJECT = "project"
KIND_PERSON = "person"
#  Kỳ dài hơn chừng này ngày thì gom theo TUẦN: 90 cột ngày quá mảnh để đọc.
DAILY_MAX_DAYS = 31


def _base(db: Session, list_ids: set[int], kind: str, entity_id: int):
    q = db.query(WorkTask).filter(WorkTask.parent_id.is_(None), WorkTask.deleted_at.is_(None))
    if kind == KIND_PROJECT:
        return q.filter(WorkTask.list_id == entity_id)
    return (q.join(WorkTaskAssignee, WorkTaskAssignee.task_id == WorkTask.id)
            .filter(WorkTask.list_id.in_(list_ids), WorkTaskAssignee.employee_id == entity_id,
                    WorkTaskAssignee.kind == int(WorkAssigneeKind.PIC)))


def _bucket_starts(first_day: date, today: date, weekly: bool) -> list[date]:
    step = 7 if weekly else 1
    starts, day = [], first_day
    while day <= today:
        starts.append(day)
        day += timedelta(days=step)
    return starts


def trend(db: Session, list_ids: set[int], kind: str, entity_id: int, today: str, period_days: int,
          since_utc: datetime) -> dict:
    """`{granularity, buckets: [{start, label, created, done_on_time, done_late, done_no_due}]}` — đủ mọi mốc, kể cả
    mốc 0 (một ngày không ai làm gì cũng là thông tin)."""
    weekly = period_days > DAILY_MAX_DAYS
    today_d = date.fromisoformat(today)
    first_day = today_d - timedelta(days=period_days - 1)
    starts = _bucket_starts(first_day, today_d, weekly)
    empty = {"granularity": "week" if weekly else "day", "buckets": []}
    if kind not in (KIND_PROJECT, KIND_PERSON) or not entity_id or not list_ids:
        return empty
    if kind == KIND_PROJECT and entity_id not in list_ids:
        return empty

    def count(cond):
        return func.coalesce(func.sum(case((cond, 1), else_=0)), 0)

    created_day = vn_date_str(db, WorkTask.created_at)
    created = dict(_base(db, list_ids, kind, entity_id)
                   .with_entities(created_day, func.count(WorkTask.id))
                   .filter(WorkTask.created_at >= since_utc).group_by(created_day).all())

    done_day = vn_date_str(db, WorkTask.completed_at)
    has_due = WorkTask.due_date != ""
    on_time = and_(has_due, done_day <= WorkTask.due_date)
    done = {d: (int(a), int(b), int(c)) for d, a, b, c in (
        _base(db, list_ids, kind, entity_id)
        .with_entities(done_day, count(on_time), count(and_(has_due, done_day > WorkTask.due_date)), count(~has_due))
        .filter(WorkTask.status == int(WorkTaskStatus.DONE), WorkTask.completed_at.isnot(None),
                WorkTask.completed_at >= since_utc)
        .group_by(done_day).all())}

    #  Mỗi ngày rơi vào mốc có ngày bắt đầu lớn nhất mà không vượt nó.
    index = {}
    for i, start in enumerate(starts):
        for offset in range(7 if weekly else 1):
            index[(start + timedelta(days=offset)).isoformat()] = i
    buckets = [{"start": s.isoformat(), "label": s.strftime("%d/%m"),
                "created": 0, "done_on_time": 0, "done_late": 0, "done_no_due": 0} for s in starts]
    for day, n in created.items():
        if str(day) in index:
            buckets[index[str(day)]]["created"] += int(n)
    for day, (n_on_time, n_late, n_no_due) in done.items():
        if str(day) in index:
            b = buckets[index[str(day)]]
            b["done_on_time"] += n_on_time
            b["done_late"] += n_late
            b["done_no_due"] += n_no_due
    return {"granularity": "week" if weekly else "day", "buckets": buckets}
