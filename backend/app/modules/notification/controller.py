from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success

from .model import Notification

router = APIRouter(prefix="/api/notifications", tags=["notification"])

RETENTION_DAYS = 90   # tự dọn thông báo ĐÃ ĐỌC cũ hơn ngưỡng này (chặn phình bảng)


def _out(n: Notification) -> dict:
    return {"id": n.id, "title": n.title, "body": n.body, "link": n.link or "",
            "is_read": bool(n.is_read), "at": n.created_at.isoformat() if n.created_at else ""}


def _prune_old(db: Session, user_id: int) -> None:
    """Xóa thông báo ĐÃ ĐỌC cũ > RETENTION_DAYS của user. Chỉ đụng dòng của chính họ."""
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == True,
        Notification.created_at < cutoff,
    ).delete(synchronize_session=False)
    db.commit()


@router.get("")
def list_notifications(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Thông báo của chính người dùng — phân trang + lọc.
    Query: page, page_size, unread=true (chỉ chưa đọc), q (tìm tiêu đề/nội dung).
    Trả: unread (tổng chưa đọc), total (theo bộ lọc), page, page_size, items."""
    _prune_old(db, user.id)
    base = db.query(Notification).filter(Notification.user_id == user.id)
    unread = base.filter(Notification.is_read == False).count()

    q = base
    if (request.query_params.get("unread") or "").lower() == "true":
        q = q.filter(Notification.is_read == False)
    search = (request.query_params.get("q") or "").strip()
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Notification.title.ilike(like), Notification.body.ilike(like)))

    total = q.count()
    try:
        page = max(1, int(request.query_params.get("page") or 1))
    except (ValueError, TypeError):
        page = 1
    try:
        size = min(100, max(1, int(request.query_params.get("page_size") or 20)))
    except (ValueError, TypeError):
        size = 20
    items = (q.order_by(Notification.id.desc())
             .offset((page - 1) * size).limit(size).all())
    return success({"unread": unread, "total": total, "page": page, "page_size": size,
                    "items": [_out(n) for n in items]})


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


@router.delete("/read")
def delete_read(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Xóa tất cả thông báo ĐÃ ĐỌC của người dùng."""
    n = db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == True)\
        .delete(synchronize_session=False)
    db.commit()
    return success({"deleted": n}, f"Đã xóa {n} thông báo đã đọc")


@router.delete("/{nid}")
def delete_one(nid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Xóa 1 thông báo của chính người dùng."""
    db.query(Notification).filter(Notification.id == nid, Notification.user_id == user.id)\
        .delete(synchronize_session=False)
    db.commit()
    return success(None, "Đã xóa thông báo")
