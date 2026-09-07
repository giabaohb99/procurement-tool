"""bao-CR-307 — cột "Đơn giá (Sau VAT)" = đơn giá × (1 + VAT%), làm tròn 2 số lẻ.

Cột nằm trong bộ cột dòng dùng chung nên phải có mặt ở CẢ HAI file Excel:
màn Tiến độ mua hàng và màn Đơn mua hàng (file ĐMH bê nguyên bộ cột Tiến độ, CR-068).
"""
from app.modules.purchase_order import export as po_ex
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_progress import export as pex


def _row(price: float, vat: float) -> dict:
    po = PurchaseOrder(code="PO1", status="approved")
    it = POItem(po_id=1, product_code="SP1", qty_order=10, price=price, vat=vat)
    return pex.row_values(po, it, None, show_supplier=True)


def test_don_gia_sau_vat_lam_tron_2_so_le():
    # Case thật của khách: 166.666,67 × 1,08 = 180.000,0036 — phải ra giá chẵn 180.000
    assert _row(166666.67, 8)["price_after_vat"] == 180000.0


def test_vat_0_thi_bang_dung_don_gia():
    # VAT 0 vừa là "chưa nhập" vừa là "hàng không chịu thuế" — sau VAT = trước VAT
    assert _row(12345.6789, 0)["price_after_vat"] == 12345.68


def test_don_gia_0_khong_no():
    assert _row(0, 8)["price_after_vat"] == 0


def test_cot_dung_ngay_sau_vat_o_ca_hai_file():
    """Vị trí khách yêu cầu: sau cột VAT%, trước Thành tiền — ở cả file Tiến độ lẫn file ĐMH."""
    progress_keys = [c.key for c in pex.columns_for(show_supplier=True)]
    i = progress_keys.index("vat")
    assert progress_keys[i + 1] == "price_after_vat"
    assert progress_keys[i + 2] == "order_amount"

    dmh_keys = [c.key for c in po_ex.line_columns(show_supplier=True)]
    j = dmh_keys.index("vat")
    assert dmh_keys[j + 1] == "price_after_vat"
