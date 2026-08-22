"""Backfill LỊCH SỬ MUA HÀNG cho các dòng ĐMH đã hoàn thành từ trước.

Chạy TRONG container api (LUÔN chạy thử trước, chỉ ghi khi có --apply):
    # 1. Xem đơn cũ đang nằm ở tiến độ nào, thiếu bao nhiêu bản ghi lịch sử
    docker compose exec -T api python -m scripts.backfill_purchase_history --stats

    # 2. Mặc định: chỉ dòng tiến độ `completed` (Hoàn thành)
    docker compose exec -T api python -m scripts.backfill_purchase_history
    docker compose exec -T api python -m scripts.backfill_purchase_history --apply

    # 3. Đơn PO CŨ chưa được chuyển tiến độ chuẩn — lấy theo THỰC TẾ ĐÃ NHẬN HÀNG
    docker compose exec -T api python -m scripts.backfill_purchase_history --include-received
    docker compose exec -T api python -m scripts.backfill_purchase_history --include-received --apply

    # 4. Hoặc tự chỉ định trạng thái nào được tính là đã mua xong (B-06: truyền MÃ, không
    #    truyền chữ tiếng Việt — xem PO_PROGRESS_STATUS trong app/core/status_codes.py)
    docker compose exec -T api python -m scripts.backfill_purchase_history \
        --status "completed,doc_sent" --apply

Vì sao cần: bảng `tab_purchase_history` chỉ được ghi tại đúng 1 chỗ —
`purchase_order.service.auto_advance_line` khi dòng CHUYỂN sang `completed`. Những dòng
đã ở `completed` trước khi có tính năng (hoặc do import Misa gán thẳng cột tiến độ) không
đi qua chỗ đó nên chưa có snapshot. Script dựng lại phần thiếu, dùng chính
`purchase_history.service.snapshot_line` để record giống hệt luồng chạy thật.

Dòng ĐÃ HỦY (tiến độ `cancelled`, hoặc đơn `status = cancelled`) luôn bị loại, kể cả khi
đã lỡ nhận hàng — lịch sử mua hàng không tính đơn hủy.

Ngày chốt (`completed_at`) suy ra theo thứ tự ưu tiên, KHÔNG đóng dấu ngày chạy script:
  1. Ngày YCTT đã chi gần nhất của dòng (đúng nghĩa "hoàn thành" = đã thanh toán)
  2. Ngày nhận hàng gần nhất của dòng
  3. Ngày đơn hàng
  4. Hôm nay (chỉ khi không có gì cả)

An toàn khi chạy lại: `snapshot_line` bỏ qua dòng đã có snapshot (`po_item_id` là UNIQUE).
"""
import argparse
import csv
from datetime import date

from sqlalchemy import and_, case, func, or_

import app.core.all_models  # noqa: F401 — nạp đủ model để SQLAlchemy dựng được mapper
from app.core.database import SessionLocal
from app.core.status_codes import PO_PROGRESS_STATUS
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_history.service import snapshot_line
from app.modules.purchase_order.model import POItem, PODelivery, PurchaseOrder
from app.modules.purchase_order.service import PROG_CANCELLED, PROG_COMPLETED

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


def _print_stats(db) -> None:
    """Phân bố tiến độ dòng × đã có lịch sử chưa — chạy trên DB thật để biết còn thiếu ở đâu."""
    rows = (db.query(POItem.progress_status,
                     func.count(POItem.id),
                     func.sum(case((PurchaseHistory.id.is_(None), 1), else_=0)),
                     func.sum(case((POItem.qty_received > 0, 1), else_=0)))
            .outerjoin(PurchaseHistory, PurchaseHistory.po_item_id == POItem.id)
            .group_by(POItem.progress_status).all())
    print(f"{'Tiến độ dòng':<40}{'Tổng':>8}{'Thiếu LS':>10}{'Đã nhận':>10}")
    for st, total, missing, received in sorted(rows, key=lambda r: -r[1]):
        # B-06: cột lưu MÃ. In kèm nhãn để người chạy đối chiếu, nhưng --status vẫn nhận MÃ.
        nhan = PO_PROGRESS_STATUS.label_of(st or "")
        ten = (f"{st} — {nhan}" if nhan else (st or "(trống)"))
        print(f"{ten:<40}{total:>8}{int(missing or 0):>10}{int(received or 0):>10}")
    print("\nCột 'Thiếu LS' = số dòng chưa có bản ghi lịch sử mua hàng.")


def _write_csv(path: str, plan: list[dict], applied: bool) -> None:
    """Xuất danh sách dòng đã/sẽ ghi. Khi --apply, file này CHÍNH LÀ vé hoàn tác (--undo)."""
    if not path or not plan:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(plan[0].keys()))
        w.writeheader()
        w.writerows(plan)
    print(f"Đã xuất {len(plan)} dòng ra {path}"
          + (" — GIỮ FILE NÀY để hoàn tác bằng --undo nếu cần." if applied else " (rà trước khi --apply)."))


def _undo(db, path: str, apply: bool) -> None:
    """Xóa đúng các bản ghi lịch sử do lần chạy trước tạo ra, theo cột history_id trong file CSV."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        ids = [int(r["history_id"]) for r in csv.DictReader(f) if (r.get("history_id") or "").strip()]
    if not ids:
        print(f"{path} không có cột history_id nào — file này là bản chạy thử, không có gì để hoàn tác.")
        return
    found = db.query(PurchaseHistory).filter(PurchaseHistory.id.in_(ids)).all()
    print(f"File ghi {len(ids)} bản ghi; còn trong DB: {len(found)}")
    if not apply:
        print("(chạy thử) thêm --apply để xóa thật.")
        return
    for h in found:
        db.delete(h)
    db.commit()
    print(f"Đã xóa {len(found)} bản ghi lịch sử. Tổng bảng còn: {db.query(PurchaseHistory.id).count()}")


def main(apply: bool, statuses: list[str], include_received: bool, stats: bool,
         csv_path: str, undo: str) -> None:
    db = SessionLocal()
    try:
        if undo:
            _undo(db, undo, apply)
            return
        if stats:
            _print_stats(db)
            return

        # Dòng ĐỦ ĐIỀU KIỆN vào lịch sử: tiến độ nằm trong `statuses`, hoặc (nếu bật
        # --include-received) đã nhận hàng thực tế dù cột tiến độ chưa chuẩn — đơn cũ
        # import từ Misa hay rơi vào ca này.
        eligible = POItem.progress_status.in_(statuses)
        if include_received:
            eligible = or_(eligible, POItem.qty_received > 0)
        # Không đưa dòng đã hủy vào lịch sử mua hàng dù có phát sinh nhận hàng.
        # B-06: bỏ vế `POItem.line_status != "Hủy đơn"` từng đứng ở đây — cột đó là mức GIAO
        # HÀNG của dòng (not_delivered/partial/full, xem PO_ITEM_LINE_STATUS), không bao giờ
        # mang giá trị hủy, nên vế đó chưa từng lọc được gì. Việc hủy dòng nằm ở
        # `progress_status`, đã có ở vế đầu.
        not_cancelled = and_(POItem.progress_status != PROG_CANCELLED,
                             PurchaseOrder.status != "cancelled")

        base = (db.query(POItem, PurchaseOrder)
                .join(PurchaseOrder, PurchaseOrder.id == POItem.po_id)
                .filter(eligible, not_cancelled))
        done = base.count()
        have = db.query(PurchaseHistory.id).count()

        rows = (base.outerjoin(PurchaseHistory, PurchaseHistory.po_item_id == POItem.id)
                .filter(PurchaseHistory.id.is_(None))
                .order_by(POItem.id.asc()).all())

        print(f"Điều kiện: tiến độ ∈ {statuses}"
              + (" HOẶC đã nhận hàng (qty_received > 0)" if include_received else ""))
        print(f"Dòng đủ điều kiện: {done} | đã có lịch sử (toàn bảng): {have} | THIẾU: {len(rows)}\n")
        if not rows:
            print("Không có gì để đồng bộ.")
            return

        src_count: dict[str, int] = {}
        written = 0
        plan: list[dict] = []          # để xuất CSV rà trước khi ghi
        new_objs: list = []            # để lấy id sau commit → file hoàn tác
        for item, po in rows:
            day, src = _completed_at(db, po, item)
            src_count[src] = src_count.get(src, 0) + 1
            written += 1
            plan.append({"po_code": po.code, "product_code": item.product_code,
                         "product_name": item.product_name, "supplier_code": po.supplier_code,
                         "qty_order": float(item.qty_order or 0), "price": float(item.price or 0),
                         "progress_status": item.progress_status, "completed_at": day,
                         "nguon_ngay": src, "po_item_id": item.id, "history_id": ""})
            if written <= 20 or written % 100 == 0:
                print(f"  [{written:>4}] {po.code} / {item.product_code} — {day} ({src})")
            if apply:
                # snapshot_line đóng dấu completed_at = hôm nay (đúng cho luồng chạy thật).
                # Dữ liệu cũ thì phải sửa lại theo ngày suy ra ở trên, kẻo cả kho lịch sử
                # cùng mang ngày chạy script.
                obj = snapshot_line(db, po, item)
                if obj is not None:
                    obj.completed_at = day
                    new_objs.append((len(plan) - 1, obj))
                if written % BATCH == 0:
                    db.commit()

        if apply:
            db.commit()
            for idx, obj in new_objs:   # sau commit mới có id — ghi vào file để hoàn tác được
                plan[idx]["history_id"] = obj.id
            print(f"\nĐã ghi {written} dòng lịch sử. Tổng bảng: {db.query(PurchaseHistory.id).count()}")
        else:
            print(f"\n(chạy thử) sẽ ghi {written} dòng — thêm --apply để ghi thật.")
        _write_csv(csv_path, plan, apply)
        print("Nguồn ngày chốt: " + ", ".join(f"{k}={v}" for k, v in sorted(src_count.items())))
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Đồng bộ lịch sử mua hàng cho đơn ĐMH cũ")
    ap.add_argument("--apply", action="store_true", help="Ghi vào DB (mặc định chỉ chạy thử, in ra)")
    ap.add_argument("--stats", action="store_true", help="Chỉ in phân bố tiến độ dòng × thiếu lịch sử")
    ap.add_argument("--status", default=PROG_COMPLETED,
                    help='MÃ tiến độ được coi là đã mua xong, cách nhau bằng dấu phẩy '
                         f'(mặc định "{PROG_COMPLETED}"; xem PO_PROGRESS_STATUS)')
    ap.add_argument("--include-received", action="store_true",
                    help="Lấy thêm mọi dòng ĐÃ NHẬN HÀNG dù cột tiến độ chưa chuẩn (đơn cũ/import Misa)")
    ap.add_argument("--csv", default="/app/backfill_purchase_history.csv",
                    help="File CSV liệt kê dòng sẽ/đã ghi (mặc định /app/backfill_purchase_history.csv)")
    ap.add_argument("--undo", default="", help="Hoàn tác: xóa các bản ghi ghi trong file CSV của lần chạy --apply")
    a = ap.parse_args()
    main(a.apply, [s.strip() for s in a.status.split(",") if s.strip()],
         a.include_received, a.stats, a.csv, a.undo)
