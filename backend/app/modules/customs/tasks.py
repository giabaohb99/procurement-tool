"""Việc nền của phân hệ hải quan — bao-CR-698: dọn nhật ký từng dòng của lô nạp (hằng đêm 02:45)."""
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal

from .row_log_cleanup import cleanup

log = logging.getLogger("app.customs.tasks")


@celery_app.task(name="customs.cleanup_row_logs")
def cleanup_row_logs_task(days: int | None = None) -> dict:
    """`days` để chạy tay với hạn khác; mặc định lấy `customs_row_log_keep_days` (0 = tắt)."""
    db = SessionLocal()
    try:
        return cleanup(db, days=days)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        log.exception("Dọn nhật ký dòng hải quan hỏng")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
