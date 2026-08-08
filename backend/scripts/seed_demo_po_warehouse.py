"""Gán KHO NHẬN cho các dòng đơn mua hàng — để thử tab "Đơn hàng về kho" ở chi tiết Kho.

CHỈ DÙNG CHO LOCAL. Chỉ đụng vào dòng đang BỎ TRỐNG kho, và chỉ gán cho các kho truyền vào.

    docker compose exec -T api python -m scripts.seed_demo_po_warehouse --warehouses "Kho B18,Kho C1-2"
    docker compose exec -T api python -m scripts.seed_demo_po_warehouse --warehouses "Kho B18" --clear

Lần giao (tab_po_delivery) của dòng cũng được gán theo kho của dòng nếu đang trống — để cột
"Đã nhận (kho này)" có số.
"""
import argparse
from itertools import cycle

import app.core.all_models  # noqa: F401 — nạp đủ model, tránh lỗi mapper của relationship chéo module
from app.core.database import SessionLocal
from app.modules.catalog.model import Warehouse
from app.modules.purchase_order.model import PODelivery, POItem


def main(codes: list[str], clear: bool) -> None:
    db = SessionLocal()
    try:
        known = {w.code for w in db.query(Warehouse).filter(Warehouse.code.in_(codes)).all()}
        missing = [c for c in codes if c not in known]
        if missing:
            print(f"Không có kho: {missing}. Bỏ qua.")
            codes = [c for c in codes if c in known]
        if not codes:
            return

        if clear:
            items = db.query(POItem).filter(POItem.warehouse_code.in_(codes)).all()
            ids = [i.id for i in items]
            for it in items:
                it.warehouse_code = ""
            n_d = 0
            if ids:
                for d in db.query(PODelivery).filter(PODelivery.po_item_id.in_(ids)).all():
                    d.warehouse_code = ""
                    n_d += 1
            db.commit()
            print(f"Đã xóa kho khỏi {len(items)} dòng hàng và {n_d} lần giao.")
            return

        items = db.query(POItem).filter(
            (POItem.warehouse_code == "") | (POItem.warehouse_code.is_(None))).all()
        if not items:
            print("Mọi dòng hàng đều đã có kho — không gán thêm.")
            return
        wheel = cycle(codes)
        for it in items:
            it.warehouse_code = next(wheel)
        db.flush()

        n_d = 0
        by_item = {it.id: it.warehouse_code for it in items}
        for d in db.query(PODelivery).filter(PODelivery.po_item_id.in_(list(by_item))).all():
            if not (d.warehouse_code or "").strip():
                d.warehouse_code = by_item[d.po_item_id]
                n_d += 1
        db.commit()
        print(f"Đã gán kho {codes} cho {len(items)} dòng hàng và {n_d} lần giao.")
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--warehouses", required=True, help="Danh sách MÃ kho, cách nhau bằng dấu phẩy")
    ap.add_argument("--clear", action="store_true", help="Xóa kho khỏi các dòng đang gán các kho này")
    a = ap.parse_args()
    main([c.strip() for c in a.warehouses.split(",") if c.strip()], a.clear)
