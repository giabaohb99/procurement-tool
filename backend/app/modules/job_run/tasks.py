"""Việc nền của sổ việc chạy ngầm (bao-CR-703): dọn sổ quá hạn giữ (job_run_keep_days, mặc định 90, 0 = tắt)."""
from app.core.celery_app import celery_app
from app.core.database import SessionLocal

from . import service


@celery_app.task(name="job_run.cleanup")
def cleanup_task(days: int | None = None) -> dict:
    db = SessionLocal()
    try:
        return service.cleanup(db, days=days)
    finally:
        db.close()
