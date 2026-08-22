"""Dòng ĐMH đã nhận hàng thì KHÓA nhận diện sản phẩm (Mã hàng / ĐVT).

Đổi mã hàng sau khi đã nhận sẽ dời phiếu nhập kho + tồn kho đã ghi theo mã cũ
sang mã khác → sai số liệu kho. Backend phải chặn, không chỉ ẩn nút ở giao diện.
"""
import pytest
from fastapi import HTTPException

from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.schema import POItemIn
from app.modules.purchase_order.service import _save_items


def _po_voi_dong(db, qty_received: float):
    po = PurchaseOrder(code="PO1", status="approved")
    db.add(po)
    db.commit()
    db.refresh(po)
    it = POItem(po_id=po.id, product_code="SP001", product_name="Hàng A", unit="Cái",
                qty_order=10, qty_received=qty_received, progress_status="received")
    db.add(it)
    db.commit()
    db.refresh(it)
    return po, it


def _payload(it, **doi):
    base = dict(id=it.id, product_code=it.product_code, product_name=it.product_name,
                unit=it.unit, qty_order=float(it.qty_order or 0))
    base.update(doi)
    return [POItemIn(**base)]


def test_da_nhan_hang_khong_doi_duoc_ma_hang(db):
    po, it = _po_voi_dong(db, qty_received=4)
    with pytest.raises(HTTPException) as e:
        _save_items(db, po, _payload(it, product_code="SP999"), user_id=1)
    assert e.value.status_code == 400
    assert "Mã hàng" in e.value.detail


def test_da_nhan_hang_khong_doi_duoc_dvt(db):
    po, it = _po_voi_dong(db, qty_received=4)
    with pytest.raises(HTTPException) as e:
        _save_items(db, po, _payload(it, unit="Thùng"), user_id=1)
    assert e.value.status_code == 400
    assert "ĐVT" in e.value.detail


def test_da_nhan_hang_khong_doi_duoc_ten_hang(db):
    po, it = _po_voi_dong(db, qty_received=4)
    with pytest.raises(HTTPException) as e:
        _save_items(db, po, _payload(it, product_name="Hàng B"), user_id=1)
    assert e.value.status_code == 400
    assert "Tên hàng" in e.value.detail


def test_da_nhan_hang_van_luu_duoc_khi_khong_doi_gi(db):
    """Lưu lại y nguyên (vd chỉ sửa SL/giá) thì không được báo lỗi oan."""
    po, it = _po_voi_dong(db, qty_received=4)
    _save_items(db, po, _payload(it, qty_order=12), user_id=1)
    db.refresh(it)
    assert float(it.qty_order) == 12
    assert it.product_code == "SP001" and it.product_name == "Hàng A"


def test_chua_nhan_hang_van_doi_duoc_ma_hang(db):
    po, it = _po_voi_dong(db, qty_received=0)
    _save_items(db, po, _payload(it, product_code="SP999"), user_id=1)
    db.refresh(it)
    assert it.product_code == "SP999"
