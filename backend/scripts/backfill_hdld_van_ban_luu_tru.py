# -*- coding: utf-8 -*-
"""Bù BẢN LƯU TRỮ ở phân hệ Văn bản cho mọi HĐLĐ đã có trước duoc-CR-629 — CHẠY TAY.

Không nằm trong migration (nạp dữ liệu và chép tệp không thuộc DDL). IDEMPOTENT: chạy lại không
sinh thêm văn bản / liên kết tệp (cầu nối so `document_id` và sha256).

MẶC ĐỊNH LÀ CHẠY THỬ (chỉ đếm, không ghi gì). Muốn ghi phải có `--apply` VÀ `--yes` (hoặc gõ xác nhận
khi chạy trên terminal); script in máy chủ + tên DB đích trước khi ghi.

Chạy trong container api:
    # kiểm điều kiện triển khai (loại HDLD có sẵn do người dùng tạo? văn bản HDLD mồ côi?) — chỉ đọc
    docker compose exec -T api python scripts/backfill_hdld_van_ban_luu_tru.py --check
    # chạy thử: đếm HĐ chưa có văn bản
    docker compose exec -T api python scripts/backfill_hdld_van_ban_luu_tru.py
    # ghi thật
    docker compose exec -T api python scripts/backfill_hdld_van_ban_luu_tru.py --apply --yes
    # ROLLBACK: xóa mềm mọi văn bản lưu trữ HĐLĐ và đặt document_id = 0 (trước khi downgrade); cũng cần --apply --yes
    docker compose exec -T api python scripts/backfill_hdld_van_ban_luu_tru.py --soft-delete-all --apply --yes

Cần loại văn bản `HDLD` đang bật (seed tạo); thiếu thì mọi HĐ được tính là «bỏ qua».
"""
import argparse
import sys

sys.path.insert(0, "/app")

import app.core.all_models  # noqa: E402,F401 — đăng ký mapper trước khi mở session
from app.core.base_model import mark_deleted  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.modules.document.model import Document  # noqa: E402
from app.modules.labor_contract import document_archive_sync  # noqa: E402
from app.modules.labor_contract.model import LaborContract  # noqa: E402


def run(db, *, dry_run: bool = False, soft_delete_all: bool = False) -> dict:
    """Trả bộ đếm: created · synced · skipped · failed · pending (chỉ dry-run)."""
    counts = {"created": 0, "synced": 0, "skipped": 0, "failed": 0, "pending": 0, "removed": 0}
    #  Loại HDLD thiếu / đang tắt ⇒ cầu đồng bộ bỏ qua IM LẶNG: báo ngay cả khi chạy thử (review L6).
    from app.modules.doc_catalog.model import DocType
    doc_type = db.query(DocType).filter(DocType.code == "HDLD").first()
    counts["type_inactive"] = int(doc_type is None or not doc_type.is_active)
    rows = db.query(LaborContract.id, LaborContract.document_id, LaborContract.created_by) \
        .order_by(LaborContract.id).all()   # kể cả HĐ xóa mềm

    if soft_delete_all:
        for cid, document_id, _ in rows:
            if not document_id:
                continue
            if dry_run:
                counts["removed"] += 1
                continue
            doc = db.get(Document, document_id)
            if doc is not None and not doc.is_deleted:
                mark_deleted(doc, 0)
            lc = db.get(LaborContract, cid)
            lc.document_id = 0
            counts["removed"] += 1
            db.flush()
        #  Cả văn bản loại HDLD KHÔNG gắn HĐ nào (mồ côi) — rollback phải sạch hẳn (review L3).
        from app.modules.document.labor_contract_archive_access import hdld_type_id
        typed = hdld_type_id(db)
        if typed:
            linked = {d for _, d, _ in rows if d}
            for doc in db.query(Document).filter(Document.doc_type_id == typed,
                                                 Document.is_deleted == False).all():  # noqa: E712
                if dry_run:
                    counts["removed"] += doc.id not in linked   # đã đếm ở vòng trên
                else:
                    mark_deleted(doc, 0)
                    counts["removed"] += 1
        if not dry_run:
            db.commit()
        return counts

    for cid, document_id, created_by in rows:
        existing = db.get(Document, document_id) if document_id else None
        if dry_run:
            if existing is None:
                counts["pending"] += 1
            continue
        had = existing is not None
        new_id = document_archive_sync.archive_sync(db, cid, created_by or 1)
        if not new_id:
            counts["failed" if had or document_id else "skipped"] += 1
        else:
            counts["synced" if had else "created"] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="GHI thật (mặc định chỉ chạy thử, đếm)")
    parser.add_argument("--yes", action="store_true", help="đồng ý ghi, không hỏi lại (cần cùng --apply)")
    parser.add_argument("--soft-delete-all", action="store_true",
                        help="rollback: xóa mềm mọi văn bản HĐLĐ, đặt document_id = 0 (chỉ ghi khi có --apply)")
    parser.add_argument("--check", action="store_true",
                        help="chỉ kiểm điều kiện dừng triển khai (loại HDLD có sẵn / văn bản mồ côi), không ghi")
    args = parser.parse_args()
    if args.yes and not args.apply:
        parser.error("--yes chỉ có nghĩa khi đi cùng --apply")

    from app.core.database import engine
    from app.modules.document.labor_contract_archive_access import check_doc_type

    target = engine.url
    print(f"DB đích: {target.host}:{target.port or ''}/{target.database}")
    db = SessionLocal()
    try:
        if args.check:
            problems = check_doc_type(db)
            for p in problems:
                print("ĐIỀU KIỆN DỪNG TRIỂN KHAI:", p)
            print("OK" if not problems else "KHÔNG ĐẠT")
            return 2 if problems else 0
        dry_run = not args.apply
        if not dry_run and not args.yes:
            if not sys.stdin.isatty() or input(f"Ghi vào {target.database}? gõ 'yes' để tiếp tục: ").strip() != "yes":
                print("Hủy: thiếu --yes hoặc chưa xác nhận.")
                return 1
        problems = check_doc_type(db)
        if problems and not dry_run and not args.soft_delete_all:
            for p in problems:
                print("ĐIỀU KIỆN DỪNG TRIỂN KHAI:", p)
            print("Dừng — xử lý các điều kiện trên trước khi ghi.")
            return 2
        counts = run(db, dry_run=dry_run, soft_delete_all=args.soft_delete_all)
        if counts.get("type_inactive"):
            print("CẢNH BÁO: loại văn bản HDLD đang thiếu hoặc bị tắt — cầu đồng bộ sẽ bỏ qua mọi hợp đồng.")
        print(("[CHẠY THỬ] " if dry_run else "[ĐÃ GHI] ") + " · ".join(f"{k}={v}" for k, v in counts.items()))
        return 1 if counts["failed"] else 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
