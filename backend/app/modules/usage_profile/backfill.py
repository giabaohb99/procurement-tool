"""Gom bù nhiều ngày: `python -m app.modules.usage_profile.backfill --days 90 [--from YYYY-MM-DD]`.

Tuần tự, commit mỗi ngày, ngủ 0,2 giây giữa các ngày (không chiếm DB). Lỗi một ngày không làm hỏng ngày khác:
bắt lỗi, log, đi tiếp, cuối cùng in danh sách ngày lỗi. Ngày cũ hơn hạn giữ nguồn thô (~89 ngày) bị TỪ CHỐI
(gom lại sẽ ghi đè số tốt bằng số thiếu); `--force` mới được bỏ qua, và có cảnh báo trong log.
"""
import argparse
import logging
import time
from datetime import date, timedelta

from app.core import all_models  # noqa: F401 — nạp đủ model cho worker / script (cấu hình mapper cần mọi lớp)
from app.core.database import SessionLocal
from app.core.vn_time import vn_today

from .daily_builder import DayTooOldError, aggregate_day, earliest_safe_day

log = logging.getLogger("app.usage_profile.backfill")
MAX_DAYS = 90


def backfill(days: int, start: date | None = None, sleep_s: float = 0.2, force: bool = False) -> dict:
    if not 1 <= days <= MAX_DAYS:
        raise ValueError(f"--days phải trong 1..{MAX_DAYS}")
    first = start or (vn_today() - timedelta(days=days))
    if not force:
        #  --days 90 chạm đúng ngày D-90 (nguồn đã bị dọn một phần): kẹp về ngày an toàn đầu tiên thay vì ghi đè số.
        first = max(first, earliest_safe_day())
    ok, failed = [], []
    for i in range(days):
        day = first + timedelta(days=i)
        if day >= vn_today():
            break
        db = SessionLocal()
        try:
            aggregate_day(db, day, force=force)
            ok.append(day.isoformat())
        except DayTooOldError:
            db.rollback()
            failed.append(day.isoformat())
        except Exception:  # noqa: BLE001 — một ngày hỏng không được chặn các ngày còn lại
            db.rollback()
            log.exception("Gom bù ngày %s lỗi", day)
            failed.append(day.isoformat())
        finally:
            db.close()
        time.sleep(sleep_s)
    return {"ok": len(ok), "failed": failed}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=MAX_DAYS)
    ap.add_argument("--from", dest="start", type=date.fromisoformat, default=None)
    ap.add_argument("--force", action="store_true", help="gom cả ngày quá hạn giữ nguồn thô (có thể ghi đè số tốt bằng số thiếu)")
    args = ap.parse_args()
    print(backfill(args.days, args.start, force=args.force))
