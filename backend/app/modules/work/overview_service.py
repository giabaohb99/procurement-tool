"""Phân hệ Dự án — số liệu cho màn TỔNG QUAN.

Tách khỏi `list_service` / `task_service` vì đây thuần là đếm: không sửa gì,
không có bất biến nào phải giữ, và mọi query đều gom theo `visible_list_ids`.

Vì sao đếm ở MÁY CHỦ chứ không kéo hết về gom ở trình duyệt như màn Tổng quan
Nhân sự: bên đó chỉ có vài trăm nhân sự nằm trong MỘT endpoint danh sách, còn
việc ở đây nằm rải trong từng dự án và API bảng kanban lấy theo TỪNG dự án —
gom ở client là hàng chục lượt gọi rồi tải về vài nghìn thẻ chỉ để đếm.

⚠️ Mọi con số phải lọc qua `visible_list_ids`. Đếm thẳng trên `tab_work_task`
là lộ khối lượng việc của những đội mình không tham gia.
"""
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.work.membership_service import Actor, visible_list_ids
from app.modules.work.model import WorkAssigneeKind, WorkList, WorkTaskStatus
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

#  Giờ Việt Nam. Máy chủ chạy UTC nên "hôm nay" lệch 7 tiếng nếu lấy thẳng —
#  việc đến hạn hôm nay sẽ bị đếm là quá hạn suốt buổi tối.
VN_OFFSET = timedelta(hours=7)

#  Số dự án vẽ trên biểu đồ cột. Nhiều hơn thì chữ chồng lên nhau, mà phần đuôi
#  toàn dự án một hai việc, không nói lên điều gì.
TOP_PROJECTS = 8


def _today() -> str:
    return (datetime.utcnow() + VN_OFFSET).strftime("%Y-%m-%d")


def overview(db: Session, actor: Actor) -> dict:
    """Thẻ số liệu + dữ liệu hai biểu đồ của màn Tổng quan."""
    ids = visible_list_ids(db, actor.employee_id, actor.company_id)
    if not ids:
        return _empty()

    lists = db.query(WorkList).filter(WorkList.id.in_(ids)).all()

    #  Nền chung của mọi phép đếm việc: chỉ task CHA còn sống, trong dự án mình
    #  thấy. Việc con là gạch đầu dòng bên trong thẻ, không phải một đầu việc.
    def tasks():
        return db.query(WorkTask).filter(
            WorkTask.list_id.in_(ids),
            WorkTask.parent_id.is_(None),
            WorkTask.deleted_at.is_(None),
        )

    by_status = dict(
        tasks().with_entities(WorkTask.status, func.count(WorkTask.id))
        .group_by(WorkTask.status).all())

    open_only = tasks().filter(WorkTask.status == int(WorkTaskStatus.OPEN))

    overdue = open_only.filter(
        WorkTask.due_date != "", WorkTask.due_date < _today()).count()

    #  "Việc của tôi" = tôi là NGƯỜI PHỤ TRÁCH, không tính người theo dõi: theo
    #  dõi là để biết, không phải để làm.
    mine = (open_only.join(WorkTaskAssignee, WorkTaskAssignee.task_id == WorkTask.id)
            .filter(WorkTaskAssignee.employee_id == actor.employee_id,
                    WorkTaskAssignee.kind == int(WorkAssigneeKind.PIC))
            .distinct().count())

    open_by_list = dict(
        open_only.with_entities(WorkTask.list_id, func.count(WorkTask.id))
        .group_by(WorkTask.list_id).all())

    by_priority = [
        {"priority": int(priority), "open": int(count)}
        for priority, count in (
            open_only.with_entities(WorkTask.priority, func.count(WorkTask.id))
            .group_by(WorkTask.priority).all())
    ]

    by_project = sorted(
        ({"list_id": lst.id, "name": lst.name, "open": open_by_list.get(lst.id, 0)}
         for lst in lists if not lst.is_archived),
        key=lambda row: row["open"], reverse=True)[:TOP_PROJECTS]

    return {
        "project_total": sum(1 for lst in lists if not lst.is_archived),
        "project_archived": sum(1 for lst in lists if lst.is_archived),
        "task_open": by_status.get(int(WorkTaskStatus.OPEN), 0),
        "task_done": by_status.get(int(WorkTaskStatus.DONE), 0),
        "task_cancelled": by_status.get(int(WorkTaskStatus.CANCELLED), 0),
        "task_overdue": overdue,
        "task_mine": mine,
        "by_project": by_project,
        "by_priority": sorted(by_priority, key=lambda row: row["priority"]),
    }


def _empty() -> dict:
    """Chưa tham gia dự án nào. Trả đủ KHÓA với số 0 chứ không trả `{}` —
    giao diện đọc `data.task_open` thẳng, thiếu khóa là `undefined` trên thẻ."""
    return {
        "project_total": 0, "project_archived": 0,
        "task_open": 0, "task_done": 0, "task_cancelled": 0,
        "task_overdue": 0, "task_mine": 0,
        "by_project": [], "by_priority": [],
    }
