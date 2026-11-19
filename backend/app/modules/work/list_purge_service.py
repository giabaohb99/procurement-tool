"""XÓA VĨNH VIỄN một dự án (duoc-CR-783, anh Được 19/11/2026).

Anh Được: "kêu xóa luôn mà sao còn lưu trữ nữa — có 2 chức năng là xóa vĩnh viễn và đưa vào lưu trữ". Trước đây "xóa" dự
án chỉ là lưu trữ (`archive_list`, A-01). Nay hai thao tác tách hẳn: *Đưa vào lưu trữ* (giữ nguyên, khôi phục được) và
*Xóa vĩnh viễn* (hàm này — không lấy lại được).

Xóa những gì:
- việc (cả việc con, việc đang ở thùng rác), người phụ trách / theo dõi, giá trị trường tùy biến, liên kết phụ thuộc;
- bình luận của các việc (kèm lượt thích, nhắc tên) và tệp đính kèm của việc lẫn của bình luận — tệp trên kho lưu trữ chỉ
  mất khi không còn chỗ nào dùng (`delete_attachments_for`);
- cột kanban, trường tùy biến + lựa chọn, thành viên riêng, rồi chính dự án.

GIỮ LẠI nhật ký thao tác (`AuditLog`): đó là chỗ duy nhất trả lời được "ai đã xóa dự án nào, lúc nào". Đề xuất kế hoạch AI
(`tab_ai_plan.list_id`) cũng giữ — là lịch sử của đề xuất, không phải dữ liệu của dự án.

Xóa từng bảng TƯỜNG MINH chứ không dựa vào `ON DELETE CASCADE`: bài kiểm chạy SQLite không bật khóa ngoại, và bình luận /
tệp là bảng dùng chung không có khóa ngoại nào trỏ về việc. Chỉ chủ dự án (`CAN_OWN`), cùng cổng với lưu trữ.
"""
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.work.audit_entity import AUDIT_LIST
from app.modules.work.label_model import WorkLabelField, WorkLabelOption, WorkTaskLabel
from app.modules.work.link_model import WorkTaskLink
from app.modules.work.membership_service import CAN_OWN, Actor, get_list_or_403
from app.modules.work.model import WorkList, WorkListMember
from app.modules.work.task_model import WorkSection, WorkTask, WorkTaskAssignee

TASK_ENTITY = "work_task"


def _purge_task_comments_and_files(db: Session, task_ids: list[int]) -> None:
    """Bình luận của các việc (kèm thích / nhắc tên) và tệp của việc + của bình luận — cùng khuôn `forum.delete_post`."""
    from app.modules.attachment.service import delete_attachments_for
    from app.modules.comment.model import Comment, CommentMention, CommentReaction

    comment_ids = [i for (i,) in db.query(Comment.id)
                   .filter(Comment.entity == TASK_ENTITY, Comment.entity_id.in_(task_ids)).all()] if task_ids else []
    delete_attachments_for(db, [(TASK_ENTITY, t) for t in task_ids] + [("comment", c) for c in comment_ids],
                           commit=False)
    if comment_ids:
        db.query(CommentReaction).filter(CommentReaction.comment_id.in_(comment_ids)).delete(synchronize_session=False)
        db.query(CommentMention).filter(CommentMention.comment_id.in_(comment_ids)).delete(synchronize_session=False)
        db.query(Comment).filter(Comment.id.in_(comment_ids)).delete(synchronize_session=False)


def purge_list(db: Session, actor: Actor, list_id: int) -> dict:
    """Xóa vĩnh viễn dự án `list_id` và mọi thứ bên trong. Trả `{"tasks": số việc đã xóa}`."""
    lst = get_list_or_403(db, actor, list_id, CAN_OWN)
    name = lst.name
    task_ids = [i for (i,) in db.query(WorkTask.id).filter(WorkTask.list_id == list_id).all()]

    _purge_task_comments_and_files(db, task_ids)
    if task_ids:
        db.query(WorkTaskLabel).filter(WorkTaskLabel.task_id.in_(task_ids)).delete(synchronize_session=False)
        db.query(WorkTaskAssignee).filter(WorkTaskAssignee.task_id.in_(task_ids)).delete(synchronize_session=False)
        db.query(WorkTaskLink).filter(or_(WorkTaskLink.list_id == list_id,
                                          WorkTaskLink.predecessor_id.in_(task_ids),
                                          WorkTaskLink.successor_id.in_(task_ids))).delete(synchronize_session=False)
        #  Gỡ quan hệ cha – con trước rồi mới xóa: xóa cả loạt mà việc cha đi trước việc con là vướng khóa ngoại tự trỏ.
        db.query(WorkTask).filter(WorkTask.id.in_(task_ids)).update({WorkTask.parent_id: None},
                                                                   synchronize_session=False)
        db.query(WorkTask).filter(WorkTask.id.in_(task_ids)).delete(synchronize_session=False)
    else:
        db.query(WorkTaskLink).filter(WorkTaskLink.list_id == list_id).delete(synchronize_session=False)

    field_ids = [i for (i,) in db.query(WorkLabelField.id).filter(WorkLabelField.list_id == list_id).all()]
    if field_ids:
        db.query(WorkLabelOption).filter(WorkLabelOption.field_id.in_(field_ids)).delete(synchronize_session=False)
        db.query(WorkLabelField).filter(WorkLabelField.id.in_(field_ids)).delete(synchronize_session=False)
    db.query(WorkSection).filter(WorkSection.list_id == list_id).delete(synchronize_session=False)
    db.query(WorkListMember).filter(WorkListMember.list_id == list_id).delete(synchronize_session=False)
    db.query(WorkList).filter(WorkList.id == list_id).delete(synchronize_session=False)
    db.commit()
    record(db, actor.user_id, AUDIT_LIST, list_id, "delete",
           f"Xóa vĩnh viễn dự án {name} ({len(task_ids)} việc)")
    return {"tasks": len(task_ids)}
