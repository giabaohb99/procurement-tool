"""Việc nền của phân hệ hải quan — bao-CR-698: dọn nhật ký từng dòng của lô nạp (hằng đêm 02:45);
bao-CR-699: gộp dòng hàng trùng (ngày 1 và 16 lúc 03:30)."""
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal

from app.core import app_settings

from . import line_merge
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


@celery_app.task(name="customs.merge_duplicate_lines")
def merge_duplicate_lines_task(dry_run: bool = False) -> dict:
    """Gộp dòng hàng trùng (`line_merge`). Công tắc customs_line_merge_enabled tắt thì bỏ qua; `dry_run` chỉ đếm."""
    if not app_settings.get("customs_line_merge_enabled") and not dry_run:
        return {"status": "disabled"}
    db = SessionLocal()
    try:
        return line_merge.run(db, dry_run=dry_run)
    except Exception as e:  # noqa: BLE001
        db.rollback()
        log.exception("Gộp dòng hải quan trùng hỏng")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
