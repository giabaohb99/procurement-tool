# -*- coding: utf-8 -*-
"""Gộp dòng hàng hải quan trùng (cùng tờ khai + giá + lượng, không xung đột) — bao-CR-699.

Chạy trong container api:

    python -m scripts.customs_merge_duplicates                  # CHẠY THỬ: đếm nhóm / dòng, phân bổ xung đột theo cột
    python -m scripts.customs_merge_duplicates --apply          # gộp thật (chép dòng sắp xóa ra tệp JSON trước)

Luật gộp ở `app/modules/customs/line_merge.py`. Việc nền `customs.merge_duplicate_lines` chạy cùng luật ngày 1 và 16.
⚠️ `--apply` chép mọi dòng sắp xóa ra `--dump` (mặc định theo giờ chạy) TRƯỚC khi xóa — vẫn phải sao lưu cơ sở dữ
liệu trước khi chạy trên prod.
"""
import argparse
import json
from datetime import datetime

import app.core.all_models  # noqa: F401 — nạp đủ mapper

from app.core.database import SessionLocal
from app.modules.customs import line_merge
from app.modules.customs.importer import _import_lock
from scripts.customs_row_hash import dump_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="gộp thật — mặc định chỉ chạy thử")
    parser.add_argument("--dump", default="", help="tệp JSON chép dòng sắp xóa (mặc định theo giờ chạy)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        with _import_lock(db):          # không chạy chồng một lượt nạp tệp
            result, updates = line_merge.plan(db)
            print(json.dumps(result.as_dict(True), ensure_ascii=False, indent=2))
            if not args.apply:
                print("Chạy thử — chưa ghi gì. Thêm --apply để gộp thật.")
                return
            path = args.dump or f"customs_merge_{datetime.now():%Y%m%d_%H%M%S}.json"
            dump_rows(db, result.delete_ids, path)
            print(f"Đã chép {len(result.delete_ids)} dòng sắp xóa ra {path}.")
            out = line_merge.apply_plan(db, result, updates)
            print(json.dumps(out, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
