"""Dịch vụ dùng chung cho Việc cần làm (CR-215).

Đứng riêng để cả `/api/alerts` (module alert) lẫn `/api/dashboard/tasks` cùng
đọc một trạng thái "đã đánh dấu xong" — nhét vào một controller thì bên kia
phải import chéo controller, vòng vèo hơn.
"""
from sqlalchemy.orm import Session

from .model import UserTaskDismiss

#  Trần một lần gửi — không ai đánh dấu tay nghìn việc, mà script bắn bừa thì có.
MAX_DISMISS_KEYS = 500
MAX_KEY_LEN = 64


def load_dismissed_keys(db: Session, user) -> set[str]:
    """Mọi task_key mà tài khoản này đã đánh dấu xong."""
    rows = db.query(UserTaskDismiss.task_key).filter(
        UserTaskDismiss.user_id == user.id).all()
    return {key for (key,) in rows}


def dismiss_keys(db: Session, user, keys: list[str]) -> int:
    """Đánh dấu xong một loạt việc; key đã có thì bỏ qua. Trả về số key mới ghi."""
    clean = [k.strip() for k in keys if k and len(k.strip()) <= MAX_KEY_LEN]
    clean = list(dict.fromkeys(clean))[:MAX_DISMISS_KEYS]
    if not clean:
        return 0
    existing = load_dismissed_keys(db, user)
    added = 0
    for key in clean:
        if key in existing:
            continue
        db.add(UserTaskDismiss(user_id=user.id, task_key=key,
                               created_by=user.id, updated_by=user.id))
        added += 1
    if added:
        db.commit()
    return added


def restore_keys(db: Session, user, keys: list[str], restore_all: bool = False) -> int:
    """Khôi phục (bỏ đánh dấu xong). `restore_all=True` = xóa sạch của tài khoản."""
    query = db.query(UserTaskDismiss).filter(UserTaskDismiss.user_id == user.id)
    if not restore_all:
        clean = [k.strip() for k in keys if k and len(k.strip()) <= MAX_KEY_LEN]
        if not clean:
            return 0
        query = query.filter(UserTaskDismiss.task_key.in_(clean[:MAX_DISMISS_KEYS]))
    removed = query.delete(synchronize_session=False)
    db.commit()
    return removed
