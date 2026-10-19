"""Dọn `tab_ui_event` quá hạn (duoc-CR-641, phase 03) + dọn số gom/snapshot/nhãn quá 3 năm (CR-641, quyết định 4).

KHÁC `request_log.cleanup`: không chờ gói R2. Sự kiện giao diện là dữ liệu ĐO để gom, không phải
chứng cứ; bản bền của nó là `tab_usage_daily`. Xóa theo LÔ (khóa ngắn), trần số lô, chạm trần thì
`log.warning`. `dry_run=True` chỉ đếm.
"""
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import delete, func, select

from app.core import all_models  # noqa: F401 — nạp đủ model cho worker / script (cấu hình mapper cần mọi lớp)
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.vn_time import vn_today

from .model import UiEvent, UsageDaily, UserUsageLabel, UserUsageSnapshot

log = logging.getLogger("app.usage_profile.cleanup")

UI_EVENT_RETENTION_DAYS = 90
SUMMARY_RETENTION_DAYS = 3 * 365   # tab_usage_daily + snapshot + nhãn: giữ 3 năm
BATCH_SIZE = 2000
MAX_BATCHES = 500


def purge_in_batches(db, model, condition, id_col, *, batch_size: int = BATCH_SIZE,
                     max_batches: int = MAX_BATCHES) -> int:
    """Xóa theo lô id; trả số dòng đã xóa. Chạm trần số lô thì cảnh báo."""
    deleted = 0
    for _ in range(max_batches):
        ids = [r[0] for r in db.execute(select(id_col).where(condition).order_by(id_col).limit(batch_size))]
        if not ids:
            break
        db.execute(delete(model).where(id_col.in_(ids)))
        db.commit()
        deleted += len(ids)
    else:
        log.warning("Dọn %s chạm trần %s lô, còn dòng quá hạn chưa xóa.", model.__tablename__, max_batches)
    return deleted


def cleanup_ui_events(db, now: datetime | None = None, days: int = UI_EVENT_RETENTION_DAYS,
                      dry_run: bool = False, batch_size: int = BATCH_SIZE) -> dict:
    cutoff = (now or datetime.utcnow()) - timedelta(days=days)
    cond = UiEvent.occurred_at < cutoff
    if dry_run:
        n = db.execute(select(func.count()).select_from(UiEvent).where(cond)).scalar() or 0
        return {"status": "dry_run", "cutoff": cutoff.isoformat(), "matched": n}
    deleted = purge_in_batches(db, UiEvent, cond, UiEvent.id, batch_size=batch_size)
    return {"status": "success", "cutoff": cutoff.isoformat(), "deleted": deleted}


def cleanup_summaries(db, today: date | None = None, days: int = SUMMARY_RETENTION_DAYS,
                      batch_size: int = BATCH_SIZE) -> dict:
    cutoff = (today or vn_today()) - timedelta(days=days)
    return {
        "daily": purge_in_batches(db, UsageDaily, UsageDaily.day < cutoff, UsageDaily.id, batch_size=batch_size),
        "labels": purge_in_batches(db, UserUsageLabel, UserUsageLabel.period_start < cutoff,
                                   UserUsageLabel.id, batch_size=batch_size),
        "snapshots": purge_in_batches(db, UserUsageSnapshot, UserUsageSnapshot.period_start < cutoff,
                                      UserUsageSnapshot.id, batch_size=batch_size),
    }


@celery_app.task(name="usage.cleanup_ui_events")
def cleanup_ui_events_task(days: int = UI_EVENT_RETENTION_DAYS, dry_run: bool = False) -> dict:
    db = SessionLocal()
    try:
        result = cleanup_ui_events(db, days=days, dry_run=dry_run)
        if not dry_run:
            result["summaries"] = cleanup_summaries(db)
        log.info("Dọn dữ liệu hồ sơ cách làm việc: %s", result)
        return result
    finally:
        db.close()
