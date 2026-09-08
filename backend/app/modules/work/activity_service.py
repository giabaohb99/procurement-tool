"""Phân hệ Công việc — dòng hoạt động cấp DỰ ÁN (D-09, §8 của `05-giao-dien.md`).

Gộp nhật ký của cả một list: mọi việc trong list + thành viên vào ra + sửa chính
dự án và cột. Mới nhất trên cùng, lấy thêm theo trang khi cuộn.

Khác **E-04** (khối «Lịch sử thao tác» trong panel một việc): E-04 hỏi thẳng
`/api/audit-logs` theo đúng một `entity_id`, còn đây phải gom nhiều đối tượng
thuộc cùng một dự án — nên có endpoint riêng chứ không nhét thêm tham số vào
`/api/audit-logs` (endpoint đó dùng chung cho cả hệ và **không kiểm quyền theo
entity**; xem cảnh báo ở `shared/audit/audit-api.ts`).

Quyền: đi qua `get_list_or_403` như mọi đường khác của phân hệ — thấy được dự án
mới đọc được dòng hoạt động của nó (`04-phan-quyen.md` §2).
"""
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.modules.audit.controller import ACTION_LABEL
from app.modules.audit.model import AuditLog
from app.modules.work.audit_entity import (ACTIVITY_KIND_BY_ENTITY, AUDIT_LIST,
                                           AUDIT_LIST_MEMBER, AUDIT_TASK,
                                           WorkActivityKind)
from app.modules.work.membership_service import Actor, get_list_or_403
from app.modules.work.task_model import WorkTask

#  Trần một lần lấy. Dòng hoạt động cuộn vô hạn nên khách hàng tự quyết lấy bao
#  nhiêu, nhưng đừng cho phép quét sạch bảng trong một lượt.
MAX_LIMIT = 100


def _task_id_subquery(list_id: int):
    """Id mọi việc thuộc dự án — KỂ CẢ việc đã xóa mềm.

    Không lọc `deleted_at IS NULL`: dòng "Xóa công việc" là thứ người ta muốn
    thấy nhất trên nhật ký, lọc đi thì việc biến mất mà không ai biết ai xóa.
    """
    return select(WorkTask.id).where(WorkTask.list_id == list_id)


def _scope_condition(list_id: int):
    """Ba nguồn dòng hoạt động của MỘT dự án.

    `entity_id` chỉ so được trong phạm vi một `entity` — id việc, id dự án và id
    nhóm đánh số độc lập nhau (xem `audit_entity.py`).
    """
    return or_(
        and_(AuditLog.entity == AUDIT_TASK, AuditLog.entity_id.in_(_task_id_subquery(list_id))),
        and_(AuditLog.entity == AUDIT_LIST, AuditLog.entity_id == list_id),
        and_(AuditLog.entity == AUDIT_LIST_MEMBER, AuditLog.entity_id == list_id),
    )


def _resolve_actor_names(db: Session, user_ids: set[int]) -> dict[int, str]:
    """Tên người thao tác cho CẢ TRANG trong ba lượt truy vấn.

    `core.audit.resolve_actor` tra từng người một: 30 dòng nhật ký là 60 lượt
    query, mà một trang hoạt động gần như luôn chỉ có vài người khác nhau.
    """
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    ids = {i for i in user_ids if i}
    if not ids:
        return {}
    users = db.query(User).filter(User.id.in_(ids)).all()
    emp_ids = {u.employee_id for u in users if u.employee_id}
    names = {}
    if emp_ids:
        names = {e.id: e.full_name for e in
                 db.query(Employee).filter(Employee.id.in_(emp_ids)).all()}
    return {u.id: (names.get(u.employee_id) or u.email or f"User #{u.id}") for u in users}


def _resolve_task_titles(db: Session, task_ids: set[int]) -> dict[int, str]:
    """Tiêu đề việc để dòng nhật ký bấm sang được panel chi tiết."""
    if not task_ids:
        return {}
    rows = db.query(WorkTask.id, WorkTask.title).filter(WorkTask.id.in_(task_ids)).all()
    return {i: t for i, t in rows}


def list_activities(db: Session, actor: Actor, list_id: int,
                    kind: int | None = None, by: int | None = None,
                    offset: int = 0, limit: int = 30) -> dict:
    """Một trang dòng hoạt động, mới nhất trước.

    - `kind` — lọc theo loại sự kiện (`WorkActivityKind`).
    - `by`   — lọc theo NGƯỜI thao tác, nhận `user_id` (trục của `tab_audit_log`,
      không phải trục nhân sự của phân hệ).
    """
    get_list_or_403(db, actor, list_id)

    limit = max(1, min(limit, MAX_LIMIT))
    offset = max(0, offset)

    q = db.query(AuditLog).filter(_scope_condition(list_id))
    if kind is not None:
        entities = [e for e, k in ACTIVITY_KIND_BY_ENTITY.items() if int(k) == int(kind)]
        #  Mã lạ (người dùng tự sửa URL) → không có entity nào khớp, trả rỗng
        #  chứ đừng lặng lẽ bỏ qua bộ lọc và đổ ra tất cả.
        q = q.filter(AuditLog.entity.in_(entities or [""]))
    if by:
        q = q.filter(AuditLog.created_by == by)

    total = q.count()
    #  Sắp theo `id` chứ không `created_at`: hai thao tác trong cùng một giây là
    #  chuyện thường (tạo việc rồi gán người ngay), mà thứ tự nhảy lung tung
    #  giữa hai trang thì cuộn xuống sẽ thấy dòng lặp hoặc dòng mất.
    rows = q.order_by(AuditLog.id.desc()).offset(offset).limit(limit).all()

    names = _resolve_actor_names(db, {r.created_by for r in rows})
    titles = _resolve_task_titles(
        db, {r.entity_id for r in rows if r.entity == AUDIT_TASK})

    items = [_activity_out(r, names, titles) for r in rows]
    return {"items": items, "total": total, "has_more": offset + len(rows) < total}


def _activity_out(log: AuditLog, names: dict[int, str], titles: dict[int, str]) -> dict:
    kind = ACTIVITY_KIND_BY_ENTITY.get(log.entity, WorkActivityKind.LIST)
    task_id = log.entity_id if log.entity == AUDIT_TASK else None
    return {
        "id": log.id,
        "kind": int(kind),
        "action": log.action,
        "action_label": ACTION_LABEL.get(log.action, log.action),
        "message": log.message or "",
        "by": names.get(log.created_by) or "Hệ thống",
        "by_id": log.created_by,
        "at": log.created_at,
        #  Có `task_id` thì giao diện mở được panel chi tiết ngay từ dòng nhật
        #  ký. Việc đã xóa cứng thì không còn tiêu đề — để rỗng, giao diện tự
        #  thôi không dựng liên kết.
        "task_id": task_id,
        "task_title": titles.get(task_id, "") if task_id else "",
    }


def list_actors(db: Session, actor: Actor, list_id: int) -> list[dict]:
    """Những người TỪNG thao tác trên dự án — nguồn cho ô lọc «theo người».

    Lấy từ chính nhật ký chứ không lấy danh sách thành viên: người đã rời dự án
    vẫn còn dấu vết trong dòng hoạt động, thiếu họ trong ô lọc thì có dòng mà
    không lọc được.
    """
    get_list_or_403(db, actor, list_id)
    ids = {i for (i,) in db.query(AuditLog.created_by)
           .filter(_scope_condition(list_id)).distinct().all() if i}
    names = _resolve_actor_names(db, ids)
    out = [{"id": i, "name": names.get(i) or f"User #{i}"} for i in ids]
    return sorted(out, key=lambda x: x["name"])
