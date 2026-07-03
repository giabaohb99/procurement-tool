from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success

from .model import Notification

router = APIRouter(prefix="/api/notifications", tags=["notification"])


def _out(n: Notification) -> dict:
    return {"id": n.id, "title": n.title, "body": n.body, "link": n.link or "",
            "is_read": bool(n.is_read), "at": n.created_at.isoformat() if n.created_at else ""}


@router.get("")
def list_notifications(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Thông báo trong app của chính người dùng (mới nhất) + số chưa đọc."""
    base = db.query(Notification).filter(Notification.user_id == user.id)
    items = base.order_by(Notification.id.desc()).limit(30).all()
    unread = base.filter(Notification.is_read == False).count()
    return success({"unread": unread, "items": [_out(n) for n in items]})


@router.post("/{nid}/read")
def mark_read(nid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == nid, Notification.user_id == user.id).first()
    if n and not n.is_read:
        n.is_read = True
        db.commit()
    return success(None)


@router.post("/read-all")
def mark_all_read(db: Session = Depends(get_db), user=Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == False)\
        .update({"is_read": True}, synchronize_session=False)
    db.commit()
    return success(None, "Đã đánh dấu tất cả là đã đọc")
