"""Phân hệ Công việc — SỬA bình luận của chính mình (E-05).

Bình luận của việc nằm ở bảng dùng chung `tab_comment` (entity `work_task`), nên
tệp này CHỈ thêm phần còn thiếu — sửa — và mượn hàm ghi nhắc tên của
`comment.service`. Cổng quyền là `get_task_or_403` của phân hệ (cùng mức `CAN_EDIT`
mà `comment.service.resolve_doc` đòi khi GỬI bình luận; bài D1 bắt mọi route của
phân hệ đi qua cửa này). Tạo/xóa/thích vẫn đi cửa chung `/api/comments`.

Ba luật:

1. **Chỉ người viết sửa được** — khác với XÓA (quản trị `user.delete` được dọn nội
   dung không phù hợp). Sửa là đổi lời của người khác nói, không có lý do nào cho
   phép, kể cả OWNER của dự án; muốn bỏ thì xóa.
2. **Cần quyền GHI** (`mode="write"`): khách xem (VIEWER) không sửa được, và người
   đã bị gỡ khỏi dự án thì 403 dù vẫn là người viết.
3. **Nhắc tên làm lại từ đầu**: nội dung mới có thể thêm/bỏ `@`. Chỉ người MỚI
   được nhắc mới nhận chuông — sửa lỗi chính tả không được kéo chuông kêu lại.
"""
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.comment import service as comment_service
from app.modules.comment.model import Comment, CommentMention
from app.modules.work import notify_service as notify
from app.modules.work.membership_service import CAN_EDIT, Actor
from app.modules.work.task_model import WorkTask

logger = logging.getLogger("app.work.notify")


def edit_comment(db: Session, actor: Actor, user, task_id: int, comment_id: int, body: str,
                 background_tasks=None) -> dict:
    """Đổi nội dung bình luận `comment_id` của việc `task_id`; trả bình luận đã đóng gói.

    `actor` để gác tư cách thành viên (cửa `get_task_or_403`, bài D1 soi đúng cửa này),
    `user` để đóng gói bình luận (`can_edit`/`liked`… tính theo tài khoản)."""
    from app.modules.comment.controller import _pack  # nhập muộn: tránh vòng import
    from app.modules.work.task_service import get_task_or_403

    #  Mức GHI (MEMBER trở lên) của dự án chứa việc — khách xem / người đã rời dự án 403.
    #  RBAC `work_task.write` đã gác ở route.
    task = get_task_or_403(db, actor, task_id, CAN_EDIT)

    c = db.get(Comment, comment_id)
    #  Sai việc cũng là "không thấy": không để lộ bình luận của việc khác qua đường này.
    if not c or c.entity != "work_task" or c.entity_id != task_id:
        raise HTTPException(404, "Không tìm thấy bình luận")
    if c.created_by != user.id:
        raise HTTPException(403, "Chỉ người viết mới sửa được bình luận này")

    body = (body or "").strip()
    has_files = bool(comment_service.file_map(db, [c.id]).get(c.id))
    if not body and not has_files:
        raise HTTPException(400, "Nội dung bình luận không được để trống")
    if len(body) > comment_service.MAX_BODY:
        raise HTTPException(400, f"Bình luận tối đa {comment_service.MAX_BODY} ký tự")

    before = set(comment_service.mention_map(db, [c.id]).get(c.id, []))
    c.body = body
    c.updated_by = user.id
    db.query(CommentMention).filter(CommentMention.comment_id == c.id).delete(
        synchronize_session=False)
    #  MỘT giao dịch cho nội dung + bộ nhắc tên: `save_mentions` tự commit khi có
    #  người được nhắc, còn không thì commit dưới đây — không có lúc nội dung mới
    #  đã lưu mà bộ nhắc tên đã bị xóa sạch (lỗi giữa chừng = mất nhắc tên cũ).
    now_mentioned = comment_service.save_mentions(db, c, user.id)
    db.commit()
    db.refresh(c)

    fresh = [u for u in now_mentioned if u not in before]
    if fresh:
        _notify_new_mentions(db, actor, user, task, c, fresh, background_tasks)
    return _pack(db, [c], user, with_reply_count=False)[0]


def _notify_new_mentions(db: Session, actor: Actor, user, task: WorkTask, c: Comment, user_ids,
                         background_tasks) -> None:
    """Chuông "được nhắc tên" cho người MỚI được @ — chỉ người còn xem được việc.
    Bình luận đã lưu xong: lỗi ở đây nuốt + ghi log, không thành 500."""
    from app.modules.notification.service import get_user_display_name

    try:
        allowed = notify.audience_user_ids(db, task, user_ids)
        targets = [u for u in user_ids if u in allowed]
        if not targets:
            return
        excerpt = comment_service.strip_mentions(db, c.body)
        excerpt = excerpt if len(excerpt) <= 140 else excerpt[:140].rstrip() + "…"
        notify.send_bell_users(
            db, targets, f"{task.title} — Bạn được nhắc tên",
            f"{get_user_display_name(db, user)} đã nhắc bạn trong việc \"{task.title}\": {excerpt}",
            notify.task_link(task.id), actor, background_tasks)
    except Exception:
        db.rollback()
        logger.warning("Không báo được nhắc tên khi sửa bình luận %s", c.id, exc_info=True)
