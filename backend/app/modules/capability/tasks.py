"""Celery `capability.build_cycles` — dựng vòng đời phiếu gia tăng 05:00 VN + dọn dòng quá 3 năm (duoc-CR-656, D1a)."""
import logging
from datetime import datetime, timedelta

from app.core import all_models  # noqa: F401 — nạp đủ model cho worker (cấu hình mapper cần mọi lớp)
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.modules.capability import cycle_builder
from app.modules.capability.model import WorkCycle

log = logging.getLogger("app.capability.tasks")

RETENTION_DAYS = 3 * 365


@celery_app.task(name="capability.build_cycles")
def build_cycles_task() -> dict:
    db = SessionLocal()
    try:
        result = cycle_builder.run_incremental(db)
        cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
        #  Dọn theo ngày XONG: dòng còn mở (done_at NULL) không bao giờ bị dọn ở đây.
        removed = db.query(WorkCycle).filter(WorkCycle.done_at < cutoff).delete(synchronize_session=False)
        db.commit()
        result["purged"] = removed
        return result
    except Exception:
        db.rollback()
        log.exception("Dựng vòng đời phiếu lỗi")
        raise
    finally:
        db.close()
