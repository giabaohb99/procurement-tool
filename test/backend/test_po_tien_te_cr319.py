"""bao-CR-319 — nền tiền tệ của đơn mua hàng.

Điểm cần canh: công nợ và tồn kho KHÔNG có cột loại tiền, nên mọi con số chảy sang
hai chỗ đó bắt buộc đã quy đổi. Nếu ai đó lỡ tay bỏ tỷ giá ra khỏi `recompute_effects`,
đơn 10 USD sẽ nằm trong công nợ đúng 10 đồng mà không có lỗi nào nổi lên — test này
là cái chuông cho tình huống đó.
"""
import pytest

from app.modules.purchase_order import service
from app.modules.purchase_order.model import OrderType, POItem, PurchaseOrder
from app.modules.purchase_order.schema import DeliveryIn, POItemIn
from app.modules.payable.model import Payable

RATE = 25_000.0


def _make_po(db, seed, **kw):
    po = PurchaseOrder(code=kw.pop("code", "PO-USD-001"), company_id=seed.company_id,
                       supplier_code="NX", supplier_name=seed.sup_name,
                       order_date="2026-09-08", status="approved", **kw)
    db.add(po)
    db.flush()
    return po


def _item_in(**kw):
    base = dict(product_code="SP01", product_name="Hàng nhập", item_group="Nhãn",
                unit="cái", qty_request=2, qty_order=2, price=10, vat=0,
                required_date="2026-09-20", warehouse_code="KHO01")
    base.update(kw)
    return POItemIn(**base)


# ── rate_of ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("raw, mong_doi", [
    (None, 1.0),        # cột chưa có giá trị (dữ liệu cũ trước migration)
    (0, 1.0),           # 0 là bẫy chết người: nhân vào thành 0 đồng, không ai báo lỗi
    ("", 1.0),
    (RATE, RATE),
])
def test_rate_of_khong_bao_gio_tra_ve_0(raw, mong_doi):
    assert service.rate_of(POItem(exchange_rate=raw)) == mong_doi


def test_rate_of_khi_doi_tuong_chua_co_cot():
    """Đối tượng không có thuộc tính exchange_rate vẫn phải ra 1, không nổ AttributeError."""
    assert service.rate_of(object()) == 1.0


# ── _save_items: dòng chép loại tiền / tỷ giá từ đơn ─────────────────────────────
def test_dong_hang_thua_huong_loai_tien_cua_don(db, seed):
    po = _make_po(db, seed, order_type=int(OrderType.IMPORT), currency="USD", exchange_rate=RATE)
    service._save_items(db, po, [_item_in()], user_id=1)
    db.flush()

    it = service.items_of(db, po.id)[0]
    assert it.currency == "USD"
    assert float(it.exchange_rate) == RATE


def test_dong_tra_bang_tien_viet_trong_don_ngoai_te_khong_dinh_ty_gia(db, seed):
    """Đơn nhập khẩu vẫn lẫn dòng trả bằng VNĐ (phí nội địa) — dòng đó tỷ giá phải là 1."""
    po = _make_po(db, seed, order_type=int(OrderType.IMPORT), currency="USD", exchange_rate=RATE)
    service._save_items(db, po, [_item_in(currency="VND")], user_id=1)
    db.flush()

    it = service.items_of(db, po.id)[0]
    assert it.currency == "VND"
    assert float(it.exchange_rate) == 1.0


def test_don_trong_nuoc_mac_dinh_vnd_ty_gia_1(db, seed):
    po = _make_po(db, seed)
    service._save_items(db, po, [_item_in()], user_id=1)
    db.flush()

    it = service.items_of(db, po.id)[0]
    assert it.currency == "VND"
    assert float(it.exchange_rate) == 1.0


# ── recompute_effects: công nợ + base_amount đã quy đổi ──────────────────────────
def test_cong_no_va_base_amount_dung_so_quy_doi(db, seed):
    po = _make_po(db, seed, order_type=int(OrderType.IMPORT), currency="USD", exchange_rate=RATE)
    service._save_items(db, po, [_item_in(deliveries=[DeliveryIn(
        received_qty=2, received_date="2026-09-10", warehouse_code="KHO01")])], user_id=1)
    db.flush()
    service.recompute_effects(db, po, user_id=1)
    db.flush()

    it = service.items_of(db, po.id)[0]
    # amount giữ NGUYÊN TỆ: 2 × 10 USD, VAT 0
    assert float(it.amount) == 20.0
    assert float(it.base_amount) == 20.0 * RATE

    pay = db.query(Payable).filter(Payable.po_id == po.id,
                                   Payable.source_type == "goods").one()
    assert float(pay.amount) == 20.0 * RATE


def test_don_vnd_khong_doi_mot_dong_nao(db, seed):
    """Chốt chặn hồi quy: dữ liệu cũ (VNĐ, tỷ giá 1) phải ra đúng con số như trước CR-319."""
    po = _make_po(db, seed, code="PO-VND-001")
    service._save_items(db, po, [_item_in(price=1000, vat=10, deliveries=[DeliveryIn(
        received_qty=2, received_date="2026-09-10", warehouse_code="KHO01")])], user_id=1)
    db.flush()
    service.recompute_effects(db, po, user_id=1)
    db.flush()

    it = service.items_of(db, po.id)[0]
    assert float(it.amount) == 2200.0          # 2 × 1000 × 1,1
    assert float(it.base_amount) == 2200.0
    pay = db.query(Payable).filter(Payable.po_id == po.id,
                                   Payable.source_type == "goods").one()
    assert float(pay.amount) == 2000.0
    assert float(pay.vat) == 200.0
