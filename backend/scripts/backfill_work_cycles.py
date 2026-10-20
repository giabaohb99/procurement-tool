"""Dựng lại TOÀN BỘ `tab_work_cycle` (duoc-CR-656, D1a). Chạy lại bao nhiêu lần cũng không nhân đôi dòng.

    docker compose exec -T api python -m scripts.backfill_work_cycles              # mọi loại
    docker compose exec -T api python -m scripts.backfill_work_cycles --kind 1 3   # chỉ YCMH + ĐMH
    docker compose exec -T api python -m scripts.backfill_work_cycles --dry-run    # chỉ đếm phiếu sẽ tính

Phạm vi lịch sử = những gì nhật ký còn giữ (change_log từ ngày bật, audit từ 01/07/2026) + cột mốc của chính bảng.
Phiếu không có dấu vết trong nhật ký được ghi `is_estimated = 1`. Sau khi dựng xong, đặt lại watermark để lượt đêm tiếp.
"""
import argparse
import time
from datetime import datetime

from app.core import all_models  # noqa: F401
from app.core.database import SessionLocal
from app.modules.capability import cycle_builder, cycle_sources
from app.modules.capability.cycle_specs import SPECS


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", type=int, nargs="*", help="chỉ các CycleKind này")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    kinds = set(args.kind) if args.kind else None
    db = SessionLocal()
    try:
        if args.dry_run:
            for spec in SPECS:
                if not kinds or int(spec.kind) in kinds:
                    print(spec.kind.name, len(cycle_sources.touched_ids(db, spec, None)), "phiếu")
            return
        start, now = time.time(), datetime.utcnow()
        result = cycle_builder.build_all(db, None, now, kinds)
        if not kinds:
            cycle_builder._set_watermark(db, now)
        for k, n in result.items():
            print(f"kind {k}: {n} dòng")
        print(f"xong trong {time.time() - start:.1f}s")
    finally:
        db.close()


if __name__ == "__main__":
    main()
