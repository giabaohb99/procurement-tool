"""Phân hệ Công việc — nối vào chuông thông báo (W3: F-01, F-04).

Ba sự kiện sinh chuông, mỗi sự kiện một thông báo RIÊNG (không gộp):

| sự kiện                 | người nhận                          | hàm                     |
|-------------------------|-------------------------------------|-------------------------|
| giao việc (F-01)        | PIC MỚI được thêm vào việc          | `notify_assigned`       |
| đổi trạng thái (F-04)   | PIC + người theo dõi                | `notify_status_changed` |
| bình luận mới (F-04)    | PIC + người theo dõi (+ người cũ)   | `task_watcher_user_ids` |

Luật chung:

- **Không báo cho chính người thao tác** — tự giao việc cho mình, tự đổi trạng
  thái việc của mình thì không có chuông nào kêu.
- Người nhận quy từ trục NHÂN SỰ (`employee_id`) sang TÀI KHOẢN đang hoạt động;
  nhân sự chưa có tài khoản thì bỏ qua (không có chuông nào để kêu).
- **Chỉ báo cho người còn XEM được việc** (`audience_user_ids`): còn là thành viên
  dự án chứa việc VÀ có `work_task.read`. Gỡ người khỏi dự án KHÔNG xóa dòng
  PIC/theo dõi của họ, nên thiếu lớp lọc này thì người đã rời dự án (hay nhân sự
  ngoài dự án bị gán qua API) vẫn nhận chuông kèm tên việc + trích bình luận.
- **Chuông hỏng không được làm hỏng thao tác chính**: việc đã lưu xong rồi mới
  báo, lỗi nào trong lúc báo cũng nuốt + ghi log — người dùng giao việc xong mà
  bị 500 vì chuông lỗi là tệ hơn việc không có chuông.
- Dùng thẳng bảng `tab_notification` giống `comment/controller._push` và
  `trigger_notification`; KHÔNG dùng `trigger_notification` vì hàm đó dành cho
  chứng từ (nhãn "Yêu cầu mua hàng"/"Phiếu khảo sát", email workflow) và sẽ
  commit/gửi mail ngoài ý muốn.
- Link đích là `/project/tasks/{id}` — trang trung chuyển `TaskRedirectPage`
  tra dự án chứa việc rồi mở panel (khớp `core/comment_registry.py`).
"""
import logging

from sqlalchemy.orm import Session

from app.modules.work.model import (WorkAssigneeKind, WorkGroup, WorkGroupMember,
                                    WorkList, WorkListMember, WorkTaskStatus)
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

logger = logging.getLogger("app.work.notify")

TASK_LINK = "/project/tasks/{id}"

_STATUS_TEXT = {
    int(WorkTaskStatus.OPEN): "mở lại",
    int(WorkTaskStatus.DONE): "hoàn thành",
    int(WorkTaskStatus.CANCELLED): "hủy",
}


def task_link(task_id: int) -> str:
    return TASK_LINK.format(id=task_id)


def _user_ids_of_employees(db: Session, employee_ids) -> dict[int, int]:
    """`{user_id: employee_id}` của tài khoản đang hoạt động gắn với các nhân sự."""
    from app.modules.user.model import User

    ids = [int(i) for i in set(employee_ids or []) if i]
    if not ids:
        return {}
    rows = (db.query(User.id, User.employee_id)
            .filter(User.employee_id.in_(ids), User.is_active == True).all())  # noqa: E712
    return {uid: eid for uid, eid in rows}


def _actor_name(db: Session, actor) -> str:
    from app.modules.notification.service import get_user_display_name
    from app.modules.user.model import User

    user = db.get(User, actor.user_id)
    return get_user_display_name(db, user) if user else "Một thành viên"


def _clip(text: str, limit: int = 120) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _list_member_employee_ids(db: Session, list_id: int) -> set[int]:
    """Mọi nhân sự có vai trò hiệu lực trên list — cùng nguồn với
    `membership_service.effective_role` (mời riêng · nhóm chứa list · nhóm ông),
    gom một lượt thay vì hỏi từng người."""
    lst = db.get(WorkList, list_id) if list_id else None
    if not lst:
        return set()
    ids = {e for (e,) in db.query(WorkListMember.employee_id)
           .filter(WorkListMember.list_id == list_id).all()}
    if lst.group_id:
        chain = [lst.group_id]
        grp = db.get(WorkGroup, lst.group_id)
        if grp and grp.parent_id:
            chain.append(grp.parent_id)
        ids |= {e for (e,) in db.query(WorkGroupMember.employee_id)
                .filter(WorkGroupMember.group_id.in_(chain)).all()}
    ids.discard(0)
    return ids


def audience_user_ids(db: Session, task: WorkTask, user_ids) -> set[int]:
    """Lọc `user_ids` còn XEM được `task`: tài khoản hoạt động, nhân sự còn là thành
    viên dự án chứa việc, và vai trò có `work_task.read` (cùng hai cổng của
    `comment.service.resolve_doc`). Người nhận mỗi việc chỉ vài người nên hỏi quyền
    từng người (có bộ đệm 60 giây của `get_perm_profile`) là đủ rẻ."""
    from app.core.auth import user_has_permission
    from app.modules.user.model import User

    ids = {int(u) for u in (user_ids or []) if u}
    if not ids or task is None:
        return set()
    members = _list_member_employee_ids(db, task.list_id)
    if not members:
        return set()
    users = (db.query(User)
             .filter(User.id.in_(ids), User.is_active == True,  # noqa: E712
                     User.employee_id.in_(members)).all())
    return {u.id for u in users if user_has_permission(db, u, "work_task", "read")}


def send_bell(db: Session, task: WorkTask, employee_ids, title: str, body: str, link: str,
              actor, background_tasks=None) -> int:
    """Ghi chuông cho các NHÂN SỰ (trừ người thao tác, chỉ người còn xem được `task`).
    Trả số người đã được báo."""
    try:
        targets = _user_ids_of_employees(db, employee_ids)
        #  Bỏ chính người thao tác — kể cả tài khoản khác cùng một nhân sự với họ.
        user_ids = audience_user_ids(db, task, [u for u, e in targets.items()
                                                if u != actor.user_id and e != actor.employee_id])
    except Exception:
        db.rollback()
        logger.warning("Không tra được tài khoản người nhận chuông %s", link, exc_info=True)
        return 0
    return send_bell_users(db, user_ids, title, body, link, actor, background_tasks)


def send_bell_users(db: Session, user_ids, title: str, body: str, link: str, actor,
                    background_tasks=None) -> int:
    """Ghi chuông cho các TÀI KHOẢN (đã loại người thao tác ở nơi gọi, hàm này loại thêm
    đúng `actor.user_id`). Không bao giờ ném lỗi ra ngoài — xem ghi chú đầu tệp."""
    try:
        from app.modules.notification.model import Notification

        targets = sorted({int(u) for u in (user_ids or []) if u and int(u) != actor.user_id})
        if not targets:
            return 0
        for uid in targets:
            db.add(Notification(user_id=uid, title=title, body=body, link=link,
                                created_by=actor.user_id))
        db.commit()
        _push(targets, title, body, link, background_tasks)
        return len(targets)
    except Exception:
        db.rollback()
        logger.warning("Không ghi được chuông cho %s", link, exc_info=True)
        return 0


def _push(user_ids: list[int], title: str, body: str, link: str, background_tasks) -> None:
    """Web Push nền, best-effort — cùng cách `comment/controller._push` làm."""
    try:
        from app.core.database import SessionLocal
        from app.modules.push import service as push_service

        if background_tasks is not None:
            background_tasks.add_task(push_service.send_to_users, SessionLocal,
                                      user_ids, title, body, link)
        else:
            push_service.send_to_users(SessionLocal, user_ids, title, body, link)
    except Exception:
        logger.debug("Đẩy Web Push thất bại", exc_info=True)


def watcher_employee_ids(db: Session, task_id: int, kinds=None) -> list[int]:
    """Nhân sự đang PIC hoặc theo dõi một việc. Việc con không kế thừa từ cha."""
    q = db.query(WorkTaskAssignee.employee_id).filter(WorkTaskAssignee.task_id == task_id)
    if kinds:
        q = q.filter(WorkTaskAssignee.kind.in_([int(k) for k in kinds]))
    return [e for (e,) in q.all() if e]


def task_watcher_user_ids(db: Session, task_id: int) -> set[int]:
    """Tài khoản của PIC + người theo dõi (CHƯA lọc quyền xem — nơi gọi lọc bằng
    `audience_user_ids`)."""
    return set(_user_ids_of_employees(db, watcher_employee_ids(db, task_id)))


def comment_recipient_user_ids(db: Session, task: WorkTask, user_ids) -> set[int]:
    """`comment/service.recipient_ids` gọi cho bình luận mới (F-04): cộng PIC + người
    theo dõi vào bộ người nhận, rồi bỏ ai không còn xem được việc."""
    return audience_user_ids(db, task, set(user_ids or []) | task_watcher_user_ids(db, task.id))


def notify_assigned(db: Session, actor, task: WorkTask, new_pic_ids, background_tasks=None) -> int:
    """F-01 — "Bạn được giao việc". Chỉ gọi với PIC MỚI (không có trong bộ cũ)."""
    if not new_pic_ids:
        return 0
    try:
        who = _actor_name(db, actor)
        due = f" · hạn {task.due_date}" if task.due_date else ""
        return send_bell(db, task, new_pic_ids, f"Bạn được giao việc: {_clip(task.title, 80)}",
                         f"{who} đã giao cho bạn việc \"{_clip(task.title)}\"{due}.",
                         task_link(task.id), actor, background_tasks)
    except Exception:
        db.rollback()
        logger.warning("Không báo được giao việc %s", task.id, exc_info=True)
        return 0


def notify_status_changed(db: Session, actor, task: WorkTask, new_status: int,
                          background_tasks=None) -> int:
    """F-04 — đổi trạng thái báo PIC + người theo dõi."""
    try:
        verb = _STATUS_TEXT.get(int(new_status), "cập nhật")
        who = _actor_name(db, actor)
        title = f"Việc \"{_clip(task.title, 80)}\" đã {verb}"
        return send_bell(db, task, watcher_employee_ids(db, task.id), title,
                         f"{who} vừa chuyển việc \"{_clip(task.title)}\" sang trạng thái {verb}.",
                         task_link(task.id), actor, background_tasks)
    except Exception:
        db.rollback()
        logger.warning("Không báo được đổi trạng thái việc %s", task.id, exc_info=True)
        return 0
