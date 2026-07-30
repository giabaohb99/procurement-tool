"""Task dọn dẹp thông báo cũ — chạy theo lịch (celery-beat).

Thông báo in-app cũ hơn NOTIFICATION_KEEP_DAYS ngày sẽ bị xóa để CSDL gọn.
Xóa cả đã đọc lẫn chưa đọc (quá hạn thì không còn ý nghĩa theo dõi).
"""
from datetime import datetime, timedelta

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal

from .model import Notification


@celery_app.task(name="notification.cleanup")
def cleanup_notifications_task(days: int | None = None) -> dict:
    """Xóa thông báo cũ hơn `days` ngày (mặc định lấy từ config). Trả số dòng đã xóa."""
    keep_days = days if days is not None else settings.NOTIFICATION_KEEP_DAYS
    cutoff = datetime.now() - timedelta(days=keep_days)
    db = SessionLocal()
    try:
        n = (
            db.query(Notification)
            .filter(Notification.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        return {"status": "success", "deleted": n, "cutoff": cutoff.isoformat()}
    except Exception as e:  # noqa: BLE001
        db.rollback()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
