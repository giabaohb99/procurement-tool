# -*- coding: utf-8 -*-
"""Gỡ liên kết YCBG -> YCMH đã xóa, cho dữ liệu cũ — bao-CR-580.

Từ bao-CR-580, xóa YCMH thì YCBG tự gỡ liên kết. Các YCMH xóa TRƯỚC bản vá vẫn còn dây nối
(YCBG vẫn bày mã YCMH đã xóa, vẫn đứng ở «Đã tạo YCMH»). Chạy một lần sau khi deploy; chạy lại vô hại.

    docker compose exec -T api python scripts/unlink_deleted_pr_cr580.py --dry-run   # xem sẽ gỡ gì
    docker compose exec -T api python scripts/unlink_deleted_pr_cr580.py             # gỡ thật
"""
import argparse
import sys

sys.path.insert(0, "/app")

import app.core.all_models  # noqa: E402,F401
from app.core.database import SessionLocal  # noqa: E402
from app.modules.survey_request.service import (  # noqa: E402
    list_deleted_linked_prs, unlink_deleted_prs,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="chỉ liệt kê, không ghi")
    args = ap.parse_args()
    db = SessionLocal()
    try:
        if args.dry_run:
            prs = list_deleted_linked_prs(db)
            print(f"YCMH da xoa con noi YCBG: {len(prs)}")
            for pr in prs:
                print(f"  {pr.id} {pr.code}")
            return
        codes = unlink_deleted_prs(db, 0)
        print(f"da go lien ket {len(codes)} YCMH: {', '.join(codes) or '(khong co)'}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
