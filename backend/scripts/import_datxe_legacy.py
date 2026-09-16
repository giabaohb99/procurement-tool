# -*- coding: utf-8 -*-
"""Nạp dữ liệu ĐẶT XE hệ cũ (2 tệp Excel) vào module `vehicle_booking`.

Nguồn (xuất từ `app.degoholding.vn`, 15/09/2026):
  - `import-yeu-cau-dat-xe-cong-tac.xlsx`  309 dòng → TYPE_CAR
  - `import-yeu-cau-giao-hang.xlsx`         46 dòng → TYPE_DELIVERY

Bốn quyết định đã chốt với người dùng (15/09/2026):
  1. Nạp CẢ HAI tệp.
  2. `--wipe` xóa sạch phiếu demo của `seed_datxe_demo.py` trước khi nạp, mã
     đánh lại từ DX001. (Kiểm rồi: không phiên duyệt nào trỏ vào phiếu demo.)
  3. Dòng có người tạo KHÔNG tra được hồ sơ nhân sự thì BỎ — 18 dòng, 5 người
     (Phạm Phương Thuỳ · Trần Thị Hải Sang · Trần Thị Mỹ Giang · Nguyễn Anh
     Kiệt · Phạm Thị Thanh Nhi). Còn 337 dòng.
  4. Biển số ghi tay (`xe thuê` · `xe thê` · `XE THUÊ NGOÀI`, 13 dòng) → để
     trống khóa xe, nguyên văn vào `note`.

Quy tắc chuyển từng cột nằm ở `datxe_legacy_mapping.py`.

Chạy (LOCAL / DEV):
    docker compose cp <file>.xlsx api:/tmp/datxe.xlsx
    docker compose cp <file>.xlsx api:/tmp/giaohang.xlsx
    docker compose exec -T -e PYTHONPATH=/app api python -m scripts.import_datxe_legacy \\
        --car /tmp/datxe.xlsx --delivery /tmp/giaohang.xlsx --wipe

Thêm `--dry-run` để xem báo cáo mà không ghi DB. KHÔNG idempotent: chạy lại mà
không `--wipe` là nhân đôi dữ liệu (nguồn không có mã yêu cầu để so trùng).
"""
import argparse
import sys
from collections import Counter

import openpyxl

import app.core.all_models  # noqa: F401 — nạp đủ model để mapper resolve quan hệ
from app.core.database import SessionLocal
from app.modules.company.model import Company
from app.modules.employee.model import Employee
from app.modules.user.model import User
from app.modules.vehicle_booking.model import Driver, Vehicle, VehicleBooking
from scripts.datxe_legacy_mapping import Lookups, build_kwargs, parse_legacy_dt


def read_sheet(path: str) -> list[dict]:
    """Đọc sheet đầu → list dict theo tiêu đề cột. Bỏ dòng trắng hoàn toàn."""
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = book.worksheets[0]
    rows = list(sheet.iter_rows(values_only=True))
    book.close()
    if not rows:
        return []
    header = [("" if h is None else str(h).strip()) for h in rows[0]]
    out = []
    for row in rows[1:]:
        if not any(c is not None and str(c).strip() for c in row):
            continue
        out.append({header[i]: (row[i] if i < len(row) else None)
                    for i in range(len(header))})
    return out


def sort_key(row: dict, is_delivery: bool):
    """Xếp theo mốc thời gian sớm nhất để mã DX chạy đúng thứ tự lịch sử."""
    start_key = "Thời gian lấy hàng" if is_delivery else "Thời gian đi"
    stamps = [d for d in (parse_legacy_dt(row.get("Thời gian điều phối")),
                          parse_legacy_dt(row.get(start_key))) if d]
    return min(stamps) if stamps else parse_legacy_dt("01:00:00 1/1/2100")


def main() -> int:
    parser = argparse.ArgumentParser(description="Nạp đặt xe hệ cũ vào vehicle_booking")
    parser.add_argument("--car", help="Excel đặt xe công tác")
    parser.add_argument("--delivery", help="Excel giao hàng")
    parser.add_argument("--wipe", action="store_true",
                        help="XÓA mọi phiếu đặt xe đang có trước khi nạp")
    parser.add_argument("--dry-run", action="store_true", help="Không ghi DB")
    args = parser.parse_args()

    if not args.car and not args.delivery:
        parser.error("cần ít nhất --car hoặc --delivery")

    sources = [(args.car, False), (args.delivery, True)]
    sources = [(p, d) for p, d in sources if p]

    db = SessionLocal()
    look = Lookups(
        employees=db.query(Employee).all(),
        users=db.query(User).all(),
        companies=db.query(Company).all(),
        vehicles=db.query(Vehicle).all(),
        drivers=db.query(Driver).all(),
    )

    # Gom cả hai tệp rồi xếp chung theo thời gian — mã DX liền mạch theo lịch sử
    # thay vì công tác một dải, giao hàng một dải.
    staged: list[tuple[dict, bool]] = []
    for path, is_delivery in sources:
        rows = read_sheet(path)
        print(f"Đọc {path}: {len(rows)} dòng "
              f"({'giao hàng' if is_delivery else 'đặt xe công tác'})")
        staged.extend((r, is_delivery) for r in rows)
    staged.sort(key=lambda pair: sort_key(pair[0], pair[1]))

    if args.wipe:
        removed = db.query(VehicleBooking).delete(synchronize_session=False)
        print(f"Đã xóa {removed} phiếu đặt xe cũ (--wipe)")
        if args.dry_run:
            db.rollback()
            print("  (dry-run: hoàn tác lệnh xóa)")

    skipped: list[str] = []
    warnings: list[str] = []
    made = Counter()
    seq = 0

    for row, is_delivery in staged:
        kwargs, notes = build_kwargs(row, is_delivery, look)
        if not kwargs:
            skipped.extend(notes)
            continue
        warnings.extend(notes)
        seq += 1
        booking = VehicleBooking(code=f"DX{seq:03d}", is_deleted=False, **kwargs)
        db.add(booking)
        made["giao hàng" if is_delivery else "đặt xe công tác"] += 1

    if args.dry_run:
        db.rollback()
        print("\n--- DRY RUN: không ghi gì vào DB ---")
    else:
        db.commit()

    print(f"\nTạo phiếu: {sum(made.values())}  {dict(made)}")
    print(f"Bỏ dòng:   {len(skipped)}")
    for line, count in Counter(skipped).most_common():
        print(f"   x{count}  {line}")
    if warnings:
        print(f"Cảnh báo:  {len(warnings)}")
        for line, count in Counter(warnings).most_common(12):
            print(f"   x{count}  {line}")
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
