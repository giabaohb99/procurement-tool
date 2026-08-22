"""Nạp CÔNG NỢ MẪU cho 1 nhà cung cấp — để test tab "Công nợ" (dashboard) ở màn chi tiết NCC.

CHỈ DÙNG CHO LOCAL. Mọi dòng sinh ra đều có invoice_no bắt đầu bằng "DEMO-" nên xóa lại rất gọn.

    docker compose exec -T api python -m scripts.seed_demo_payables --supplier "Cẩm Hùng"
    docker compose exec -T api python -m scripts.seed_demo_payables --supplier "Cẩm Hùng" --clear   # chỉ xóa

Dữ liệu trải đủ 5 mốc tuổi nợ (chưa đến hạn → quá hạn >90 ngày), cả 2 luồng nợ
(hàng hóa / vận chuyển) và cả 3 trạng thái (unpaid / partial / paid),
phát sinh rải trong 6 tháng gần nhất để biểu đồ theo tháng có cột.
"""
import argparse
from datetime import date, timedelta

from app.core.database import SessionLocal
from app.modules.payable.model import Payable
from app.modules.payable.service import recalc_status
from app.modules.supplier.model import Supplier

VAT_RATE = 0.08
DEMO_PREFIX = "DEMO-"

# (số ngày phát sinh trước hôm nay, số ngày tới hạn kể từ ngày phát sinh, tiền trước VAT, luồng, % đã trả)
# paid_pct > 1  → TRẢ DƯ (remaining âm) ; amount âm → hóa đơn ĐIỀU CHỈNH GIẢM / trả hàng.
ROWS = [
    (5, 30, 12_500_000, "goods", 0),        # chưa đến hạn
    (12, 30, 8_400_000, "goods", 0.5),      # chưa đến hạn, trả một phần
    (20, 7, 3_200_000, "shipping", 0),      # quá hạn ~13 ngày → 1-30
    (35, 15, 21_000_000, "goods", 0),       # quá hạn ~20 ngày → 1-30
    (60, 15, 5_600_000, "shipping", 0.3),   # quá hạn ~45 ngày → 31-60
    (75, 30, 17_800_000, "goods", 0),       # quá hạn ~45 ngày → 31-60
    (110, 30, 9_900_000, "goods", 0),       # quá hạn ~80 ngày → 61-90
    (135, 30, 4_300_000, "shipping", 0.6),  # quá hạn ~105 ngày → >90
    (160, 30, 26_500_000, "goods", 0),      # quá hạn ~130 ngày → >90
    (45, 30, 7_200_000, "goods", 1),        # đã tất toán
    (95, 30, 13_400_000, "goods", 1),       # đã tất toán
    (150, 30, 2_800_000, "shipping", 1),    # đã tất toán
    (25, 30, 6_000_000, "goods", 1.25),     # trả dư 25% → remaining âm
    (70, 30, -4_500_000, "goods", 0),       # điều chỉnh giảm / trả hàng → total âm
    (18, 30, -1_200_000, "shipping", 0),    # giảm trừ cước vận chuyển
]


def main(supplier_code: str, clear_only: bool) -> None:
    db = SessionLocal()
    try:
        sup = db.query(Supplier).filter(Supplier.code == supplier_code).first()
        if not sup:
            codes = [s.code for s in db.query(Supplier).limit(20).all()]
            print(f"Không tìm thấy NCC có mã '{supplier_code}'. Vài mã đang có: {codes}")
            return

        old = (db.query(Payable)
               .filter(Payable.supplier_code == sup.code, Payable.invoice_no.like(f"{DEMO_PREFIX}%"))
               .all())
        for p in old:
            db.delete(p)
        db.flush()
        print(f"Đã xóa {len(old)} dòng công nợ mẫu cũ của '{sup.code}'.")
        if clear_only:
            db.commit()
            return

        today = date.today()
        for i, (ago, term, amount, source, paid_pct) in enumerate(ROWS, start=1):
            incur = today - timedelta(days=ago)
            due = incur + timedelta(days=term)
            vat = round(amount * VAT_RATE, 2)
            total = round(amount + vat, 2)
            paid = round(total * paid_pct, 2)
            p = Payable(
                company_id=sup.company_id if hasattr(sup, "company_id") else 0,
                supplier_code=sup.code, supplier_name=sup.name,
                source_type=source, ref_type="delivery", ref_id=0,
                po_id=0, po_code=f"PO-DEMO-{i:03d}", invoice_no=f"{DEMO_PREFIX}{i:03d}",
                incur_date=incur.isoformat(), period=str(incur.year), due_date=due.isoformat(),
                amount=amount, vat=vat, total=total, paid_amount=paid,
            )
            # Gọi thẳng recalc_status thay vì chép lại luật: bản chép tay ở đây từng phải kèm
            # chú thích "bám đúng service.recalc_status" — nghĩa là nó đã là bản sao chờ lệch.
            # Nó cũng đặt luôn `remaining` và `status` (mã B-05).
            recalc_status(p)
            db.add(p)
        db.commit()
        print(f"Đã nạp {len(ROWS)} khoản công nợ mẫu cho '{sup.code}' ({sup.name}).")
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--supplier", default="Cẩm Hùng", help="Mã (code) nhà cung cấp")
    ap.add_argument("--clear", action="store_true", help="Chỉ xóa dữ liệu mẫu, không nạp mới")
    a = ap.parse_args()
    main(a.supplier, a.clear)
