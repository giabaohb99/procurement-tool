"""Nạp TẠM sổ chi tiết mua hàng Misa (báo cáo HTML của chủ dự án) vào sổ giá bao bì làm nguồn giá đúng (duoc-CR-784).

Chạy TRONG container api. Mặc định là CHẠY THỬ (không ghi); chỉ ghi khi có --apply:
    docker compose exec -T api python -m scripts.import_misa_price_ledger /tmp/bao-cao.html            # chạy thử
    docker compose exec -T api python -m scripts.import_misa_price_ledger /tmp/bao-cao.html --apply    # ghi thật
    docker compose exec -T api python -m scripts.import_misa_price_ledger --purge                      # xem trước việc gỡ
    docker compose exec -T api python -m scripts.import_misa_price_ledger --purge --apply              # gỡ hẳn nguồn Misa

Tệp nguồn: đối số đầu tiên hoặc biến môi trường MISA_FILE (HTML có `window.VTBB_DEMO = {...}` hoặc JSON cùng cấu trúc). Pháp nhân
gán cho mọi dòng: --company-id hoặc biến COMPANY_ID (mặc định 1, cùng mặc định của `import_purchase_history_legacy.py`).

Nạp xong: sổ giá có thêm dòng nguồn 3 (Sổ Misa) và `tab_setting.misa_price_cutoff` = ngày lớn nhất của dòng Misa; từ đó mọi phép
tính giá chỉ xét Misa tới mốc + nguồn lịch sử mua hàng / dòng ĐMH SAU mốc. `--purge` xóa dòng nguồn 3 + mốc → như chưa nạp.
Chạy lại bao nhiêu lần cũng ra cùng kết quả (idempotent). Dòng Misa ghi `vat = NULL` (không biết). Script TỪ CHỐI chạy khi sổ đã có
dòng Misa do màn Quản lý Import (module 6, xlsx) nạp — hai đường đánh `source_id` khác nhau; gỡ sạch bằng `--purge --apply` rồi nạp lại. Chi tiết quy tắc: `app/modules/product_price/misa_ledger_import.py`.
"""
import argparse
import os
import sys

import app.core.all_models  # noqa: F401 — nạp đủ model để SQLAlchemy dựng được mapper
from app.core.database import SessionLocal
from app.modules.company.model import Company
from app.modules.product_price.misa_cutoff import get_misa_cutoff
from app.modules.product_price.misa_ledger_import import (MisaSourceError, build_misa_rows, import_misa_rows,
                                                          load_misa_source, purge_misa_rows)


def _print(title: str, stats: dict) -> None:
    print(title)
    for key, value in stats.items():
        print(f"  {key}: {value}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", default=os.getenv("MISA_FILE"), help="tệp HTML / JSON nguồn (hoặc biến MISA_FILE)")
    ap.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ chạy thử, lùi toàn bộ)")
    ap.add_argument("--purge", action="store_true", help="gỡ nguồn Misa: xóa dòng nguồn 3 và mốc")
    ap.add_argument("--company-id", type=int, default=int(os.getenv("COMPANY_ID", "1")), help="pháp nhân gán cho dòng Misa")
    args = ap.parse_args()
    mode = "GHI THẬT" if args.apply else "CHẠY THỬ (không ghi)"

    db = SessionLocal()
    try:
        if args.purge:
            _print(f"[{mode}] gỡ nguồn Misa:", purge_misa_rows(db))
        else:
            if not args.source:
                print("LỖI: thiếu tệp nguồn (đối số đầu tiên hoặc biến MISA_FILE)")
                return 2
            if db.get(Company, args.company_id) is None:
                print(f"LỖI: pháp nhân id={args.company_id} không có trong tab_company")
                return 2
            try:
                rows, parsed = build_misa_rows(load_misa_source(args.source), args.company_id)
            except MisaSourceError as exc:
                print(f"LỖI: {exc}")
                return 2
            if not rows:
                print("LỖI: tệp không có dòng mua hàng hợp lệ nào — không nạp")
                return 2
            _print(f"[{mode}] đọc tệp:", parsed)
            try:
                written = import_misa_rows(db, rows)
            except MisaSourceError as exc:      # sổ đã có dòng Misa do module 6 (xlsx) nạp — không trộn được
                db.rollback()
                print(f"LỖI: {exc}")
                return 2
            _print(f"[{mode}] ghi sổ giá (nguồn 3, pháp nhân {args.company_id}):", written)
        print(f"  mốc sổ Misa sau khi chạy: {get_misa_cutoff(db)}")
        db.commit() if args.apply else db.rollback()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
