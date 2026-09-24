# -*- coding: utf-8 -*-
"""Chuyển phiếu CŨ của phòng tự mua hàng sang luật «Phòng xử lý» — bao-CR-480.

Chạy MỖI KHI một phòng vừa được cấp bộ máy mua riêng (có người giữ vai trò «Quản lý thu
mua phòng»), và một lần ngay sau khi deploy CR-480 cho các phòng đã có sẵn. Chạy lại vô hại.

    docker compose exec -T api python scripts/backfill_handling_dept.py --dry-run   # xem sẽ đổi gì
    docker compose exec -T api python scripts/backfill_handling_dept.py             # đổi thật
    docker compose exec -T api python scripts/backfill_handling_dept.py --dept 5    # chỉ một phòng

Không truyền `--dept` thì tự lấy mọi phòng đang có người giữ bậc `dept_proc` trên YCMH.
Vì sao không tự chạy lúc khởi động: xem `backfill_handling_dept` trong
`app/modules/purchase_request/service.py`.
"""
import argparse
import sys

sys.path.insert(0, "/app")

import app.core.all_models  # noqa: E402,F401
from app.core.database import SessionLocal  # noqa: E402
from app.modules.purchase_request.service import (  # noqa: E402
    backfill_handling_dept, list_self_purchasing_dept_ids,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="chỉ đếm, không ghi")
    ap.add_argument("--dept", type=int, action="append", help="id phòng (lặp lại được)")
    args = ap.parse_args()
    db = SessionLocal()
    try:
        targets = set(args.dept) if args.dept else list_self_purchasing_dept_ids(db)
        print("phong tu mua hang:", sorted(targets) or "(khong co)")
        counts = backfill_handling_dept(db, targets, dry_run=args.dry_run)
        for key, n in counts.items():
            print(f"  {key}: {n} phieu {'se doi' if args.dry_run else 'da doi'}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
