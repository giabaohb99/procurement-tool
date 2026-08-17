"""CR-074 — gắn nhãn "Chưa tạo đơn mua hàng" cho các dòng YCMH cũ.

Trước CR-074 dòng YCMH chưa có ĐMH nào cũng mang nhãn "Chưa đặt hàng", lẫn với dòng đã
có đơn nhưng chưa bấm đặt hàng. Script này tách dữ liệu cũ ra đúng hai nhóm:

  dòng đang "Chưa đặt hàng" + KHÔNG có dòng ĐMH nào (mã sản phẩm + mã YCMH) → "Chưa tạo đơn mua hàng"
  dòng đang "Chưa đặt hàng" + CÓ dòng ĐMH (kể cả đơn Nháp, trừ đơn đã Hủy)   → giữ nguyên

CỐ Ý KHÔNG gọi `sync_from_purchase_orders`: hàm đó suy lại cả trạng thái PHIẾU và có thể
bắn thông báo "đã nhận hàng"/"hoàn thành" cho hàng loạt người dùng. Ở đây chỉ sửa đúng
một cột, không đụng trạng thái phiếu, không gửi gì.

Chạy TRONG container api (mặc định chạy thử, chỉ ghi khi có --apply):
    docker compose exec -T api python -m scripts.backfill_line_status_cr074
    docker compose exec -T api python -m scripts.backfill_line_status_cr074 --apply
"""
import argparse

import app.core.all_models  # noqa: F401 — nạp đủ model để SQLAlchemy dựng được mapper
from app.core.database import SessionLocal
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.service import LINE_STATUS_NOT_ORDERED, LINE_STATUS_NO_PO


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ chạy thử)")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        # Cặp (mã YCMH, mã sản phẩm) đã có ít nhất một dòng ĐMH còn sống.
        created = {(r[0], r[1]) for r in
                   db.query(PurchaseOrder.pr_code, POItem.product_code)
                   .join(POItem, POItem.po_id == PurchaseOrder.id)
                   .filter(PurchaseOrder.status != "cancelled").distinct().all()}

        rows = (db.query(PurchaseRequestItem, PurchaseRequest.code)
                .join(PurchaseRequest, PurchaseRequest.id == PurchaseRequestItem.pr_id)
                .filter(PurchaseRequestItem.line_status == LINE_STATUS_NOT_ORDERED).all())

        doi, giu = 0, 0
        for it, pr_code in rows:
            if (pr_code, it.product_code) in created:
                giu += 1
                continue
            doi += 1
            if args.apply:
                it.line_status = LINE_STATUS_NO_PO

        if args.apply:
            db.commit()
        print(f"Dòng đang '{LINE_STATUS_NOT_ORDERED}': {len(rows)}")
        print(f"  -> đổi sang '{LINE_STATUS_NO_PO}': {doi}")
        print(f"  -> giữ nguyên (đã có ĐMH)      : {giu}")
        print("ĐÃ GHI" if args.apply else "CHẠY THỬ — thêm --apply để ghi thật")
    finally:
        db.close()


if __name__ == "__main__":
    main()
