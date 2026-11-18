"""Phân hệ Dự án — khối CẦN XỬ LÝ NGAY của màn Tổng quan (duoc-CR-782).

Ba loại việc người quản lý phải ra tay, mỗi loại một con số + tối đa `TOP_TASKS` dòng để bấm vào:
- **Quá hạn lâu nhất** kèm NGƯỜI PHỤ TRÁCH và SỐ NGÀY TRỄ — biết việc nào trễ mà không biết ai đang giữ thì vẫn phải
  mở từng thẻ để hỏi;
- **Chưa ai nhận**: việc đang mở không có người phụ trách — không ai làm, và cũng không hiện ở bảng theo người;
- **Chưa đặt hạn**: việc đang mở không có hạn — không bao giờ "quá hạn" nên lọt khỏi mọi cảnh báo.

Số truy vấn cố định: hai câu đếm, ba câu lấy dòng, một câu lấy người phụ trách của các việc quá hạn, hai câu tra tên.
"""
from datetime import date

from sqlalchemy import exists
from sqlalchemy.orm import Session

from app.modules.work.model import WorkAssigneeKind, WorkTaskStatus
from app.modules.work.people import employee_info
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

#  Số dòng mỗi danh sách — cùng mốc 8 với hai danh sách cũ của màn Tổng quan (`overview_service.TOP_TASKS`).
TOP_TASKS = 8
PIC = int(WorkAssigneeKind.PIC)


def _open_tasks(db: Session, list_ids):
    return db.query(WorkTask).filter(
        WorkTask.list_id.in_(list_ids), WorkTask.parent_id.is_(None), WorkTask.deleted_at.is_(None),
        WorkTask.status == int(WorkTaskStatus.OPEN))


def _row(task: WorkTask, list_names: dict[int, str], openable: set[int] | None) -> dict:
    """`can_open = False` khi người xem không là thành viên dự án chứa việc (phạm vi "mọi dự án") — mở là 403."""
    return {"id": task.id, "list_id": task.list_id, "list_name": list_names.get(task.list_id, ""),
            "title": task.title, "due_date": task.due_date,
            "can_open": openable is None or task.list_id in openable}


def attention(db: Session, list_ids, today: str, list_names: dict[int, str],
              openable: set[int] | None = None) -> dict:
    """`{overdue_tasks, unassigned_count, unassigned_tasks, no_due_count, no_due_tasks}`."""
    if not list_ids:
        return {"overdue_tasks": [], "unassigned_count": 0, "unassigned_tasks": [],
                "no_due_count": 0, "no_due_tasks": []}

    overdue = (_open_tasks(db, list_ids).filter(WorkTask.due_date != "", WorkTask.due_date < today)
               .order_by(WorkTask.due_date.asc(), WorkTask.id.asc()).limit(TOP_TASKS).all())
    pics: dict[int, list[int]] = {}
    for task_id, emp_id in (db.query(WorkTaskAssignee.task_id, WorkTaskAssignee.employee_id)
                            .filter(WorkTaskAssignee.task_id.in_([t.id for t in overdue] or [0]),
                                    WorkTaskAssignee.kind == PIC).all()):
        pics.setdefault(task_id, []).append(emp_id)
    names = employee_info(db, [e for ids in pics.values() for e in ids])
    today_d = date.fromisoformat(today)
    overdue_rows = [{
        **_row(t, list_names, openable),
        "overdue_days": (today_d - date.fromisoformat(t.due_date)).days,
        #  Tên người phụ trách, giữ thứ tự id để hai lần tải cho cùng một kết quả.
        "assignees": [names.get(e, {}).get("name", "") for e in sorted(pics.get(t.id, []))],
    } for t in overdue]

    no_pic = ~exists().where(WorkTaskAssignee.task_id == WorkTask.id, WorkTaskAssignee.kind == PIC)
    unassigned = _open_tasks(db, list_ids).filter(no_pic)
    no_due = _open_tasks(db, list_ids).filter(WorkTask.due_date == "")
    return {
        "overdue_tasks": overdue_rows,
        "unassigned_count": unassigned.count(),
        #  Việc chưa ai nhận: hạn gần nhất trước (sắp tới hạn mà chưa ai giữ là gấp nhất), chưa đặt hạn xuống cuối.
        "unassigned_tasks": [_row(t, list_names, openable) for t in unassigned.order_by(
            (WorkTask.due_date == "").asc(), WorkTask.due_date.asc(), WorkTask.id.asc()).limit(TOP_TASKS).all()],
        "no_due_count": no_due.count(),
        #  Việc chưa đặt hạn: việc tạo LÂU nhất trước — càng cũ càng dễ đã bị quên.
        "no_due_tasks": [_row(t, list_names, openable) for t in no_due.order_by(WorkTask.id.asc()).limit(TOP_TASKS).all()],
    }
