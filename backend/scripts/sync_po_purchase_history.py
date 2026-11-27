"""bao-CR-790 — dựng / sửa bản ghi LỊCH SỬ MUA HÀNG đang mở cho các dòng ĐMH đã nhận hàng (dữ liệu có từ trước khi có tính năng).

Chạy TRONG container api (LUÔN chạy thử trước, chỉ ghi khi có --apply):
    docker compose exec -T api python -m scripts.sync_po_purchase_history            # chạy thử, in số liệu
    docker compose exec -T api python -m scripts.sync_po_purchase_history --apply    # ghi thật
    docker compose exec -T api python -m scripts.sync_po_purchase_history --po PO01260 --apply   # chỉ một đơn

Vì sao cần: từ bao-CR-790 lịch sử mua hàng được ghi ngay khi hàng về kho (`purchase_history.service.sync_po_history`, gọi sau mỗi
lần lưu / đổi trạng thái ĐMH). Các đơn đã nhận hàng TRƯỚC đó không đi qua chỗ gọi ấy nên chưa có bản ghi. Script gọi đúng hàm đó cho
từng đơn — kết quả giống hệt luồng chạy thật:
  - dòng đã nhận hàng của đơn đã duyệt (chưa hủy, chưa xóa) -> bản ghi ĐANG MỞ, số lấy theo ĐMH hiện tại;
  - dòng `completed` chưa có bản ghi -> bản ghi ĐÃ CHỐT (và chốt dòng sổ giá);
  - bản ghi đang mở của dòng hết đủ điều kiện -> xóa; bản ghi đã chốt và dữ liệu cũ nạp từ Excel KHÔNG bị đụng.

An toàn khi chạy lại: lần hai không đổi gì. Chạy thử ghi vào phiên để đếm đúng rồi rollback.
"""
import argparse

from sqlalchemy import func, or_

import app.core.all_models  # noqa: F401 — nạp đủ model để SQLAlchemy dựng được mapper
from app.core.database import SessionLocal
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_history.service import OPEN, sync_po_history
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.line_status_service import PO_DEAD_STATUSES, PO_PENDING_STATUSES

BATCH = 100


def _target_orders(db, po_code: str) -> list[int]:
    """Id ĐMH cần dựng lại: đơn được tính (đã duyệt trở đi, chưa xóa mềm) HOẶC đơn còn bản ghi đang mở (có thể đã hết điều kiện)."""
    query = db.query(PurchaseOrder.id)
    if po_code:
        return [r[0] for r in query.filter(PurchaseOrder.code == po_code).all()]
    stale = db.query(PurchaseHistory.po_id).filter(PurchaseHistory.line_stage == OPEN).distinct()
    live = query.filter(or_(
        PurchaseOrder.id.in_(stale),
        PurchaseOrder.is_deleted.is_(False) & PurchaseOrder.status.notin_([*PO_PENDING_STATUSES, *PO_DEAD_STATUSES])))
    return sorted(r[0] for r in live.all())


def _print_table(db, title: str) -> None:
    rows = (db.query(PurchaseHistory.source, PurchaseHistory.line_stage, func.count(PurchaseHistory.id))
            .group_by(PurchaseHistory.source, PurchaseHistory.line_stage)
            .order_by(PurchaseHistory.source, PurchaseHistory.line_stage).all())
    print(title)
    for source, stage, count in rows:
        print(f"  nguồn {source:<8} giai đoạn {stage} ({'đang mở' if stage == OPEN else 'đã chốt'}): {count}")


def main(apply: bool, po_code: str) -> None:
    db = SessionLocal()
    try:
        ids = _target_orders(db, po_code)
        _print_table(db, "Trước khi chạy:")
        total = {"inserted": 0, "updated": 0, "deleted": 0, "finalized": 0}
        touched = 0
        for start in range(0, len(ids), BATCH):
            for po in db.query(PurchaseOrder).filter(PurchaseOrder.id.in_(ids[start:start + BATCH])).all():
                stats = sync_po_history(db, po)
                if any(stats.values()):
                    touched += 1
                for key, value in stats.items():
                    total[key] += value
            if apply:
                db.commit()
        db.flush()
        _print_table(db, "Sau khi chạy:" if apply else "Sau khi chạy (CHẠY THỬ, chưa ghi):")
        print(f"Đơn đã xét: {len(ids)} · đơn có thay đổi: {touched} · thêm {total['inserted']} · sửa {total['updated']} · "
              f"xóa {total['deleted']} · chốt {total['finalized']}")
        if apply:
            db.commit()
            print("ĐÃ GHI.")
        else:
            db.rollback()
            print("(chạy thử) thêm --apply để ghi thật.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dựng bản ghi lịch sử mua hàng đang mở cho các dòng ĐMH đã nhận hàng")
    parser.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ chạy thử)")
    parser.add_argument("--po", default="", help="chỉ chạy một đơn theo mã, ví dụ PO01260")
    args = parser.parse_args()
    main(args.apply, args.po.strip())
