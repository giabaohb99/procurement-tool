"""Phân hệ Công việc — gom dữ liệu phụ của một mớ task bằng SỐ QUERY CỐ ĐỊNH.

Thẻ việc trên kanban cần: người phụ trách, tag, nhãn tùy biến, tiến độ việc con
n/m, số bình luận. Hỏi từng thứ trong vòng lặp là 5 query nhân số thẻ — một
bảng 200 việc thành nghìn câu truy vấn. Tệp này hỏi mỗi thứ đúng một lần cho cả
mẻ rồi phát về theo `task_id`.
"""
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.modules.work.label_model import WorkTaskLabel, WorkTaskTag
from app.modules.work.task_model import WorkTask, WorkTaskAssignee


def _employee_names(db: Session, ids: list[int]) -> dict[int, dict]:
    from app.modules.employee.model import Employee

    ids = [i for i in set(ids) if i]
    if not ids:
        return {}
    rows = db.query(Employee).filter(Employee.id.in_(ids)).all()
    return {e.id: {"name": e.full_name or "", "code": e.code or ""} for e in rows}


def collect(db: Session, tasks: list[WorkTask]) -> dict:
    """Trả bó dữ liệu phụ, tra theo `task_id`.

    `{assignees, tags, labels, subtasks, comments}` — mỗi khóa là một dict
    `task_id -> giá trị`, thiếu khóa nghĩa là task đó không có gì.
    """
    ids = [t.id for t in tasks]
    if not ids:
        return {"assignees": {}, "tags": {}, "labels": {}, "subtasks": {}, "comments": {}}

    rows = db.query(WorkTaskAssignee).filter(WorkTaskAssignee.task_id.in_(ids)).all()
    names = _employee_names(db, [r.employee_id for r in rows])
    assignees: dict[int, list] = {}
    for r in rows:
        info = names.get(r.employee_id) or {}
        assignees.setdefault(r.task_id, []).append({
            "employee_id": r.employee_id, "kind": int(r.kind),
            "employee_name": info.get("name", ""), "employee_code": info.get("code", ""),
        })

    tags: dict[int, list] = {}
    for tt in db.query(WorkTaskTag).filter(WorkTaskTag.task_id.in_(ids)).all():
        tags.setdefault(tt.task_id, []).append(tt.tag_id)

    labels: dict[int, list] = {}
    for tl in db.query(WorkTaskLabel).filter(WorkTaskLabel.task_id.in_(ids)).all():
        labels.setdefault(tl.task_id, []).append(
            {"field_id": tl.field_id, "option_id": tl.option_id})

    #  Tiến độ việc con n/m (C-02): đếm theo CHA, chỉ tính việc con còn sống.
    from app.modules.work.model import WorkTaskStatus  # tránh vòng import ở đầu tệp

    subtasks: dict[int, dict] = {}
    #  `case(...)` chứ không `func.if_(...)`: `IF()` là hàm riêng của MySQL, bộ
    #  test chạy trên SQLite in-memory sẽ nổ ngay câu này.
    sub_rows = (db.query(WorkTask.parent_id,
                         func.count(WorkTask.id),
                         func.sum(case((WorkTask.status == int(WorkTaskStatus.DONE), 1),
                                       else_=0)))
                .filter(WorkTask.parent_id.in_(ids), WorkTask.deleted_at.is_(None))
                .group_by(WorkTask.parent_id).all())
    for parent_id, total, done in sub_rows:
        subtasks[parent_id] = {"total": int(total or 0), "done": int(done or 0)}

    return {"assignees": assignees, "tags": tags, "labels": labels,
            "subtasks": subtasks, "comments": comment_counts(db, ids)}


def comment_counts(db: Session, task_ids: list[int]) -> dict[int, int]:
    """Số bình luận trên thẻ (E-01).

    Bình luận dùng BẢNG CHUNG `tab_comment` với `entity = 'work_task'` — khuôn
    CR-029/CR-033, không đẻ bảng riêng cho phân hệ này. Đến W3 mới mở đường ghi;
    hàm này đã đếm sẵn nên thẻ không phải đổi hình dạng lúc đó.
    """
    from app.modules.comment.model import Comment

    if not task_ids:
        return {}
    rows = (db.query(Comment.entity_id, func.count(Comment.id))
            .filter(Comment.entity == "work_task", Comment.entity_id.in_(task_ids))
            .group_by(Comment.entity_id).all())
    return {tid: n for tid, n in rows}
