"""Thêm người cùng quyền duyệt vào các phiếu đặt xe ĐANG CHỜ đã giao một người (duoc-CR-706).

Logic nằm ở `app/modules/vehicle_booking/approver_expand.py`; idempotent, không gửi thư / chuông.

    docker compose exec -T api python scripts/mo_rong_nguoi_duyet_dat_xe.py           # xem, không ghi
    docker compose exec -T api python scripts/mo_rong_nguoi_duyet_dat_xe.py --apply   # ghi thật
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app.core.all_models  # noqa: E402,F401
from app.core.database import SessionLocal  # noqa: E402
from app.modules.vehicle_booking.approver_expand import expand_pending_approvers  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ xem)")
    args = ap.parse_args()
    db = SessionLocal()
    try:
        report = expand_pending_approvers(db, args.apply)
    finally:
        db.close()
    for row in report:
        print(f"{row['code']} (#{row['booking_id']}): thêm nhân sự {row['added_employee_ids']}")
    print(f"{'ĐÃ GHI' if args.apply else 'XEM THỬ (chưa ghi)'}: {len(report)} phiếu cần mở rộng")


if __name__ == "__main__":
    main()
