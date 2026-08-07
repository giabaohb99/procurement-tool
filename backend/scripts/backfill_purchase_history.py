"""Backfill LỊCH SỬ MUA HÀNG cho các dòng ĐMH đã "Hoàn thành" từ trước.

Chạy TRONG container api:
    docker compose exec -T api python -m scripts.backfill_purchase_history          # chạy thử (chỉ in)
    docker compose exec -T api python -m scripts.backfill_purchase_history --apply  # ghi vào DB

Vì sao cần: bảng `tab_purchase_history` chỉ được ghi tại đúng 1 chỗ —
`purchase_order.service.auto_advance_line` khi dòng CHUYỂN sang "Hoàn thành". Những dòng
đã ở "Hoàn thành" trước khi có tính năng (hoặc do import Misa gán thẳng cột tiến độ) không
đi qua chỗ đó nên chưa có snapshot. Script dựng lại phần thiếu, dùng chính
`purchase_history.service.snapshot_line` để record giống hệt luồng chạy thật.

Ngày chốt (`completed_at`) suy ra theo thứ tự ưu tiên, KHÔNG đóng dấu ngày chạy script:
  1. Ngày YCTT đã chi gần nhất của dòng (đúng nghĩa "hoàn thành" = đã thanh toán)
  2. Ngày nhận hàng gần nhất của dòng
  3. Ngày đơn hàng
  4. Hôm nay (chỉ khi không có gì cả)

An toàn khi chạy lại: `snapshot_line` bỏ qua dòng đã có snapshot (`po_item_id` là UNIQUE).
"""
import sys
from datetime import date

import app.core.all_models  # noqa: F401 — nạp đủ model để SQLAlchemy dựng được mapper
from app.core.database import SessionLocal
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_history.service import snapshot_line
from app.modules.purchase_order.model import POItem, PODelivery, PurchaseOrder

BATCH = 200


def _completed_at(db, po: PurchaseOrder, item: POItem) -> tuple[str, str]:
    """Trả (ngày, nguồn) — nguồn để in ra cho người kiểm tra biết ngày lấy từ đâu."""
    delivs = db.query(PODelivery).filter(PODelivery.po_item_id == item.id).all()

    ref_ids = [d.id for d in delivs]
    if ref_ids:
        pay_ids = [p.id for p in db.query(Payable.id)
                   .filter(Payable.source_type == "goods", Payable.ref_type == "delivery",
                           Payable.ref_id.in_(ref_ids)).all()]
        if pay_ids:
            rows = (db.query(PaymentRequest.request_date)
                    .join(PaymentRequestLine, PaymentRequestLine.request_id == PaymentRequest.id)
                    .filter(PaymentRequestLine.payable_id.in_(pay_ids),
                            PaymentRequest.status == "paid").all())
            days = sorted(r[0] for r in rows if (r[0] or "").strip())
            if days:
                return days[-1], "YCTT"

    recv = sorted((d.received_date or "") for d in delivs if (d.received_date or "").strip())
    if recv:
        return recv[-1], "nhận hàng"
    if (po.order_date or "").strip():
        return po.order_date, "ngày đơn"
    return date.today().strftime("%Y-%m-%d"), "hôm nay"


def main(apply: bool) -> None:
    db = SessionLocal()
    try:
        done = (db.query(POItem.id)
                .filter(POItem.progress_status == "Hoàn thành").count())
        have = db.query(PurchaseHistory.id).count()

        rows = (db.query(POItem, PurchaseOrder)
                .join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
                .outerjoin(PurchaseHistory, PurchaseHistory.po_item_id == POItem.id)
                .filter(POItem.progress_status == "Hoàn thành", PurchaseHistory.id.is_(None))
                .order_by(POItem.id.asc()).all())

        print(f"Dòng ĐMH 'Hoàn thành': {done} | đã có lịch sử: {have} | THIẾU: {len(rows)}\n")
        if not rows:
            print("Không có gì để đồng bộ.")
            return

        src_count: dict[str, int] = {}
        written = 0
        for item, po in rows:
            day, src = _completed_at(db, po, item)
            src_count[src] = src_count.get(src, 0) + 1
            written += 1
            if written <= 20 or written % 100 == 0:
                print(f"  [{written:>4}] {po.code} / {item.product_code} — {day} ({src})")
            if apply:
                # snapshot_line đóng dấu completed_at = hôm nay (đúng cho luồng chạy thật).
                # Dữ liệu cũ thì phải sửa lại theo ngày suy ra ở trên, kẻo cả kho lịch sử
                # cùng mang ngày chạy script.
                obj = snapshot_line(db, po, item)
                if obj is not None:
                    obj.completed_at = day
                if written % BATCH == 0:
                    db.commit()

        if apply:
            db.commit()
            print(f"\nĐã ghi {written} dòng lịch sử. Tổng bảng: {db.query(PurchaseHistory.id).count()}")
        else:
            print(f"\n(chạy thử) sẽ ghi {written} dòng — thêm --apply để ghi thật.")
        print("Nguồn ngày chốt: " + ", ".join(f"{k}={v}" for k, v in sorted(src_count.items())))
    finally:
        db.close()


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
