# -*- coding: utf-8 -*-
"""Gắn lại hoạt chất / hàm lượng / nhãn của dòng hàng Tra cứu thị trường MỘT LẦN sau bao-CR-728 — bao-CR-733.

Chạy trong container api (prod: thêm `-f docker-compose.production.yml`):

    python -m scripts.gan_lai_hoat_chat_cr733 --dry-run    # đếm dòng SẼ đổi + 10 dòng mẫu, không ghi gì
    python -m scripts.gan_lai_hoat_chat_cr733 --apply      # ghi thật, chỉ dòng có giá trị khác, commit từng khúc

Vì sao: trước bao-CR-728 bộ gắn hoạt chất theo tên thương mại duyệt từ theo thứ tự `set` (đổi theo từng tiến trình),
nên dòng có tên hàng chứa từ hai tên thương mại trở lên mang hoạt chất ngẫu nhiên. Bản sửa chọn ổn định nhưng dữ liệu
ĐÃ LƯU vẫn lệch: xuất rồi nạp lại tệp chỉ sửa 7 dòng mà lô báo 11 dòng "Ghi đè" (4 dòng thừa đổi hoạt chất). Luật gắn
y như nút *Gắn lại nhãn* (`ingredient.retag_all`), khác ở chỗ đọc theo khúc và chỉ ghi dòng khác; giá trị lấy từ tệp /
sửa tay (cờ `_from_file`) giữ nguyên. Chạy lại lần hai `--dry-run` phải ra 0 dòng đổi.

Giữ khóa nạp tệp Tra cứu thị trường suốt lúc chạy (cùng khóa của lô nạp) để không chen vào một lô đang ghi. Gián
đoạn giữa chừng thì chạy lại: khúc đã commit không bị ghi lại.
"""
import argparse
import json
import sys
import time

import app.core.all_models  # noqa: F401 — nạp đủ mapper

from app.core.database import SessionLocal
from app.modules.customs import importer, read_cache
from app.modules.customs.ingredient import retag_changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="chỉ đếm, không ghi gì")
    mode.add_argument("--apply", action="store_true", help="ghi thật các dòng khác")
    args = parser.parse_args()

    db = SessionLocal()
    started = time.perf_counter()
    try:
        with importer._import_lock(db):
            out = retag_changed(db, apply=args.apply)
        if args.apply:
            read_cache.clear()       # số đếm / bộ lọc hoạt chất đọc lại ngay, không chờ hết hạn đệm
    finally:
        db.close()
    print(json.dumps({k: v for k, v in out.items() if k != "examples"}, ensure_ascii=False))
    for ex in out["examples"]:
        print(json.dumps(ex, ensure_ascii=False))
    verb = "Đã ghi" if args.apply else "Sẽ đổi (chạy thử, chưa ghi)"
    print(f"{verb} {out['changed']} / {out['total']} dòng — hoạt chất {out['active']}, hàm lượng "
          f"{out['formulation']}, nhãn {out['kind']} — {time.perf_counter() - started:.1f} giây")
    return 0


if __name__ == "__main__":
    sys.exit(main())
