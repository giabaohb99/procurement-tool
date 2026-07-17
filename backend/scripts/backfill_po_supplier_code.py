"""Backfill mã NCC (supplier_code) cho Đơn mua hàng bị thiếu.

Chạy TRONG container api (có sẵn PYTHONPATH tới app):
    docker compose exec -T api python -m scripts.backfill_po_supplier_code          # dry-run (chỉ in)
    docker compose exec -T api python -m scripts.backfill_po_supplier_code --apply  # ghi vào DB

Logic: với PO có supplier_code rỗng nhưng có supplier_name → dò trong bảng NCC theo
tên pháp lý (name) đã chuẩn hoá (bỏ khoảng trắng thừa, không phân biệt hoa/thường) để
lấy code. In rõ từng đơn: khớp / không khớp. Chỉ ghi khi truyền --apply.
"""
import sys

from app.core.database import SessionLocal
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.supplier.model import Supplier


def _norm(s: str) -> str:
    return " ".join((s or "").split()).upper()


def main(apply: bool) -> None:
    db = SessionLocal()
    try:
        by_name = {_norm(s.name): s.code for s in db.query(Supplier).all() if (s.code or "").strip()}

        pos = (db.query(PurchaseOrder)
               .filter((PurchaseOrder.supplier_code == "") | (PurchaseOrder.supplier_code.is_(None)))
               .order_by(PurchaseOrder.id.asc()).all())

        print(f"Tìm thấy {len(pos)} đơn thiếu supplier_code.\n")
        matched = missing = no_name = 0
        for po in pos:
            name = (po.supplier_name or "").strip()
            if not name:
                no_name += 1
                print(f"  [BỎ QUA] {po.code}: không có cả supplier_name (đơn nháp?)")
                continue
            code = by_name.get(_norm(name))
            if code:
                matched += 1
                print(f"  [KHỚP ] {po.code}: '{name}' -> {code}")
                if apply:
                    po.supplier_code = code
                    po.updated_by = po.updated_by or 0
            else:
                missing += 1
                print(f"  [!KHÔNG] {po.code}: '{name}' -> không có NCC nào trùng tên")

        if apply and matched:
            db.commit()
            print(f"\nĐã cập nhật {matched} đơn.")
        else:
            print(f"\n(dry-run) sẽ cập nhật {matched} đơn — thêm --apply để ghi.")
        print(f"Tổng: khớp={matched}, không khớp tên={missing}, không có tên={no_name}")
    finally:
        db.close()


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
