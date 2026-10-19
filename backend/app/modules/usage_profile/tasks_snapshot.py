"""Celery `usage.build_weekly_snapshots` — dựng snapshot + nhãn tuần (duoc-CR-641, phase 04).

Trước khi dựng, TỰ LÀNH: gom lại các ngày còn thiếu trong cửa sổ 4 tuần (job ngày lỡ chạy / máy tắt) để snapshot
không dựa trên cửa sổ có lỗ. Ngày chưa có dòng nào trong `tab_usage_daily` mới bị gom bù (ngày đã có thì giữ nguyên).
"""
import logging
from datetime import date, timedelta

from sqlalchemy import select

from app.core import all_models  # noqa: F401 — nạp đủ model cho worker / script (cấu hình mapper cần mọi lớp)
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.vn_time import vn_today

from .daily_builder import aggregate_day
from .model import UsageDaily
from .snapshot_builder import build_snapshots, last_full_week_start, monday_of
from .snapshot_sources import WINDOW_WEEKS

log = logging.getLogger("app.usage_profile.snapshot")


def heal_missing_days(db, week_start: date) -> list[str]:
    lo = week_start - timedelta(weeks=WINDOW_WEEKS - 1)
    hi = min(week_start + timedelta(days=7), vn_today())   # không gom ngày chưa kết thúc
    have = {d for (d,) in db.execute(select(UsageDaily.day).where(UsageDaily.day >= lo, UsageDaily.day < hi).distinct())}
    healed = []
    day = lo
    while day < hi:
        if day not in have:
            try:
                aggregate_day(db, day)
                healed.append(day.isoformat())
            except Exception:  # noqa: BLE001 — một ngày hỏng không chặn snapshot
                db.rollback()
                log.exception("Tự lành ngày %s lỗi", day)
        day += timedelta(days=1)
    return healed


@celery_app.task(name="usage.build_weekly_snapshots")
def build_weekly_snapshots_task(week_start: str | None = None) -> dict:
    """`week_start` YYYY-MM-DD (thứ Hai); bỏ trống = tuần đã kết thúc gần nhất."""
    target = monday_of(date.fromisoformat(week_start)) if week_start else last_full_week_start()
    db = SessionLocal()
    try:
        healed = heal_missing_days(db, target)
        n = build_snapshots(db, target)
        log.info("Snapshot tuần %s: %s người, tự lành %s ngày", target, n, len(healed))
        return {"week_start": target.isoformat(), "snapshots": n, "healed_days": healed}
    except Exception:
        db.rollback()
        log.exception("Dựng snapshot tuần %s lỗi", target)
        raise
    finally:
        db.close()
