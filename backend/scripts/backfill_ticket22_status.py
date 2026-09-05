"""bao-CR-292 (ticket 22) — chia lại trạng thái phiếu YCMH cũ theo bộ ba mốc mới.

Từ bao-CR-292, cụm "Đang xử lý" tách thành ba mốc theo mã đơn MISA + độ phủ mã hàng:
  processing «Đang xử lý»   — đã có ĐMH (kể cả Nháp) nhưng chưa đơn nào nhập MISA
  purchasing «Đang mua hàng» — có ĐMH nhập MISA nhưng mới phủ một phần mã hàng
  purchased  «Đã mua hàng»  — mọi mã hàng (trừ dòng Hủy) đều có ĐMH nhập MISA
Đồng thời mốc rời 'dispatched' hạ xuống "đã có ĐMH" (trước phải có dòng đã đặt hàng).

Phiếu cũ chỉ tự tính lại khi có ai đụng vào ĐMH liên quan — script này quét một lượt
các phiếu đang ở 'dispatched'/'processing' và đặt lại trạng thái theo luật mới.

CỐ Ý KHÔNG gọi `recompute_status`: hàm đó có thể đẩy phiếu kẹt sang 'completed' và bắn
thông báo hàng loạt. Ở đây chỉ xoay quanh 4 mốc dispatched/processing/purchasing/purchased,
không gửi gì; phiếu mà mọi dòng đã Hoàn thành thì bỏ qua, để luồng thường xử lý.

Chạy TRONG container api (mặc định chạy thử, chỉ ghi khi có --apply):
    docker compose exec -T api python -m scripts.backfill_ticket22_status
    docker compose exec -T api python -m scripts.backfill_ticket22_status --apply
"""
import argparse

import app.core.all_models  # noqa: F401 — nạp đủ model để SQLAlchemy dựng được mapper
from app.core.database import SessionLocal
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.purchase_request.service import (
    LINE_STATUS_NO_PO,
    _misa_covered_codes,
    items_of,
)


def target_status(db, pr: PurchaseRequest) -> str | None:
    """Trạng thái ĐÍCH theo luật bao-CR-292; None = bỏ qua (không dòng / đã xong hết)."""
    items = items_of(db, pr.id)
    if not items:
        return None
    active = [i for i in items if (i.line_status or LINE_STATUS_NO_PO) != "Hủy đơn"]
    if active and all((i.line_status or "") == "Hoàn thành" for i in active):
        return None   # để luồng thường đưa sang completed (kèm thông báo đúng chỗ)
    if not any((i.line_status or LINE_STATUS_NO_PO) != LINE_STATUS_NO_PO for i in active):
        return "dispatched"
    active_codes = {i.product_code for i in active}
    covered = _misa_covered_codes(db, pr.code) & active_codes
    if not covered:
        return "processing"
    if active_codes - covered:
        return "purchasing"
    return "purchased"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ chạy thử)")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        prs = (db.query(PurchaseRequest)
               .filter(PurchaseRequest.status.in_(["dispatched", "processing"]),
                       PurchaseRequest.is_deleted == False)  # noqa: E712
               .all())
        changes: dict[str, int] = {}
        for pr in prs:
            new = target_status(db, pr)
            if new is None or new == pr.status:
                continue
            key = f"{pr.status} -> {new}"
            changes[key] = changes.get(key, 0) + 1
            print(f"  {pr.code}: {key}")
            if args.apply:
                pr.status = new
        if args.apply:
            db.commit()
        print(f"Phiếu quét: {len(prs)}")
        for key, n in sorted(changes.items()):
            print(f"  {key}: {n}")
        if not changes:
            print("  (không phiếu nào đổi)")
        print("ĐÃ GHI" if args.apply else "CHẠY THỬ — thêm --apply để ghi thật")
    finally:
        db.close()


if __name__ == "__main__":
    main()
