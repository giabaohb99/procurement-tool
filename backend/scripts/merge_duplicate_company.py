# -*- coding: utf-8 -*-
"""Gộp pháp nhân TRÙNG vào pháp nhân GIỮ rồi xóa bản trùng — bao-CR-532.

Mặc định CHẠY THỬ: chạy thật toàn bộ trong một giao dịch rồi ROLLBACK, nên số in ra là số thật.
Chỉ ``--apply`` mới ghi. Tra theo MÃ, không theo id — id của bản trùng khác nhau giữa các môi
trường (prod 15, dev 16).

    docker exec -w /app <api> python scripts/merge_duplicate_company.py                 # chạy thử
    docker exec -w /app <api> python scripts/merge_duplicate_company.py --apply         # ghi thật

Mặc định: giữ ``DEGO``, bỏ ``DEGO HOLDING``. Hai bản phải CÙNG mã số thuế, không thì dừng.
Sau khi ghi: phạm vi quyền của người đang đăng nhập có thể trễ tới 60 giây (bộ đệm quyền trong
tiến trình api) — không cần khởi động lại.
Logic nằm ở ``app/modules/company/merge_service.py``.
"""
import argparse
import sys

sys.path.insert(0, "/app")

import app.core.all_models  # noqa: E402,F401
from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.modules.company.merge_service import (  # noqa: E402
    MergeError, company_columns, count_references, is_history, merge_companies, write_merge_audit,
)


def _id_of(db, code: str) -> int:
    ids = [r[0] for r in db.execute(text("select id from tab_company where code = :c"), {"c": code})]
    if len(ids) != 1:
        raise MergeError(f"Mã {code!r}: tìm thấy {len(ids)} công ty, cần đúng 1")
    return ids[0]


def _unmapped_columns(db) -> list[str]:
    """Cột 'compan' có trong CSDL mà không có trong model — vòng lặp tự dò sẽ không thấy chúng."""
    if db.bind.dialect.name != "mysql":
        return []
    mapped = set(company_columns(include_history=True))
    rows = db.execute(text("""select TABLE_NAME, COLUMN_NAME from information_schema.COLUMNS
        where TABLE_SCHEMA = database() and TABLE_NAME like 'tab%' and COLUMN_NAME like '%compan%'
        and DATA_TYPE in ('int','bigint','smallint','mediumint','tinyint')""")).all()
    return [f"{t}.{c}" for t, c in rows
            if (t, c) not in mapped and t not in ("tab_company", "tab_department_company", "tab_doc_folder",
                                                  "tab_inventory")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-code", default="DEGO")
    ap.add_argument("--dup-code", default="DEGO HOLDING")
    ap.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ chạy thử)")
    ap.add_argument("--user-id", type=int, default=0, help="id tài khoản ghi vào nhật ký")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        keep_id, dup_id = _id_of(db, args.keep_code), _id_of(db, args.dup_code)
        print(f"CSDL: {db.execute(text('select database()')).scalar() if db.bind.dialect.name == 'mysql' else '-'}")
        print(f"GIỮ  {args.keep_code!r} id={keep_id}\nBỎ   {args.dup_code!r} id={dup_id}")
        print("\nTrước khi gộp — dòng đang trỏ bản trùng:")
        for k, v in count_references(db, dup_id).items():
            print(f"  {k}: {v}")
        hist = [(t, c) for t, c in company_columns(include_history=True) if is_history(t)]
        kept = {f"{t}.{c}": db.execute(text(f"select count(*) from {t} where {c} = :d"), {"d": dup_id}).scalar()
                for t, c in hist}
        print("Lịch sử giữ nguyên (không ghi lại):", {k: v for k, v in kept.items() if v} or "không có")
        unmapped = _unmapped_columns(db)
        if unmapped:
            raise MergeError(f"Có cột công ty ngoài model, script không tự dò được: {unmapped}")

        report = merge_companies(db, keep_id, dup_id)
        print(f"\n{'ĐÃ GHI' if args.apply else 'CHẠY THỬ (sẽ rollback)'} — thay đổi:")
        for k, v in report.items():
            print(f"  {k}: {v}")

        if args.apply:
            write_merge_audit(db, keep_id, dup_id, report, args.user_id)   # lời gọi này commit
            db.commit()
            print("\nĐã commit. Còn trỏ bản trùng:", count_references(db, dup_id) or "không còn")
        else:
            db.rollback()
            print("\nĐã rollback — chưa ghi gì.")
        return 0
    except MergeError as e:
        db.rollback()
        print(f"\nDỪNG, không ghi gì: {e}")
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
