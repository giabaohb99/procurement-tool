"""Nạp DỮ LIỆU MẪU cho CR-268 — TIỀN TREO thanh toán trước. CHỈ DÙNG CHO LOCAL.

    docker compose exec -T api python -m scripts.seed_demo_tien_treo           # nạp (tự dọn bản cũ trước)
    docker compose exec -T api python -m scripts.seed_demo_tien_treo --clear   # chỉ dọn

Dựng 2 NCC mẫu + 3 kịch bản, mỗi kịch bản DỪNG NGAY TRƯỚC thao tác người dùng
cần test — vào giao diện bấm nốt phần còn lại:

  KB1 (NCC DEMO-TREO-A) — treo GẮN ĐƠN, tự đối trừ:
      Đơn PO-TREO-1 (50tr) đã duyệt, CHƯA nhận hàng + phiếu trả trước 20tr gắn đơn ĐÃ CHI.
      -> Test: mở chi tiết ĐMH thấy cảnh báo "Đã trả trước 20.000.000 đ"; ghi nhận
         nhận hàng đủ -> công nợ 50tr sinh ra bị trừ sẵn 20tr, treo về 0.

  KB2 (NCC DEMO-TREO-A) — treo CẤP NCC, cấn tay (kịch bản 30/50/20):
      Phiếu trả trước 30tr KHÔNG gắn đơn ĐÃ CHI + đơn PO-TREO-2 đã nhận đủ -> nợ 50tr.
      -> Test: màn Công nợ bấm icon cái cân trên khoản 50tr -> cấn tối đa 30tr -> nợ còn 20tr.

  KB3 (NCC DEMO-TREO-B) — NCC hoàn tiền:
      Phiếu trả trước 15tr KHÔNG gắn đơn ĐÃ CHI.
      -> Test: mở chi tiết phiếu -> "Ghi nhận NCC hoàn tiền" 5tr rồi hoàn nốt.

Tạo phiếu + chi tiền đi qua ĐÚNG service người dùng đi (create_requests / set_status),
không INSERT tay — số liệu sinh ra y hệt thao tác thật.
"""
import argparse

import app.core.all_models  # noqa: F401 — nạp đủ model, tránh lỗi mapper quan hệ chéo module
from app.core.database import SessionLocal
from app.modules.goods_receipt import service as gr_service
from app.modules.inventory import service as inv_service
from app.modules.payable.model import Payable
from app.modules.payment_request import service as prq_service
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.payment_request.schema import LineIn, PRequestCreate
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_order.service import recompute_effects
from app.modules.supplier.model import Supplier
from app.modules.user.model import User

SUP_A = ("DEMO-TREO-A", "NCC Demo Tien Treo Anpha")
SUP_B = ("DEMO-TREO-B", "NCC Demo Tien Treo Beta")
PO_CODES = ["PO-TREO-1", "PO-TREO-2"]


def _resolve_actor(db) -> int:
    """Lấy user làm người tạo dữ liệu mẫu — ưu tiên admin cho dễ nhận ra trong audit."""
    u = db.query(User).filter(User.email == "admin").first() or db.query(User).first()
    if not u:
        raise SystemExit("DB chưa có user nào — chạy seed trước đã.")
    return u.id


def _resolve_company(db) -> int:
    from app.modules.company.model import Company

    c = (db.query(Company).filter(Company.is_active.is_(True)).first()
         or db.query(Company).first())
    if not c:
        raise SystemExit("DB chưa có công ty nào — chạy seed trước đã.")
    return c.id


def clear(db) -> None:
    codes = [SUP_A[0], SUP_B[0]]

    reqs = db.query(PaymentRequest).filter(PaymentRequest.supplier_code.in_(codes)).all()
    for r in reqs:
        db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == r.id).delete()
        db.delete(r)

    n_pay = db.query(Payable).filter(Payable.supplier_code.in_(codes)).delete(
        synchronize_session=False)

    pos = db.query(PurchaseOrder).filter(PurchaseOrder.code.in_(PO_CODES)).all()
    for po in pos:
        for d in db.query(PODelivery).filter(PODelivery.po_id == po.id).all():
            # Nhận hàng từng sinh phiếu nhập kho ngầm + tồn kho — gỡ bằng đúng helper
            # của service, đừng tự viết lại luật trừ tồn.
            gr_service.remove_for_delivery(db, d.id)
            inv_service.remove_delivery(db, d.id)
            db.delete(d)
        db.query(POItem).filter(POItem.po_id == po.id).delete(synchronize_session=False)
        db.delete(po)

    n_ph = db.query(PurchaseHistory).filter(PurchaseHistory.po_code.in_(PO_CODES)).delete(
        synchronize_session=False)
    n_sup = db.query(Supplier).filter(Supplier.code.in_(codes)).delete(
        synchronize_session=False)
    db.commit()
    print(f"Đã dọn: {len(reqs)} phiếu YCTT, {n_pay} công nợ, {len(pos)} ĐMH, "
          f"{n_ph} lịch sử mua, {n_sup} NCC mẫu.")


def _make_prepay(db, uid: int, company_id: int, sup_code: str, *,
                 po_code: str, amount: float, note: str) -> PaymentRequest:
    """Lập + duyệt + CHI một phiếu trả trước qua đúng đường service của form trắng."""
    data = PRequestCreate(request_date="2026-09-01", prepay=1, supplier_code=sup_code,
                          company_id=company_id, source_type="goods", note=note,
                          lines=[LineIn(po_code=po_code, amount=amount)])
    req = prq_service.create_requests(db, data, uid)[0]
    prq_service.set_status(db, req.id, "submitted", uid)
    prq_service.set_status(db, req.id, "approved", uid)
    prq_service.set_status(db, req.id, "paid", uid)
    return req


def _make_po(db, uid: int, company_id: int, sup_code: str, sup_name: str, *,
             code: str, qty: float, price: float, received: bool) -> PurchaseOrder:
    po = PurchaseOrder(code=code, status="approved", order_date="2026-09-01",
                       supplier_code=sup_code, supplier_name=sup_name,
                       company_id=company_id, created_by=uid, updated_by=uid)
    db.add(po)
    db.flush()
    it = POItem(po_id=po.id, product_code=f"SP-{code}", product_name=f"Hàng demo {code}",
                unit="cái", qty_order=qty, price=price, vat=0, item_group="Nhãn",
                created_by=uid, updated_by=uid)
    db.add(it)
    db.flush()
    if received:
        db.add(PODelivery(po_id=po.id, po_item_id=it.id, delivery_no=1, ship_qty=qty,
                          received_qty=qty, received_date="2026-09-02",
                          invoice_no=f"DEMO-HD-{code}", created_by=uid, updated_by=uid))
        db.flush()
    recompute_effects(db, po, uid)
    db.commit()
    return po


def main(clear_only: bool) -> None:
    db = SessionLocal()
    try:
        clear(db)
        if clear_only:
            return

        uid = _resolve_actor(db)
        company_id = _resolve_company(db)

        for code, name in (SUP_A, SUP_B):
            db.add(Supplier(code=code, name=name, supplier_type="goods", vat=0,
                            created_by=uid, updated_by=uid))
        db.commit()

        # KB1 — treo GẮN ĐƠN: chi 20tr trước, đơn 50tr CHƯA nhận hàng.
        r1 = _make_prepay(db, uid, company_id, SUP_A[0], po_code="PO-TREO-1",
                          amount=20_000_000,
                          note="DEMO CR-268 / KB1 — ứng trước 20tr cho đơn PO-TREO-1")
        _make_po(db, uid, company_id, *SUP_A, code="PO-TREO-1", qty=5,
                 price=10_000_000, received=False)

        # KB2 — treo CẤP NCC: ứng 30tr không gắn đơn, đơn 50tr ĐÃ nhận đủ -> nợ 50tr.
        # (Chi trước khi tạo đơn — đúng trình tự ngoài đời và tránh khớp nhầm hóa đơn.)
        r2 = _make_prepay(db, uid, company_id, SUP_A[0], po_code="",
                          amount=30_000_000,
                          note="DEMO CR-268 / KB2 — ứng NCC 30tr không gắn đơn")
        _make_po(db, uid, company_id, *SUP_A, code="PO-TREO-2", qty=5,
                 price=10_000_000, received=True)

        # KB3 — NCC hoàn tiền: ứng 15tr không gắn đơn cho NCC B.
        r3 = _make_prepay(db, uid, company_id, SUP_B[0], po_code="",
                          amount=15_000_000,
                          note="DEMO CR-268 / KB3 — ứng NCC 15tr, chờ NCC hoàn cọc")

        hang_a = prq_service.summarize_hanging(db, SUP_A[0])
        hang_b = prq_service.summarize_hanging(db, SUP_B[0])
        print("Đã nạp xong bộ mẫu CR-268:")
        print(f"  KB1: {r1.code} treo 20tr gắn PO-TREO-1 (đơn chưa nhận hàng)")
        print(f"  KB2: {r2.code} treo 30tr cấp NCC + công nợ PO-TREO-2 = 50tr")
        print(f"  KB3: {r3.code} treo 15tr cấp NCC ({SUP_B[0]})")
        print(f"  Kiểm chéo: treo {SUP_A[0]} = {hang_a['total']:,.0f} (kỳ vọng 50.000.000), "
              f"treo {SUP_B[0]} = {hang_b['total']:,.0f} (kỳ vọng 15.000.000)")
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--clear", action="store_true", help="Chỉ dọn dữ liệu mẫu, không nạp mới")
    a = ap.parse_args()
    main(a.clear)
