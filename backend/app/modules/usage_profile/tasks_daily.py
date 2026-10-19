"""Celery `usage.aggregate_daily` — gom ngày VN (mặc định HÔM QUA) vào `tab_usage_daily` (duoc-CR-641, phase 02)."""
import logging
from datetime import date, timedelta

from app.core import all_models  # noqa: F401 — nạp đủ model cho worker / script (cấu hình mapper cần mọi lớp)
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.vn_time import vn_today

from .daily_builder import DayTooOldError, aggregate_day

log = logging.getLogger("app.usage_profile.daily")


@celery_app.task(name="usage.aggregate_daily")
def aggregate_daily_task(day: str | None = None, force: bool = False) -> dict:
    """`day` dạng YYYY-MM-DD; bỏ trống = hôm qua theo giờ VN. Ngày quá hạn giữ nguồn thô bị từ chối trừ khi `force`."""
    target = date.fromisoformat(day) if day else vn_today() - timedelta(days=1)
    db = SessionLocal()
    try:
        n = aggregate_day(db, target, force=force)
        log.info("Gom ngày %s: %s dòng", target, n)
        return {"day": target.isoformat(), "rows": n}
    except DayTooOldError:
        db.rollback()
        log.warning("Từ chối gom ngày %s: quá hạn giữ nguồn thô", target)
        raise
    except Exception:
        db.rollback()
        log.exception("Gom ngày %s lỗi", target)
        raise
    finally:
        db.close()
