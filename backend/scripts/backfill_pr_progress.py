"""Backfill TIẾN ĐỘ (đặt/nhận) từ Đơn mua hàng -> Yêu cầu mua hàng nguồn.

Vì sao cần: các dòng ĐMH tạo TRƯỚC 2026-07-11 (trước khi có state-machine tiến độ)
bị migration 5ad008ca924e đóng dấu progress_status = "Chưa đặt hàng" và KHÔNG được
auto-nâng. Hàm đồng bộ sang YCMH bỏ qua mọi dòng còn ở "Chưa đặt hàng"
(if idx < 1: continue), nên cột "TIẾN ĐỘ (NHẬN / ĐẶT)" của YCMH hiển thị "—"
dù đơn đã hoàn thành và đã nhận hàng.

Script này quét mọi ĐMH đã ra khỏi Nháp, chạy lại auto-advance cho từng dòng theo
điều kiện dữ liệu thực (mã MISA, số lượng nhận, số HĐ, ngày giao chứng từ, thanh toán)
rồi đồng bộ lại sang YCMH. An toàn / idempotent: chạy lại nhiều lần cho cùng kết quả.

Chạy TRONG container api:
    docker compose exec -T api python -m scripts.backfill_pr_progress          # dry-run (chỉ in)
    docker compose exec -T api python -m scripts.backfill_pr_progress --apply  # ghi vào DB
"""
import sys

from app.core.database import SessionLocal
from app.core import all_models  # noqa: F401  (đăng ký mọi mapper trước khi query)
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order import service as po_service

# Trạng thái ĐMH không đóng góp tiến độ (khớp bộ lọc trong sync_from_purchase_orders)
_SKIP_STATUS = ["draft", "submitted", "cancelled", "rejected"]


def main(apply: bool) -> None:
    db = SessionLocal()
    try:
        pos = (db.query(PurchaseOrder)
               .filter(PurchaseOrder.status.notin_(_SKIP_STATUS))
               .order_by(PurchaseOrder.id.asc()).all())
        print(f"Quét {len(pos)} đơn mua hàng (không phải Nháp/Từ chối/Hủy).\n")

        changed_pos = 0
        changed_lines = 0
        pr_codes = set()
        for po in pos:
            items = db.query(POItem).filter(POItem.po_id == po.id).all()
            would = []
            for it in items:
                if it.progress_status in po_service.PROGRESS_EXCEPTIONS:
                    continue  # Tạm ngưng / Hủy đơn: không auto
                cur = (po_service.PROGRESS_ORDER.index(it.progress_status)
                       if it.progress_status in po_service.PROGRESS_ORDER else 0)
                tgt = po_service.highest_satisfied_step(db, po, it)
                if tgt > cur:
                    would.append((it.product_name, it.progress_status,
                                  po_service.PROGRESS_ORDER[tgt]))
            if not would:
                continue
            changed_pos += 1
            changed_lines += len(would)
            if po.pr_code:
                pr_codes.add(po.pr_code)
            print(f"  {po.code} (status={po.status}, YCMH={po.pr_code or '-'}):")
            for name, frm, to in would:
                print(f"      - {name}: '{frm}' -> '{to}'")

        if apply and changed_pos:
            print("\nĐang áp dụng auto-advance + đồng bộ YCMH...")
            for po in pos:
                po_service.apply_auto_progress(db, po, user_id=0)
            print(f"Đã cập nhật {changed_lines} dòng trên {changed_pos} đơn; "
                  f"đồng bộ {len(pr_codes)} YCMH.")
        else:
            print(f"\n(dry-run) sẽ nâng {changed_lines} dòng trên {changed_pos} đơn "
                  f"({len(pr_codes)} YCMH) — thêm --apply để ghi.")
    finally:
        db.close()


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
