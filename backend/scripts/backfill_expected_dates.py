"""Backfill dữ liệu "Ngày dự kiến có hàng" (expected_date) và "Ngày cần hàng" (need_date) cho các đơn cũ.

Chức năng:
1. Đồng bộ `tab_purchase_request.need_date` = ngày cần hàng sớm nhất (min required_date) của các dòng.
2. Điền `tab_pr_item.expected_date` cho các dòng YCMH cũ còn trống theo Ngày QĐ có hàng của Phân loại (CR-065).
3. Điền `tab_po_item.expected_date` cho các dòng ĐMH cũ còn trống:
   - Nếu có YCMH nguồn: copy từ dòng YCMH nguồn tương ứng.
   - Nếu ĐMH độc lập: tính theo Ngày QĐ có hàng của Phân loại dựa trên ngày đặt hàng.
4. Điền `tab_po_delivery.promised_date` / `regulated_date` / `std_days` cho các đợt giao cũ còn trống.

Cách chạy:
- Dry-run (chỉ in xem trước, không ghi DB):
    docker compose exec -T api python -m scripts.backfill_expected_dates
- Apply (thực hiện ghi vào DB):
    docker compose exec -T api python -m scripts.backfill_expected_dates --apply
"""
import sys
from datetime import datetime

from app.core.database import SessionLocal
from app.core import all_models  # noqa: F401
from app.modules.catalog import lead_time
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_order.model import PurchaseOrder, POItem, PODelivery


def main(apply: bool = False) -> None:
    db = SessionLocal()
    mode_text = "THỰC THI (ghi vào CSDL)" if apply else "DRY-RUN (chỉ kiểm tra & in xem trước)"
    print(f"=== BẮT ĐẦU CHẠY BACKFILL DỮ LIỆU NGÀY DỰ KIẾN / NGÀY CẦN HÀNG [{mode_text}] ===\n")

    try:
        std_map = lead_time.std_days_map(db)
        print(f"Đã nạp bảng quy định lead time cho {len(std_map)} phân loại hàng.")

        # -----------------------------------------------------------------
        # 1. Backfill tab_purchase_request.need_date & tab_pr_item.expected_date
        # -----------------------------------------------------------------
        prs = db.query(PurchaseRequest).filter(PurchaseRequest.is_deleted == False).order_by(PurchaseRequest.id.asc()).all()
        pr_header_updated = 0
        pr_lines_updated = 0

        print(f"\n1. Quét {len(prs)} phiếu YCMH...")
        for pr in prs:
            items = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all()
            base_date = (pr.request_date or "").strip()
            if not base_date and pr.created_at:
                base_date = pr.created_at.strftime("%Y-%m-%d")

            # Cập nhật dòng hàng YCMH
            for it in items:
                if (it.line_status or "") == "Hủy đơn":
                    continue
                if not (it.expected_date or "").strip():
                    new_exp = lead_time.regulated_date(std_map, it.item_group or "", base_date)
                    if new_exp:
                        pr_lines_updated += 1
                        if apply:
                            it.expected_date = new_exp

            # Cập nhật header need_date
            valid_reqs = [it.required_date for it in items
                          if (it.required_date or "").strip() and (it.line_status or "") != "Hủy đơn"]
            min_req = min(valid_reqs) if valid_reqs else ""
            if min_req and pr.need_date != min_req:
                pr_header_updated += 1
                if apply:
                    pr.need_date = min_req

        print(f"  -> Cần cập nhật {pr_header_updated} đầu phiếu YCMH (need_date)")
        print(f"  -> Cần cập nhật {pr_lines_updated} dòng hàng YCMH (expected_date)")

        # -----------------------------------------------------------------
        # 2. Backfill tab_po_item.expected_date & tab_po_delivery
        # -----------------------------------------------------------------
        pos = db.query(PurchaseOrder).order_by(PurchaseOrder.id.asc()).all()
        po_lines_updated = 0
        po_dels_updated = 0

        print(f"\n2. Quét {len(pos)} đơn mua hàng (PO)...")
        for po in pos:
            # Map ngày dự kiến từ YCMH nguồn nếu có
            pr_exp_map = {}
            if po.pr_code:
                src_pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == po.pr_code).first()
                if src_pr:
                    src_items = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == src_pr.id).all()
                    pr_exp_map = {(r.product_code or "").strip(): (r.expected_date or "").strip()
                                  for r in src_items if (r.product_code or "").strip()}

            base_order_date = (po.order_date or "").strip()
            if not base_order_date and po.created_at:
                base_order_date = po.created_at.strftime("%Y-%m-%d")

            po_items = db.query(POItem).filter(POItem.po_id == po.id).all()
            for it in po_items:
                if (it.progress_status or "") == "Hủy đơn":
                    continue
                if not (it.expected_date or "").strip():
                    pcode = (it.product_code or "").strip()
                    new_exp = pr_exp_map.get(pcode, "")
                    if not new_exp:
                        new_exp = lead_time.regulated_date(std_map, it.item_group or "", base_order_date)
                    if new_exp:
                        po_lines_updated += 1
                        if apply:
                            it.expected_date = new_exp

                # Cập nhật các lần giao
                dels = db.query(PODelivery).filter(PODelivery.po_item_id == it.id).all()
                for d in dels:
                    changed = False
                    if not (d.promised_date or "").strip():
                        d.promised_date = lead_time.regulated_date(std_map, it.item_group or "", base_order_date)
                        changed = True
                    if not (d.regulated_date or "").strip():
                        d.regulated_date = lead_time.regulated_date(std_map, it.item_group or "", base_order_date)
                        changed = True
                    if not d.std_days:
                        d.std_days = lead_time.std_days_of(std_map, it.item_group or "")
                        changed = True
                    if changed:
                        po_dels_updated += 1

        print(f"  -> Cần cập nhật {po_lines_updated} dòng hàng ĐMH (expected_date)")
        print(f"  -> Cần cập nhật {po_dels_updated} đợt giao hàng ĐMH (promised_date / regulated_date / std_days)")

        if apply:
            db.commit()
            print("\n✅ ĐÃ LƯU THÀNH CÔNG VÀO CƠ SỞ DỮ LIỆU!")
        else:
            print("\n💡 Chạy với cờ `--apply` để thực thi cập nhật thật:")
            print("   docker compose exec -T api python -m scripts.backfill_expected_dates --apply")

    finally:
        db.close()


if __name__ == "__main__":
    apply_flag = "--apply" in sys.argv
    main(apply=apply_flag)
