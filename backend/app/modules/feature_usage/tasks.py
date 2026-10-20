"""Celery của báo cáo «Mức dùng chức năng» (duoc-CR-655): gom ngày 04:45 (sau `usage.aggregate_daily` 04:30) + dọn 3 năm."""
import logging
from datetime import date, timedelta

from app.core import all_models  # noqa: F401 — nạp đủ model cho worker / script
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.vn_time import vn_today
from app.modules.usage_profile.daily_builder import DayTooOldError
from app.modules.usage_profile.tasks_cleanup import SUMMARY_RETENTION_DAYS, purge_in_batches

from .daily_builder import aggregate_day
from .model import FeatureUsageDaily

log = logging.getLogger("app.feature_usage")


@celery_app.task(name="feature_usage.aggregate_daily")
def aggregate_daily_task(day: str | None = None, force: bool = False) -> dict:
    """`day` YYYY-MM-DD; bỏ trống = hôm qua (giờ VN). Cũng dọn dòng quá 3 năm."""
    target = date.fromisoformat(day) if day else vn_today() - timedelta(days=1)
    db = SessionLocal()
    try:
        rows = aggregate_day(db, target, force=force)
        cutoff = vn_today() - timedelta(days=SUMMARY_RETENTION_DAYS)
        purged = purge_in_batches(db, FeatureUsageDaily, FeatureUsageDaily.day < cutoff, FeatureUsageDaily.id)
        log.info("Gom chức năng ngày %s: %s dòng, dọn %s", target, rows, purged)
        return {"day": target.isoformat(), "rows": rows, "purged": purged}
    except DayTooOldError:
        db.rollback()
        log.warning("Từ chối gom chức năng ngày %s: quá hạn giữ sự kiện thô", target)
        raise
    except Exception:
        db.rollback()
        log.exception("Gom chức năng ngày %s lỗi", target)
        raise
    finally:
        db.close()
