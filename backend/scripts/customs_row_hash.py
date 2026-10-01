# -*- coding: utf-8 -*-
"""Tính mã băm chống trùng cho dòng hàng hải quan đã nạp + dọn dòng thừa — bao-CR-541.

Chạy (trong container api, sau `alembic upgrade head`):

    python -m scripts.customs_row_hash --backfill            # tính mã cho mọi dòng còn trống
    python -m scripts.customs_row_hash --dedupe              # CHẠY THỬ: báo số nhóm / số dòng thừa
    python -m scripts.customs_row_hash --dedupe --apply      # xóa dòng thừa (chép ra tệp trước)

Dòng thừa = dòng có cùng mã băm với một dòng khác; mỗi nhóm GIỮ dòng id nhỏ nhất (nạp sớm
nhất). Đây là phần dồn lại từ luật bao-CR-496 «trùng trong lô vẫn ghi» — đo 30/09 trên prod
có 576 nhóm / 806 dòng thừa, cùng nằm trong một lô.

⚠️ `--apply` chép mọi dòng sắp xóa ra một tệp JSON (`--dump`, mặc định đặt theo giờ chạy)
TRƯỚC khi xóa — vẫn phải sao lưu cơ sở dữ liệu trước khi chạy trên prod.
⚠️ Không cần chạy `--backfill` để chống trùng hoạt động: lần nạp sau tự tính mã cho dòng cũ
trong khoảng ngày của tệp. `--backfill` chỉ cần cho `--dedupe` (so trên toàn bảng).
"""
import argparse
import json
from datetime import date, datetime
from decimal import Decimal

import app.core.all_models  # noqa: F401 — nạp đủ mapper

from app.core.database import SessionLocal
from app.modules.customs.dedupe import backfill_hashes, find_surplus_ids
from app.modules.customs.model import CustomsLine

_CHUNK = 1000


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def dump_rows(db, ids: list[int], path: str) -> None:
    columns = [c.name for c in CustomsLine.__table__.c]
    rows = []
    for i in range(0, len(ids), _CHUNK):
        for x in db.query(CustomsLine).filter(CustomsLine.id.in_(ids[i:i + _CHUNK])):
            rows.append({c: _json_value(getattr(x, c)) for c in columns})
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False)


def delete_rows(db, ids: list[int]) -> int:
    deleted = 0
    for i in range(0, len(ids), _CHUNK):
        deleted += (db.query(CustomsLine).filter(CustomsLine.id.in_(ids[i:i + _CHUNK]))
                    .delete(synchronize_session=False))
    db.commit()
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backfill", action="store_true", help="tính mã cho mọi dòng còn trống")
    parser.add_argument("--dedupe", action="store_true", help="báo (hoặc xóa với --apply) dòng thừa")
    parser.add_argument("--apply", action="store_true", help="xóa thật — mặc định chỉ chạy thử")
    parser.add_argument("--dump", default="", help="tệp JSON chép dòng sắp xóa")
    args = parser.parse_args()
    if not (args.backfill or args.dedupe):
        parser.error("chọn --backfill và/hoặc --dedupe")

    db = SessionLocal()
    try:
        if args.backfill:
            print(f"Đã tính mã cho {backfill_hashes(db)} dòng.")
        if args.dedupe:
            empty = db.query(CustomsLine).filter(CustomsLine.row_hash == "").count()
            if empty:
                print(f"Còn {empty} dòng chưa có mã — chạy --backfill trước rồi mới dọn.")
                return
            groups, surplus = find_surplus_ids(db)
            print(f"Tổng {db.query(CustomsLine).count()} dòng; {groups} nhóm trùng; {len(surplus)} dòng thừa.")
            if not args.apply or not surplus:
                print("Chạy thử — chưa xóa gì." if surplus else "Không có dòng thừa.")
                return
            path = args.dump or f"customs_surplus_{datetime.now():%Y%m%d_%H%M%S}.json"
            dump_rows(db, surplus, path)
            print(f"Đã chép {len(surplus)} dòng sắp xóa ra {path}.")
            print(f"Đã xóa {delete_rows(db, surplus)} dòng thừa.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
