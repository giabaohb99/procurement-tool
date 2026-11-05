# -*- coding: utf-8 -*-
"""Dọn nhật ký do máy ghi MỘT LẦN — bao-CR-731. Đếm trước, người chủ gật rồi mới xóa thật.

Chạy trong container api:

    python -m scripts.don_nhat_ky_may --dry-run     # bảng số dòng SẼ dọn theo từng luật + ước tính MB, không ghi gì
    python -m scripts.don_nhat_ky_may --apply       # dọn thật theo lô nhỏ, in số dòng đã dọn + gợi ý OPTIMIZE TABLE

Luật ở `app/modules/system_log/machine_cleanup.py` (cùng luật với việc đêm `system_log.cleanup_machine_logs` 04:00), cộng
luật GET của `tab_request_log` (việc riêng `request_log.cleanup` 03:40) để một lần chạy thấy đủ.
⚠️ `--apply` KHÔNG tự chạy `OPTIMIZE TABLE`: lệnh đó dựng lại bảng, khóa ghi trong lúc chạy — người vận hành tự chọn giờ.
Sao lưu cơ sở dữ liệu trước khi `--apply` trên prod.
"""
import argparse
import sys

import app.core.all_models  # noqa: F401 — nạp đủ mapper

from sqlalchemy import func, select, text

from app.core.database import SessionLocal
from app.modules.system_log import machine_cleanup


def _avg_row_bytes(db, table: str) -> int:
    """Cỡ trung bình một dòng (dữ liệu + chỉ mục) theo thống kê của MySQL; máy khác MySQL trả 0."""
    if db.get_bind().dialect.name != "mysql":
        return 0
    row = db.execute(text(
        "SELECT table_rows, data_length + index_length FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = :t"), {"t": table}).first()
    if not row or not row[0]:
        return 0
    return int(row[1] or 0) // max(int(row[0]), 1)


def _estimate_mb(db, rule, now, rows: int) -> float:
    if not rows:
        return 0.0
    if rule.action == "clear_body":
        size = db.execute(select(func.coalesce(func.sum(func.length(rule.model.html_body)), 0))
                          .where(rule.condition(now))).scalar() or 0
        return round(int(size) / 1048576, 1)
    return round(rows * _avg_row_bytes(db, rule.table) / 1048576, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="chỉ đếm, không ghi gì")
    mode.add_argument("--apply", action="store_true", help="dọn thật")
    args = parser.parse_args()

    from datetime import datetime
    now = datetime.now()
    db = SessionLocal()
    try:
        plan = machine_cleanup.run(db, now=now, dry_run=True, include_all=True)
        by_key = {r.key: r for r in machine_cleanup.rules()}
        print(f"{'Luật':<16} {'Bảng':<16} {'Dòng':>10} {'~MB':>8}  Mô tả")
        total_mb = 0.0
        for item in plan["rules"]:
            mb = _estimate_mb(db, by_key[item["key"]], now, item["rows"])
            total_mb += mb
            print(f"{item['key']:<16} {item['table']:<16} {item['rows']:>10,} {mb:>8,.1f}  {item['label']}")
        print(f"{'Tổng':<33} {plan['total']:>10,} {total_mb:>8,.1f}")
        if args.dry_run:
            print("\nChạy thử — chưa ghi gì. Thêm --apply để dọn thật (sao lưu CSDL trước).")
            return 0

        done = machine_cleanup.run(db, now=now, include_all=True)
        print("\nĐã dọn:")
        for item in done["rules"]:
            note = f" ({item.get('status')}{', ' + item['reason'] if item.get('reason') else ''})"
            print(f"  {item['key']:<16} {item['rows']:>10,}{note}")
        tables = sorted({item["table"] for item in done["rules"] if item["rows"]})
        if tables:
            print("\nGợi ý (KHÔNG tự chạy — dựng lại bảng, khóa ghi lúc chạy; chọn giờ vắng):")
            for table in tables:
                print(f"  OPTIMIZE TABLE {table};")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
