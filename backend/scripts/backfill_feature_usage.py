"""Gom bù `tab_feature_usage_daily` cho N ngày gần nhất (duoc-CR-655). Nguồn `tab_ui_event` chỉ giữ 90 ngày.

    docker compose exec -T api python -m scripts.backfill_feature_usage --days 90
"""
import argparse
import logging
from datetime import timedelta

from app.core import all_models  # noqa: F401
from app.core.database import SessionLocal
from app.core.vn_time import vn_today
from app.modules.feature_usage.daily_builder import aggregate_day

log = logging.getLogger("scripts.backfill_feature_usage")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    args = ap.parse_args()
    days = max(1, min(args.days, 89))
    db = SessionLocal()
    try:
        for back in range(days, 0, -1):
            day = vn_today() - timedelta(days=back)
            print(day, aggregate_day(db, day))
    finally:
        db.close()


if __name__ == "__main__":
    main()
