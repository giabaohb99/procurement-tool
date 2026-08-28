"""Phân hệ Công việc — task và việc con (B-01…B-08, C-01…C-05).

Bốn luật của tệp này, đều là thứ DB không giữ hộ được:

1. **Chặn cấp 3** — cha đã có `parent_id` thì không nhận con (C-05).
2. **Việc con vô hình ngoài panel cha** — mang `list_id` của cha, `section_id`
   luôn NULL, và mọi query kanban/danh sách lọc `parent_id IS NULL` (Q10).
3. **Xóa là xóa mềm** — `deleted_at`; mọi query thường phải tự lọc.
4. **Xóa của MEMBER chỉ được task mình tạo**; ADMIN/OWNER xóa được mọi task.
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.work import serializer as ser
from app.modules.work import task_enrich
from app.modules.work import label_value_service as label_values
from app.modules.work.label_model import (WorkLabelField, WorkLabelOption,
                                          WorkTag, WorkTaskLabel, WorkTaskTag)
from app.modules.work.membership_service import (CAN_EDIT, CAN_MANAGE, Actor,
                                                 block_if_archived,
                                                 effective_role, get_list_or_403)
from app.modules.work.model import WorkAssigneeKind, WorkTaskStatus
from app.modules.work.task_model import WorkSection, WorkTask, WorkTaskAssignee


#  Bước giãn khi đánh lại số thứ tự trong một cột. Bản sao ở giao diện:
#  `frontend-v2/src/modules/work/utils/kanban-drop.ts` (hằng `SORT_STEP`).
SORT_STEP = 1000


def _shape(tasks: list[WorkTask], extra: dict) -> list[dict]:
    out = []
    for t in tasks:
        sub = extra["subtasks"].get(t.id) or {}
        out.append(ser.task_out(
            t,
            assignees=extra["assignees"].get(t.id, []),
            tag_ids=extra["tags"].get(t.id, []),
            labels=extra["labels"].get(t.id, []),
            subtask_done=sub.get("done", 0), subtask_total=sub.get("total", 0),
            comment_count=extra["comments"].get(t.id, 0),
        ))
    return out


def get_task_or_403(db: Session, actor: Actor, task_id: int, need: int = 4) -> WorkTask:
    """Lấy task theo id — cửa DUY NHẤT, luôn kiểm qua list chứa nó.

    Gõ thẳng id vào URL mà đọc được task của list mình không tham gia chính là
    lỗ mà §5.1 của `04-phan-quyen.md` bắt phải khóa. 403 chứ không 404: phân
    biệt hai cái là đã nói cho người ngoài biết id đó có thật.
    """
    t = db.get(WorkTask, task_id)
    if not t or t.deleted_at is not None:
        raise HTTPException(403, "Không có quyền trên công việc này")
    get_list_or_403(db, actor, t.list_id, need)
    return t


def board(db: Session, actor: Actor, list_id: int) -> dict:
    """Payload một phát cho kanban: cột + task cha + mọi thứ vẽ trên thẻ."""
    lst = get_list_or_403(db, actor, list_id)
    sections = (db.query(WorkSection).filter(WorkSection.list_id == list_id)
                .order_by(WorkSection.sort_order, WorkSection.id).all())
    tasks = (db.query(WorkTask)
             .filter(WorkTask.list_id == list_id,
                     WorkTask.parent_id.is_(None),      # việc con không ra kanban (C-05)
                     WorkTask.deleted_at.is_(None))
             .order_by(WorkTask.sort_order, WorkTask.id).all())
    return {
        "list": ser.list_out(lst, effective_role(db, actor.employee_id, list_id)),
        "sections": [ser.section_out(s) for s in sections],
        "tasks": _shape(tasks, task_enrich.collect(db, tasks)),
    }


def get_task(db: Session, actor: Actor, task_id: int) -> dict:
    """Chi tiết một task, kèm danh sách việc con (panel D-03)."""
    t = get_task_or_403(db, actor, task_id)
    subs = (db.query(WorkTask)
            .filter(WorkTask.parent_id == task_id, WorkTask.deleted_at.is_(None))
            .order_by(WorkTask.sort_order, WorkTask.id).all())
    data = _shape([t], task_enrich.collect(db, [t]))[0]
    data["subtasks"] = _shape(subs, task_enrich.collect(db, subs))
    return data


def create_task(db: Session, actor: Actor, data) -> dict:
    """Tạo task hoặc VIỆC CON (truyền `parent_id`).

    Việc con không nhận `list_id`/`section_id` từ người gọi: nó luôn nằm cùng
    list với cha và không thuộc cột nào — đặt khác đi là nó lọt ra kanban.
    """
    parent = None
    if data.parent_id:
        parent = db.get(WorkTask, data.parent_id)
        if not parent or parent.deleted_at is not None:
            raise HTTPException(404, "Không thấy công việc cha")
        if parent.parent_id:
            raise HTTPException(400, "Việc con chỉ sâu 2 cấp — việc con không có việc con")
        list_id = parent.list_id
    else:
        list_id = data.list_id

    lst = get_list_or_403(db, actor, list_id, CAN_EDIT)
    block_if_archived(lst)

    section_id = None
    if not parent:
        section_id = data.section_id or _first_section_id(db, list_id)
        if section_id and not _section_belongs(db, section_id, list_id):
            raise HTTPException(400, "Cột không thuộc danh sách này")

    t = WorkTask(company_id=lst.company_id, list_id=list_id, section_id=section_id,
                 parent_id=parent.id if parent else None,
                 title=data.title.strip(), description=data.description or "",
                 status=int(WorkTaskStatus.OPEN), priority=data.priority or 0,
                 start_date=data.start_date or "", due_date=data.due_date or "",
                 sort_order=data.sort_order or _next_sort_order(
                     db, list_id, section_id, parent.id if parent else None),
                 creator_employee_id=actor.employee_id,
                 created_by=actor.user_id, updated_by=actor.user_id)
    db.add(t)
    db.commit()
    if data.assignee_ids:
        set_assignees(db, actor, t.id, data.assignee_ids, [])
    record(db, actor.user_id, "work_task", t.id, "create", f"Tạo công việc: {t.title}")
    return _shape([t], task_enrich.collect(db, [t]))[0]


def _first_section_id(db: Session, list_id: int) -> int | None:
    s = (db.query(WorkSection).filter(WorkSection.list_id == list_id)
         .order_by(WorkSection.sort_order, WorkSection.id).first())
    return s.id if s else None


def _section_belongs(db: Session, section_id: int, list_id: int) -> bool:
    s = db.get(WorkSection, section_id)
    return bool(s and s.list_id == list_id)


def _next_sort_order(db: Session, list_id: int, section_id: int | None,
                     parent_id: int | None) -> int:
    """Số thứ tự để thẻ mới nằm CUỐI cột (hoặc cuối danh sách việc con).

    Trước đây mọi task mới đều mang `sort_order = 0`: cả cột trùng số nên không
    còn khe nào để chèn vào giữa, và mỗi lần kéo một thẻ vào giữa cột nó lại rơi
    xuống đáy. Đây là một nửa của lỗi kéo thả kanban (nửa kia là `move_task`).
    """
    q = db.query(func.max(WorkTask.sort_order)).filter(
        WorkTask.list_id == list_id, WorkTask.deleted_at.is_(None))
    if parent_id:
        q = q.filter(WorkTask.parent_id == parent_id)
    else:
        q = q.filter(WorkTask.parent_id.is_(None), WorkTask.section_id == section_id)
    return int(q.scalar() or 0) + SORT_STEP


def move_task(db: Session, actor: Actor, task_id: int, section_id: int,
              before_task_id: int | None) -> dict:
    """Kéo thả kanban: đưa task vào cột `section_id`, NGAY TRƯỚC `before_task_id`.

    Nhận MỐC TƯƠNG ĐỐI chứ không nhận `sort_order` tính sẵn ở trình duyệt, vì
    bảng trên màn hình có thể đang lọc (lát cắt / từ khóa) — client chỉ thấy một
    phần của cột, tự tính số thì mọi thẻ đang bị ẩn văng lên đầu.

    Cả cột đích được ĐÁNH SỐ LẠI theo bước `SORT_STEP` trong cùng một giao dịch,
    nên sau mỗi cú thả thứ tự là duy nhất và không bao giờ hết khe.
    """
    t = get_task_or_403(db, actor, task_id, CAN_EDIT)
    lst = get_list_or_403(db, actor, t.list_id, CAN_EDIT)
    block_if_archived(lst)

    if t.parent_id:
        raise HTTPException(400, "Việc con không nằm trong cột nào")
    if not _section_belongs(db, section_id, t.list_id):
        raise HTTPException(400, "Cột không thuộc danh sách này")

    t.section_id = section_id
    db.flush()

    rows = (db.query(WorkTask)
            .filter(WorkTask.list_id == t.list_id,
                    WorkTask.section_id == section_id,
                    WorkTask.parent_id.is_(None),
                    WorkTask.deleted_at.is_(None))
            .order_by(WorkTask.sort_order, WorkTask.id).all())
    others = [r for r in rows if r.id != task_id]

    if before_task_id == task_id:
        pos = min(rows.index(t), len(others))       # "chèn trước chính nó" = đứng yên
    else:
        #  Mốc lạ (thẻ vừa bị người khác kéo đi nơi khác) thì thả xuống CUỐI cột:
        #  lệch một chỗ còn hơn ném thẻ về đầu cột.
        pos = next((i for i, r in enumerate(others) if r.id == before_task_id),
                   len(others))

    others.insert(pos, t)
    for i, r in enumerate(others):
        r.sort_order = (i + 1) * SORT_STEP

    t.updated_by = actor.user_id
    db.commit()
    record(db, actor.user_id, "work_task", t.id, "update", f"Chuyển công việc: {t.title}")
    return _shape([t], task_enrich.collect(db, [t]))[0]


def update_task(db: Session, actor: Actor, task_id: int, data) -> dict:
    """Sửa task. Kéo sang cột khác = gửi `section_id` + `sort_order` (B-07).

    Đánh dấu hoàn thành cũng đi qua đây (`status`): đặt/xóa `completed_at` là
    việc của tệp này, không để nơi gọi tự nhớ.
    """
    t = get_task_or_403(db, actor, task_id, CAN_EDIT)
    lst = get_list_or_403(db, actor, t.list_id, CAN_EDIT)
    block_if_archived(lst)

    if data.section_id is not None:
        if t.parent_id:
            raise HTTPException(400, "Việc con không nằm trong cột nào")
        if data.section_id and not _section_belongs(db, data.section_id, t.list_id):
            raise HTTPException(400, "Cột không thuộc danh sách này")
        t.section_id = data.section_id or None

    for field in ("title", "description", "priority", "start_date", "due_date",
                  "sort_order"):
        val = getattr(data, field, None)
        if val is not None:
            setattr(t, field, val.strip() if isinstance(val, str) else val)

    if data.status is not None and int(data.status) != int(t.status):
        _apply_status(db, actor, t, int(data.status))

    t.updated_by = actor.user_id
    db.commit()
    record(db, actor.user_id, "work_task", t.id, "update", f"Sửa công việc: {t.title}")
    return _shape([t], task_enrich.collect(db, [t]))[0]


def _apply_status(db: Session, actor: Actor, t: WorkTask, status: int) -> None:
    """Đổi trạng thái hệ thống (B-06). Mở lại thì XÓA dấu hoàn thành, không giữ lại.

    Hoàn thành task cha KHÔNG tự tick hết việc con — giao diện cảnh báo "còn n
    việc con chưa xong" rồi hỏi xác nhận; dữ liệu để nguyên cho khớp sự thật.
    """
    t.status = status
    if status == int(WorkTaskStatus.DONE):
        t.completed_at = datetime.utcnow()
        t.completed_by = actor.employee_id
    else:
        t.completed_at = None
        t.completed_by = None


def delete_task(db: Session, actor: Actor, task_id: int) -> None:
    """Xóa MỀM (B-09 thùng rác). MEMBER chỉ xóa được task mình tạo (04 §3)."""
    t = get_task_or_403(db, actor, task_id, CAN_EDIT)
    lst = get_list_or_403(db, actor, t.list_id, CAN_EDIT)
    block_if_archived(lst)

    role = effective_role(db, actor.employee_id, t.list_id)
    if role > CAN_MANAGE and t.creator_employee_id != actor.employee_id:
        raise HTTPException(403, "Chỉ xóa được công việc do mình tạo")

    now = datetime.utcnow()
    t.deleted_at = now
    t.updated_by = actor.user_id
    #  Việc con chết theo cha: để lại thì chúng thành mồ côi, không màn nào hiện
    #  ra nữa mà vẫn đếm vào tiến độ nếu ai đó quên lọc.
    (db.query(WorkTask)
     .filter(WorkTask.parent_id == task_id, WorkTask.deleted_at.is_(None))
     .update({WorkTask.deleted_at: now}, synchronize_session=False))
    db.commit()
    record(db, actor.user_id, "work_task", task_id, "delete", f"Xóa công việc: {t.title}")


def set_assignees(db: Session, actor: Actor, task_id: int,
                  pic_ids: list[int], follower_ids: list[int]) -> dict:
    """Đặt lại toàn bộ người phụ trách + người theo dõi của task (B-02).

    NHIỀU PIC được, đúng như Lark (Q5). Một người chỉ một vai: có mặt ở cả hai
    danh sách thì PIC thắng.
    """
    t = get_task_or_403(db, actor, task_id, CAN_EDIT)
    block_if_archived(get_list_or_403(db, actor, t.list_id, CAN_EDIT))
    pics = [i for i in dict.fromkeys(pic_ids) if i]
    followers = [i for i in dict.fromkeys(follower_ids) if i and i not in pics]

    db.query(WorkTaskAssignee).filter(WorkTaskAssignee.task_id == task_id).delete(
        synchronize_session=False)
    for emp_id in pics:
        db.add(WorkTaskAssignee(task_id=task_id, employee_id=emp_id,
                                kind=int(WorkAssigneeKind.PIC),
                                created_by=actor.user_id, updated_by=actor.user_id))
    for emp_id in followers:
        db.add(WorkTaskAssignee(task_id=task_id, employee_id=emp_id,
                                kind=int(WorkAssigneeKind.FOLLOWER),
                                created_by=actor.user_id, updated_by=actor.user_id))
    db.commit()
    record(db, actor.user_id, "work_task", task_id, "update", "Đổi người phụ trách")
    return _shape([t], task_enrich.collect(db, [t]))[0]


def set_tags(db: Session, actor: Actor, task_id: int, tag_ids: list[int]) -> dict:
    """Đặt lại bộ tag của task. Tag phải thuộc CHÍNH list của task (B-05)."""
    t = get_task_or_403(db, actor, task_id, CAN_EDIT)
    block_if_archived(get_list_or_403(db, actor, t.list_id, CAN_EDIT))
    ids = [i for i in dict.fromkeys(tag_ids) if i]
    if ids:
        ok = {i for (i,) in db.query(WorkTag.id)
              .filter(WorkTag.id.in_(ids), WorkTag.list_id == t.list_id).all()}
        if set(ids) - ok:
            raise HTTPException(400, "Tag không thuộc danh sách của công việc này")
    db.query(WorkTaskTag).filter(WorkTaskTag.task_id == task_id).delete(
        synchronize_session=False)
    for tag_id in ids:
        db.add(WorkTaskTag(task_id=task_id, tag_id=tag_id,
                           created_by=actor.user_id, updated_by=actor.user_id))
    db.commit()
    return _shape([t], task_enrich.collect(db, [t]))[0]


def set_label(db: Session, actor: Actor, task_id: int, field_id: int, value) -> dict:
    """Đặt giá trị cho MỘT trường tùy biến. `value = None` = bỏ chọn.

    Hình dạng `value` tùy kiểu trường — xem `label_value_service.write_value`.
    Mọi phép kiểm kiểu nằm bên đó; ở đây chỉ lo quyền và mốc giao dịch.
    """
    t = get_task_or_403(db, actor, task_id, CAN_EDIT)
    block_if_archived(get_list_or_403(db, actor, t.list_id, CAN_EDIT))

    field = db.get(WorkLabelField, field_id)
    #  Trường của list KHÁC thì không có nghĩa gì ở đây — nhận bừa là task mang
    #  một nhãn không bao giờ hiện ra, vì giao diện chỉ vẽ trường của list mình.
    if not field or field.list_id != t.list_id:
        raise HTTPException(400, "Trường nhãn không thuộc danh sách này")

    label_values.write_value(db, field, task_id, value, actor.user_id)
    db.commit()
    return _shape([t], task_enrich.collect(db, [t]))[0]
