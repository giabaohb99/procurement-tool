"""Phân hệ Công việc — THÙNG RÁC của một dự án (B-09).

Xóa việc là xóa MỀM (`deleted_at`, xem `task_service.delete_task`); tệp này là nửa
còn lại: xem thùng rác và khôi phục.

Luật:

1. **Cùng cổng với xóa**: xem và khôi phục cần mức MEMBER (`CAN_EDIT`) — khách xem
   không thấy việc đã xóa. MEMBER chỉ khôi phục được việc do MÌNH tạo (đúng luật
   xóa ở `04-phan-quyen.md` §3); ADMIN/OWNER khôi phục được mọi việc.
2. **Việc con đi theo cha**: xóa cha thì con bị đánh dấu CÙNG một mốc `deleted_at`;
   khôi phục cha chỉ gỡ dấu của những con mang đúng mốc đó. Con đã bị xóa riêng từ
   trước (mốc khác) thì vẫn nằm trong thùng rác.
3. **Con không khôi phục trước cha**: cha còn trong thùng rác mà khôi phục con thì
   con thành mồ côi, không màn nào hiện — chặn và nói rõ phải khôi phục cha trước.
4. **Dự án đã lưu trữ thì khóa** như mọi thao tác ghi khác.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.work import task_enrich
from app.modules.work import task_service as tasks
from app.modules.work.audit_entity import AUDIT_TASK
from app.modules.work.membership_service import (CAN_EDIT, CAN_MANAGE, Actor,
                                                 block_if_archived, effective_role,
                                                 get_list_or_403)
from app.modules.work.people import employee_info
from app.modules.work.task_model import WorkTask

TRASH_LIMIT = 200   # đủ cho một dự án dùng thật; nhiều hơn thì nên dọn thùng rác chứ không cuộn


def _may_restore(role: int, actor: Actor, t: WorkTask) -> bool:
    return role <= CAN_MANAGE or t.creator_employee_id == actor.employee_id


def list_trash(db: Session, actor: Actor, list_id: int) -> list[dict]:
    """Việc đã xóa của dự án, mới xóa lên đầu. Việc con chỉ hiện khi cha còn sống
    (con của cha đã xóa đi theo cha, không liệt kê riêng)."""
    lst = get_list_or_403(db, actor, list_id, CAN_EDIT)
    role = effective_role(db, actor.employee_id, list_id)
    rows = (db.query(WorkTask)
            .filter(WorkTask.list_id == list_id, WorkTask.deleted_at.isnot(None))
            .order_by(WorkTask.deleted_at.desc(), WorkTask.id.desc())
            .limit(TRASH_LIMIT * 3).all())

    parent_ids = {t.parent_id for t in rows if t.parent_id}
    parents = {p.id: p for p in db.query(WorkTask).filter(WorkTask.id.in_(parent_ids)).all()} \
        if parent_ids else {}
    shown = [t for t in rows
             if not t.parent_id or (parents.get(t.parent_id) and parents[t.parent_id].deleted_at is None)]
    shown = shown[:TRASH_LIMIT]

    from app.modules.user.model import User
    deleter_ids = {t.updated_by for t in shown if t.updated_by}
    users = {u.id: u for u in db.query(User).filter(User.id.in_(deleter_ids)).all()} if deleter_ids else {}
    people = employee_info(db, [u.employee_id for u in users.values()])

    out = []
    for t in shown:
        deleter = users.get(t.updated_by)
        out.append({
            "id": t.id, "title": t.title, "kind": t.kind, "parent_id": t.parent_id,
            "parent_title": parents[t.parent_id].title if t.parent_id else "",
            "deleted_at": t.deleted_at,
            "deleted_by_name": (people.get(deleter.employee_id) or {}).get("name", "") if deleter else "",
            "can_restore": not lst.is_archived and _may_restore(role, actor, t),
        })
    return out


def restore_task(db: Session, actor: Actor, task_id: int) -> dict:
    """Khôi phục một việc (và các việc con đi theo nó lúc xóa) ra khỏi thùng rác."""
    t = db.get(WorkTask, task_id)
    if not t:
        raise HTTPException(403, "Không có quyền trên công việc này")
    lst = get_list_or_403(db, actor, t.list_id, CAN_EDIT)     # không phải thành viên -> 403
    if t.deleted_at is None:
        raise HTTPException(400, "Công việc này không nằm trong thùng rác")
    block_if_archived(lst)
    if not _may_restore(effective_role(db, actor.employee_id, t.list_id), actor, t):
        raise HTTPException(403, "Chỉ khôi phục được công việc do mình tạo")

    if t.parent_id:
        parent = db.get(WorkTask, t.parent_id)
        if parent is None or parent.deleted_at is not None:
            raise HTTPException(400, "Việc cha vẫn đang trong thùng rác — hãy khôi phục việc cha trước")

    stamp = t.deleted_at
    t.deleted_at = None
    t.updated_by = actor.user_id
    if not t.parent_id:
        (db.query(WorkTask)
         .filter(WorkTask.parent_id == t.id, WorkTask.deleted_at == stamp)
         .update({WorkTask.deleted_at: None}, synchronize_session=False))
        #  Cột cũ có thể đã bị xóa trong lúc việc nằm thùng rác (FK `SET NULL`) -> về cột đầu,
        #  không để việc sống lại mà không nằm cột nào trên kanban.
        if not t.section_id or not tasks._section_belongs(db, t.section_id, t.list_id):
            t.section_id = tasks._first_section_id(db, t.list_id)
    db.commit()
    record(db, actor.user_id, AUDIT_TASK, t.id, "update", f"Khôi phục công việc: {t.title}")
    return tasks._shape([t], task_enrich.collect(db, [t]))[0]
