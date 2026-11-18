"""Phân hệ Dự án — BẢNG ĐỐI CHIẾU THEO NGƯỜI của màn Tổng quan (duoc-CR-782).

Câu hỏi của người quản lý khi mở màn này: *ai đang ôm bao nhiêu việc, ai đang trễ, ai làm xong đúng hạn, ai lâu rồi
không động tới việc*. Mỗi người phụ trách (PIC) một dòng; người THEO DÕI không tính — theo dõi là để biết, không
phải để làm (cùng luật "Việc của tôi").

Số truy vấn CỐ ĐỊNH, không theo số người (luật "API báo cáo nhanh nhất"):
1. một câu gom mọi chỉ số bằng `SUM(CASE …)` nhóm theo `employee_id`;
2. một câu lấy hạn của các việc ĐANG quá hạn để tính "trễ lâu nhất" (chỉ việc quá hạn, không quét cả bảng);
3. hai câu tra tên / mã / ảnh (`people.employee_info`).

Một việc có HAI người phụ trách thì góp vào CẢ HAI dòng — tổng các dòng có thể lớn hơn số việc, đúng với câu hỏi
"mỗi người đang gánh bao nhiêu".
"""
from datetime import date, datetime, timedelta

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.modules.work.model import WorkAssigneeKind, WorkTaskStatus
from app.modules.work.people import employee_info
from app.modules.work.report_sql_date import vn_date_str
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

#  "Đến hạn sắp tới" = trong 7 ngày kể từ hôm nay (tính cả hôm nay).
DUE_SOON_DAYS = 7
#  Số việc tối đa trả về khi bấm vào một người — đây là lối đi tiếp, không phải màn danh sách thứ hai.
PERSON_TASK_LIMIT = 50

OPEN = int(WorkTaskStatus.OPEN)
DONE = int(WorkTaskStatus.DONE)
PIC = int(WorkAssigneeKind.PIC)


def _alive(query, list_ids):
    """Nền chung: chỉ việc CHA còn sống trong các dự án được đếm."""
    return query.filter(WorkTask.list_id.in_(list_ids), WorkTask.parent_id.is_(None),
                        WorkTask.deleted_at.is_(None))


def _count(cond):
    return func.coalesce(func.sum(case((cond, 1), else_=0)), 0)


def _hours(cond, col):
    return func.coalesce(func.sum(case((cond, func.coalesce(col, 0)), else_=0)), 0)


def people_rows(db: Session, list_ids, today: str, since_utc: datetime) -> list[dict]:
    """Mỗi người phụ trách một dòng; xếp người nhiều việc QUÁ HẠN lên đầu, rồi người đang mở nhiều việc."""
    if not list_ids:
        return []
    soon = (date.fromisoformat(today) + timedelta(days=DUE_SOON_DAYS - 1)).isoformat()
    is_open = WorkTask.status == OPEN
    has_due = WorkTask.due_date != ""
    overdue = and_(is_open, has_due, WorkTask.due_date < today)
    done_in_period = and_(WorkTask.status == DONE, WorkTask.completed_at.isnot(None),
                          WorkTask.completed_at >= since_utc)
    done_with_due = and_(done_in_period, has_due)
    done_on_time = and_(done_with_due, vn_date_str(db, WorkTask.completed_at) <= WorkTask.due_date)

    stats = (_alive(db.query(
        WorkTaskAssignee.employee_id,
        _count(is_open), _count(overdue),
        _count(and_(is_open, has_due, WorkTask.due_date >= today, WorkTask.due_date <= soon)),
        _count(done_in_period), _count(done_with_due), _count(done_on_time),
        _hours(is_open, WorkTask.estimate_hours), _hours(done_in_period, WorkTask.actual_hours),
        func.max(WorkTask.updated_at),
    ).join(WorkTask, WorkTask.id == WorkTaskAssignee.task_id), list_ids)
        .filter(WorkTaskAssignee.kind == PIC, WorkTaskAssignee.employee_id > 0)
        .group_by(WorkTaskAssignee.employee_id).all())

    #  "Trễ lâu nhất" lấy hạn CŨ NHẤT trong số việc đang quá hạn của từng người — một con số nói được "trễ 40 ngày"
    #  mà con số đếm "3 việc quá hạn" không nói được. MIN(due_date) đủ, không cần trừ ngày ở SQL.
    oldest_due = dict(_alive(db.query(WorkTaskAssignee.employee_id, func.min(WorkTask.due_date))
                             .join(WorkTask, WorkTask.id == WorkTaskAssignee.task_id), list_ids)
                      .filter(WorkTaskAssignee.kind == PIC, overdue)
                      .group_by(WorkTaskAssignee.employee_id).all())

    info = employee_info(db, [row[0] for row in stats])
    today_d = date.fromisoformat(today)
    rows = []
    for (emp_id, n_open, n_overdue, n_soon, n_done, n_done_due, n_on_time,
         est_open, actual_done, last_update) in stats:
        person = info.get(emp_id, {})
        oldest = oldest_due.get(emp_id)
        rows.append({
            "employee_id": emp_id,
            "name": person.get("name", ""),
            "code": person.get("code", ""),
            "avatar": person.get("avatar", ""),
            "open": int(n_open),
            "overdue": int(n_overdue),
            "due_soon": int(n_soon),
            "done_in_period": int(n_done),
            #  Tỉ lệ đúng hạn chỉ tính trên việc XONG trong kỳ CÓ đặt hạn — việc không hạn không có "đúng" hay "trễ".
            #  `None` (không phải 0%) khi chưa có việc nào để đo, giao diện hiện "—".
            "on_time_rate": round(int(n_on_time) * 100 / int(n_done_due)) if n_done_due else None,
            "max_overdue_days": (today_d - date.fromisoformat(oldest)).days if oldest else 0,
            "estimate_hours_open": float(est_open or 0),
            "actual_hours_done": float(actual_done or 0),
            "last_update": last_update.isoformat() if last_update else None,
        })
    rows.sort(key=lambda r: (-r["overdue"], -r["open"], r["name"]))
    return rows


def person_tasks(db: Session, list_ids, employee_id: int, today: str, list_names: dict[int, str],
                 openable: set[int] | None = None) -> list[dict]:
    """Việc ĐANG MỞ của một người (là PIC) — quá hạn trước, rồi theo hạn gần nhất; chưa đặt hạn xuống cuối."""
    if not list_ids or not employee_id:
        return []
    tasks = (_alive(db.query(WorkTask).join(WorkTaskAssignee, WorkTaskAssignee.task_id == WorkTask.id), list_ids)
             .filter(WorkTaskAssignee.employee_id == employee_id, WorkTaskAssignee.kind == PIC,
                     WorkTask.status == OPEN)
             .order_by((WorkTask.due_date == "").asc(), WorkTask.due_date.asc(), WorkTask.id.asc())
             .distinct().limit(PERSON_TASK_LIMIT).all())
    return [{
        "id": t.id,
        "list_id": t.list_id,
        "list_name": list_names.get(t.list_id, ""),
        "title": t.title,
        "due_date": t.due_date,
        "overdue": bool(t.due_date and t.due_date < today),
        "can_open": openable is None or t.list_id in openable,
    } for t in tasks]
