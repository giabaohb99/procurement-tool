"""bao-CR-522 — cột «Tên trên hóa đơn» ở popup Lịch sử mua hàng của ĐMH.

Lần mua qua ĐMH trên hệ có sẵn tên trong `extra.invoice_name`; dòng dữ liệu cũ (nạp Excel) không
có, nên lùi về tên đang khai ở danh mục sản phẩm và GẮN CỜ để giao diện không trình bày nó như
tên đã xuất trên hóa đơn lần đó.
"""
from app.modules.product.model import Product
from app.modules.purchase_history.controller import _attach_invoice_names


def test_history_name_wins_and_legacy_falls_back_to_catalog_with_flag(db):
    db.add(Product(code="SP-HD", name="Chai 500ml", invoice_name="Chai nhựa HDPE 500ml",
                   is_active=True, created_by=0, updated_by=0))
    db.commit()
    rows = [
        {"product_code": "SP-HD", "extra": {"invoice_name": "Chai HDPE xuất HĐ"}},   # qua ĐMH
        {"product_code": "SP-HD", "extra": {}},                                       # dữ liệu cũ
        {"product_code": "KHONG-CO", "extra": {}},                                    # mã không có
    ]
    _attach_invoice_names(db, rows)
    assert rows[0]["invoice_name"] == "Chai HDPE xuất HĐ" and rows[0]["invoice_name_from_catalog"] is False
    assert rows[1]["invoice_name"] == "Chai nhựa HDPE 500ml" and rows[1]["invoice_name_from_catalog"] is True
    assert rows[2]["invoice_name"] == "" and rows[2]["invoice_name_from_catalog"] is False


def test_empty_page_does_not_query(db):
    rows: list[dict] = []
    _attach_invoice_names(db, rows)
    assert rows == []
