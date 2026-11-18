"""Phân hệ Dự án — SỨC KHỎE TỪNG DỰ ÁN của màn Tổng quan (duoc-CR-782).

Người quản lý cần biết dự án nào đang trôi, dự án nào đang trễ, không phải mở từng bảng kanban. Một câu SQL gom mọi
chỉ số theo `list_id` (số truy vấn cố định), một câu tra tên dự án.

Nhãn sức khỏe là GIÁ TRỊ SUY RA, không lưu — trả kèm mã số và nhãn (luật R2: mã + nhãn, tiếng Việt chỉ để hiển thị).
Luật cố ý đơn giản để ai cũng tự tính lại được bằng mắt:
- **Chưa có việc**: dự án chưa có việc nào (không tính việc hủy) — gắn "Đúng tiến độ" cho nó là khen một bảng trống;
- **Trễ**: từ 25% việc đang mở trở lên đã quá hạn;
- **Có rủi ro**: có ít nhất một việc quá hạn (chưa tới ngưỡng trên);
- **Đúng tiến độ**: không việc nào quá hạn.
"""
from datetime import datetime
from enum import IntEnum

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.modules.work.model import WorkList, WorkTaskStatus
from app.modules.work.task_model import WorkTask

#  Ngưỡng % việc mở đã quá hạn để gọi là Trễ.
LATE_SHARE = 25


class ProjectHealth(IntEnum):
    """Sức khỏe dự án trên màn Tổng quan (suy ra, không lưu). Số lớn = đáng lo hơn (bảng xếp giảm dần)."""
    NO_TASKS = 0
    ON_TRACK = 1
    AT_RISK = 2
    LATE = 3


HEALTH_LABELS = {
    ProjectHealth.NO_TASKS: "Chưa có việc",
    ProjectHealth.ON_TRACK: "Đúng tiến độ",
    ProjectHealth.AT_RISK: "Có rủi ro",
    ProjectHealth.LATE: "Trễ",
}


def project_health(total: int, n_open: int, n_overdue: int) -> ProjectHealth:
    if not total:
        return ProjectHealth.NO_TASKS
    if n_overdue and n_open and n_overdue * 100 >= n_open * LATE_SHARE:
        return ProjectHealth.LATE
    if n_overdue:
        return ProjectHealth.AT_RISK
    return ProjectHealth.ON_TRACK


def _count(cond):
    return func.coalesce(func.sum(case((cond, 1), else_=0)), 0)


def project_rows(db: Session, list_ids, today: str, openable: set[int] | None = None,
                 since_utc: datetime | None = None) -> list[dict]:
    """Dự án CHƯA lưu trữ, dự án trễ / nhiều việc quá hạn lên đầu. Dự án chưa có việc nào vẫn hiện (0%).

    `since_utc` = đầu kỳ (UTC) cho `done_in_period` — số việc xong trong kỳ, vẽ thành đường cạnh cột việc mở trên biểu
    đồ dự án. Tổng việc xong từ trước tới nay quá lớn so với việc mở, vẽ chung một trục là cột bị bẹp.
    """
    if not list_ids:
        return []
    is_open = WorkTask.status == int(WorkTaskStatus.OPEN)
    overdue = and_(is_open, WorkTask.due_date != "", WorkTask.due_date < today)
    stats = {row[0]: row[1:] for row in (
        db.query(WorkTask.list_id,
                 #  Tổng KHÔNG tính việc đã hủy: hủy là "không làm nữa", tính vào mẫu số là kéo % hoàn thành xuống oan.
                 _count(WorkTask.status != int(WorkTaskStatus.CANCELLED)),
                 _count(WorkTask.status == int(WorkTaskStatus.DONE)),
                 _count(is_open), _count(overdue),
                 _count(and_(WorkTask.status == int(WorkTaskStatus.DONE), WorkTask.completed_at.isnot(None),
                             WorkTask.completed_at >= (since_utc or datetime.min))),
                 #  Hạn chót = hạn XA nhất trong số việc còn mở: ngày dự án còn phải chạy tới.
                 func.max(case((and_(is_open, WorkTask.due_date != ""), WorkTask.due_date), else_=None)))
        .filter(WorkTask.list_id.in_(list_ids), WorkTask.parent_id.is_(None), WorkTask.deleted_at.is_(None))
        .group_by(WorkTask.list_id).all())}

    rows = []
    for lst in (db.query(WorkList.id, WorkList.name, WorkList.color)
                .filter(WorkList.id.in_(list_ids), WorkList.is_archived == 0).all()):
        total, done, n_open, n_overdue, n_done_period, last_due = stats.get(lst.id, (0, 0, 0, 0, 0, None))
        total, done, n_open, n_overdue = int(total), int(done), int(n_open), int(n_overdue)
        health = project_health(total, n_open, n_overdue)
        rows.append({
            "list_id": lst.id,
            "name": lst.name,
            "color": lst.color or "",
            "total": total,
            "done": done,
            "open": n_open,
            "overdue": n_overdue,
            "done_in_period": int(n_done_period),
            "progress": round(done * 100 / total) if total else 0,
            "last_due": last_due or "",
            "health": int(health),
            "health_label": HEALTH_LABELS[health],
            #  Không là thành viên (phạm vi "mọi dự án") thì xem số được, mở bảng việc thì không.
            "can_open": openable is None or lst.id in openable,
        })
    rows.sort(key=lambda r: (-r["health"], -r["overdue"], -r["open"], r["name"]))
    return rows
