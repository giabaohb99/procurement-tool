"""Nạp lại SỔ GIÁ (`tab_product_price_ledger`) từ lịch sử mua hàng + dòng ĐMH (duoc-CR-784).

Chạy TRONG container api. Mặc định là CHẠY THỬ (không ghi), chỉ ghi khi có --apply:
    docker compose exec -T api python -m scripts.backfill_product_price_ledger            # chạy thử, in số liệu
    docker compose exec -T api python -m scripts.backfill_product_price_ledger --apply    # ghi thật
    docker compose exec -T api python -m scripts.backfill_product_price_ledger --check    # exit 1 nếu sổ giá còn lệch

Các bước: (1) `sync_history_ledger` — xóa dòng nguồn 1 mồ côi, chèn dòng lịch sử còn thiếu, điền tên kho cho dòng đã có, xóa dòng nguồn 2 đã có lịch
sử; (2) với MỌI ĐMH được tính (và đơn còn dòng nguồn 2 cũ) gọi `sync_po_price_ledger(commit=False)` theo lô 200 đơn.
Là bộ hòa giải: sổ giá là dữ liệu dẫn xuất nên chạy lại bao nhiêu lần cũng ra cùng kết quả (idempotent).
"""
import argparse
import sys

import app.core.all_models  # noqa: F401 — nạp đủ model để SQLAlchemy dựng được mapper
from app.core.database import SessionLocal
from app.modules.product_price.ledger_sync_service import (eligible_po_ids, sync_history_ledger,
                                                           sync_po_price_ledger)
from app.modules.purchase_order.model import PurchaseOrder

BATCH = 200


def run(db, apply: bool) -> dict:
    """Chạy cả hai bước; không `apply` thì lùi toàn bộ. Trả số liệu gộp (đủ để in và để `--check` so với 0)."""
    stats = sync_history_ledger(db, dry_run=False)   # dry_run=False để bước 2 thấy dòng vừa chèn; lùi ở cuối
    po = {"inserted": 0, "updated": 0, "deleted": 0}
    ids = eligible_po_ids(db)
    for i in range(0, len(ids), BATCH):
        for order in db.query(PurchaseOrder).filter(PurchaseOrder.id.in_(ids[i:i + BATCH])).all():
            res = sync_po_price_ledger(db, order, commit=False)
            for k in po:
                po[k] += res[k]
        db.flush()
        if apply:
            db.commit()
    stats.update({f"po_{k}": v for k, v in po.items()})
    stats["po_orders_scanned"] = len(ids)
    if apply:
        db.commit()
    else:
        db.rollback()
    return stats


def changes_of(stats: dict) -> int:
    """Số thay đổi cần làm để sổ giá khớp nguồn — 0 nghĩa là sổ đã khớp."""
    keys = ("inserted", "updated_warehouse", "deleted_orphans", "deleted_covered_po_lines", "po_inserted", "po_updated", "po_deleted")
    return sum(stats.get(k, 0) for k in keys)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ chạy thử)")
    ap.add_argument("--check", action="store_true", help="chạy thử và thoát mã 1 nếu sổ giá còn lệch nguồn")
    args = ap.parse_args()
    db = SessionLocal()
    try:
        stats = run(db, apply=args.apply and not args.check)
    finally:
        db.close()
    mode = "GHI THẬT" if args.apply and not args.check else "CHẠY THỬ (không ghi)"
    print(f"[{mode}] sổ giá:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    if args.check and changes_of(stats):
        print(f"LỆCH: {changes_of(stats)} thay đổi cần áp — chạy lại với --apply")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
