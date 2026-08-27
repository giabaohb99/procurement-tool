"""Seed DEMO cho tính năng Lịch sử mua hàng — CHỈ DÙNG LOCAL.

    docker compose exec -T api python -m app.seed_demo_purchase_history

Tạo ĐMH thật (tab_purchase_order + tab_po_item) rồi gọi ĐÚNG hàm production
`purchase_history.service.snapshot_line()` để sinh lịch sử — không insert thẳng vào bảng
lịch sử. Nhờ vậy dữ liệu demo giống hệt dữ liệu chạy thật.

Idempotent: xóa sạch dữ liệu demo cũ (nhận diện qua tiền tố mã PO `PODEMO`) rồi tạo lại,
nên chạy bao nhiêu lần cũng ra cùng kết quả và KHÔNG đụng dữ liệu thật.

Kịch bản phủ đủ thứ cần kiểm chứng trên UI:
  · 1 SP mua nhiều lần, nhiều NCC, giá tăng dần  → màn Sản phẩm: so giá + sắp xếp mới nhất trước
  · 1 ĐMH có 2 dòng hàng                          → ra 2 record (đúng yêu cầu gốc)
  · 1 NCC bán nhiều SP qua nhiều đơn              → màn NCC
  · 1 dòng CHƯA hoàn thành                        → PHẢI không xuất hiện trong lịch sử
"""
import app.core.all_models  # noqa: F401 — nạp mapper trước khi query

from app.core.database import SessionLocal
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_history.service import snapshot_line
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.service import PROG_COMPLETED, PROG_RECEIVED
from app.modules.supplier.model import Supplier

DEMO_PREFIX = "PODEMO"

# (mã PO, ngày đặt, mã NCC, company_id, khẩn, [ (mã SP, tên SP, ĐVT, SL, đơn giá, đã hoàn thành) ])
DEMO_ORDERS = [
    ("PODEMO01", "2025-03-12", "Cẩm Hùng", 1, False, [
        ("THI0002", "Thùng IDA Chai Pet Vuông 35 450ml-500ml - Xanh lá", "Cái", 5000, 4200, True),
    ]),
    ("PODEMO02", "2025-07-08", "Đông Tây", 2, False, [
        ("THI0002", "Thùng IDA Chai Pet Vuông 35 450ml-500ml - Xanh lá", "Cái", 8000, 4450, True),
    ]),
    # ĐMH 2 dòng → phải sinh 2 record lịch sử
    ("PODEMO03", "2025-11-25", "Cẩm Hùng", 1, False, [
        ("THC0003", "Thùng DC Chai Pet Vuông 35 450ml-500ml - Trắng viền đen", "Cái", 3000, 3900, True),
        ("THC0004", "Thùng DC Chai Pet Tròn 43 450ml-500ml - Trắng", "Cái", 2500, 4050, True),
    ]),
    ("PODEMO04", "2026-02-17", "Tân Đức", 1, True, [
        ("THI0002", "Thùng IDA Chai Pet Vuông 35 450ml-500ml - Xanh lá", "Cái", 6000, 4680, True),
    ]),
    ("PODEMO05", "2026-06-30", "Cẩm Hùng", 3, False, [
        ("THI0002", "Thùng IDA Chai Pet Vuông 35 450ml-500ml - Xanh lá", "Cái", 10000, 4850, True),
        ("NL0001", "Nguyên liệu Vi lượng AV4", "Kg", 500, 182000, True),
    ]),
    # Dòng CHƯA hoàn thành → KHÔNG được xuất hiện trong lịch sử
    ("PODEMO06", "2026-08-01", "Đông Tây", 1, False, [
        ("THI0002", "Thùng IDA Chai Pet Vuông 35 450ml-500ml - Xanh lá", "Cái", 4000, 5100, False),
    ]),
]

VAT = 8  # % — dùng chung cho mọi dòng demo


def _delete_old_demo(db) -> int:
    """Xóa ĐMH demo + dòng hàng + lịch sử tương ứng. Chỉ đụng bản ghi có tiền tố PODEMO."""
    pos = db.query(PurchaseOrder).filter(PurchaseOrder.code.like(f"{DEMO_PREFIX}%")).all()
    if not pos:
        return 0
    po_ids = [p.id for p in pos]
    item_ids = [i.id for i in db.query(POItem).filter(POItem.po_id.in_(po_ids)).all()]
    if item_ids:
        (db.query(PurchaseHistory)
           .filter(PurchaseHistory.po_item_id.in_(item_ids))
           .delete(synchronize_session=False))
    db.query(POItem).filter(POItem.po_id.in_(po_ids)).delete(synchronize_session=False)
    db.query(PurchaseOrder).filter(PurchaseOrder.id.in_(po_ids)).delete(synchronize_session=False)
    db.commit()
    return len(po_ids)


def run():
    db = SessionLocal()
    try:
        deleted_count = _delete_old_demo(db)
        if deleted_count:
            print(f"Đã dọn {deleted_count} ĐMH demo cũ.")

        # Tên NCC lấy từ danh mục thật để lịch sử hiển thị đúng tên pháp lý
        supplier_names = {s.code: s.name for s in db.query(Supplier).all()}

        po_count = line_count = history_count = 0
        for code, order_date, sup_code, company_id, urgent, lines in DEMO_ORDERS:
            if sup_code not in supplier_names:
                print(f"  ⚠ Bỏ qua {code}: không tìm thấy NCC '{sup_code}' trong danh mục.")
                continue

            all_done = all(ln[5] for ln in lines)
            po = PurchaseOrder(
                code=code,
                pr_code=f"PYC{code[-2:]}DEMO",
                misa_code=f"MISA{code[-2:]}",
                company_id=company_id,
                supplier_code=sup_code,
                supplier_name=supplier_names[sup_code],
                department="Phòng Mua hàng",
                nspt="Nguyễn Thanh Tiên",
                order_date=order_date,
                payment_terms="Công nợ 30 ngày",
                is_urgent=urgent,
                status="completed" if all_done else "received",
                # B-06: cột lưu MÃ, xem PO_DOCUMENT_STATUS trong app/core/status_codes.py
                document_status="full" if all_done else "none",
                note="Dữ liệu demo cho màn Lịch sử mua hàng",
            )
            db.add(po)
            db.commit()
            db.refresh(po)
            po_count += 1

            for sp_code, sp_name, unit, qty, price, done in lines:
                line_total = qty * price * (1 + VAT / 100)
                it = POItem(
                    po_id=po.id,
                    product_code=sp_code, product_name=sp_name, unit=unit,
                    qty_order=qty, qty_request=qty, qty_received=qty, qty_remaining=0,
                    price=price, vat=VAT, amount=line_total,
                    line_status="full",  # B-06: mức giao hàng của dòng, xem PO_ITEM_LINE_STATUS
                    invoice_no=f"HD{code[-2:]}{sp_code[-3:]}",
                    invoice_date=order_date,
                    document_delivery_date=order_date if done else "",
                    required_date=order_date,
                    progress_status=PROG_COMPLETED if done else PROG_RECEIVED,
                )
                db.add(it)
                db.commit()
                db.refresh(it)
                line_count += 1

                # Chỉ dòng đã hoàn thành mới có lịch sử — dùng đúng hàm production
                if done:
                    snapshot_line(db, po, it)
                    db.commit()
                    history_count += 1

        print(f"Đã tạo {po_count} ĐMH · {line_count} dòng hàng · {history_count} bản ghi lịch sử.")
        print("\nKiểm chứng nhanh:")
        for product_code in ("THI0002", "THC0003", "NL0001"):
            n = db.query(PurchaseHistory).filter(PurchaseHistory.product_code == product_code).count()
            print(f"  Sản phẩm {product_code}: {n} lần mua")
        for ncc in ("Cẩm Hùng", "Đông Tây", "Tân Đức"):
            n = db.query(PurchaseHistory).filter(PurchaseHistory.supplier_code == ncc).count()
            print(f"  NCC {ncc}: {n} lần bán")
        print("  (PODEMO06 chưa 'Hoàn thành' → không được tính vào các số trên)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
