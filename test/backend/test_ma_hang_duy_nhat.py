"""Mã hàng DUY NHẤT trên phiếu YCMH — còn ĐMH ĐƯỢC PHÉP trùng (bao-CR-308).

YCMH chặn vì dòng ĐMH nối ngược về dòng YCMH bằng CHUỖI `product_code` (không có khóa dòng):
`sync_from_purchase_orders` cộng dồn SL đặt/nhận theo mã rồi ghi CÙNG con số đó vào MỌI dòng
YCMH trùng mã → tiến độ nhân đôi, kéo theo trạng thái dòng và trạng thái phiếu sai.

ĐMH thì chiều gộp là an toàn (nhiều dòng cùng mã cộng gộp đúng, giống một YCMH rải ra nhiều
ĐMH) và nghiệp vụ CẦN trùng: mua theo bộ chứng từ — cùng mã nắp cho 2 lô chai khác nhau,
khác Tên trên hóa đơn / số hóa đơn. Giao diện hỏi xác nhận để chặn gõ nhầm, backend không chặn.

Luật YCMH là RATCHET: chỉ chặn TRÙNG MỚI. Phiếu đã lỡ trùng từ trước vẫn phải lưu lại được,
vì dòng bị khóa không xóa được — chặn cứng sẽ khóa chết những phiếu đó.
"""
import pytest
from fastapi import HTTPException

from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.schema import POItemIn
from app.modules.purchase_order.service import _save_items as po_save_items
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import PRItemIn
from app.modules.purchase_request.service import _save_items as pr_save_items


def _po(db):
    po = PurchaseOrder(code="PO1", status="approved")
    db.add(po)
    db.commit()
    db.refresh(po)
    return po


def _po_line(code: str, name: str = "Hàng A", **kw):
    return POItemIn(product_code=code, product_name=name, unit="Cái", qty_order=1, **kw)


def _pr(db):
    pr = PurchaseRequest(code="PYC1", status="draft")
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr


def _pr_line(code: str, name: str = "Hàng A"):
    return PRItemIn(product_code=code, product_name=name, qty=1, unit="Cái")


# ── ĐMH: trùng mã ĐƯỢC PHÉP (bao-CR-308) ───────────────────────────────────────
def test_dmh_hai_dong_cung_ma_luu_duoc(db):
    """Case bộ chứng từ: 2 dòng cùng mã, khác Tên trên hóa đơn — phải lưu được CẢ HAI."""
    po = _po(db)
    po_save_items(db, po,
                  [_po_line("SP001", invoice_name="Nắp chai lô xám"),
                   _po_line("SP001", invoice_name="Nắp chai lô vàng")], user_id=1)
    rows = db.query(POItem).filter(POItem.po_id == po.id).order_by(POItem.id).all()
    assert len(rows) == 2
    # Mỗi dòng giữ nguyên Tên trên hóa đơn của mình, không bị dòng kia đè
    assert {r.invoice_name for r in rows} == {"Nắp chai lô xám", "Nắp chai lô vàng"}


def test_dmh_ma_khac_nhau_thi_luu_binh_thuong(db):
    po = _po(db)
    po_save_items(db, po, [_po_line("SP001"), _po_line("SP002")], user_id=1)
    assert db.query(POItem).filter(POItem.po_id == po.id).count() == 2


def test_dmh_don_cu_da_trung_them_dong_trung_nua_van_luu(db):
    """Trước bao-CR-308 chỗ này chặn 400 — nay thêm dòng trùng thứ ba vẫn lưu bình thường."""
    po = _po(db)
    for _ in range(2):
        db.add(POItem(po_id=po.id, product_code="SP001", product_name="Hàng A", unit="Cái",
                      qty_order=1, progress_status="ordered"))
    db.commit()
    rows = db.query(POItem).filter(POItem.po_id == po.id).order_by(POItem.id).all()
    payload = [_po_line("SP001", id=r.id) for r in rows] + [_po_line("SP001")]
    po_save_items(db, po, payload, user_id=1)
    assert db.query(POItem).filter(POItem.po_id == po.id).count() == 3


# ── YCMH: vẫn chặn như cũ ───────────────────────────────────────────────────────
def test_ycmh_chan_hai_dong_cung_ma(db):
    pr = _pr(db)
    with pytest.raises(HTTPException) as e:
        pr_save_items(db, pr.id, [_pr_line("SP001"), _pr_line("SP001")], user_id=1)
    assert e.value.status_code == 400
    assert "SP001" in e.value.detail


def test_ycmh_ma_khac_nhau_thi_luu_binh_thuong(db):
    pr = _pr(db)
    pr_save_items(db, pr.id, [_pr_line("SP001"), _pr_line("SP002")], user_id=1)
    assert db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).count() == 2


def test_ycmh_da_trung_san_van_luu_lai_duoc(db):
    pr = _pr(db)
    for _ in range(2):
        db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP001", product_name="Hàng A", qty=1))
    db.commit()
    rows = (db.query(PurchaseRequestItem)
            .filter(PurchaseRequestItem.pr_id == pr.id).order_by(PurchaseRequestItem.id).all())
    payload = [PRItemIn(id=r.id, product_code="SP001", product_name="Hàng A", qty=1, unit="Cái")
               for r in rows]
    pr_save_items(db, pr.id, payload, user_id=1)
    assert db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).count() == 2
