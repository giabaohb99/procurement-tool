"""bao-CR-409 — hai cột ngày chứng từ của màn Tiến độ mua hàng (ticket prod 51).

Người dùng xin bày ra bảng hai thứ vốn chỉ có trong chi tiết ĐMH:

- **Ngày giao chứng từ cho KT** (`POItem.document_delivery_date`) — dữ liệu ĐÃ nằm trong
  hàng trả về từ lâu, nhưng không cột nào vẽ, không khai trong `_sort_map()` nên cũng
  không sắp xếp và không lọc điều kiện được. Trả về rồi bỏ xó.
- **Ngày hóa đơn của LẦN GIAO** (`PODelivery.invoice_date`) — trước CR này backend
  KHÔNG trả về, chỉ trả về *số* hóa đơn.

Bốn chốt ở đây:

1. Hàng trả về có đủ hai key, lấy đúng giá trị của dòng hàng / lần giao.
2. Dòng chưa có lần giao nào thì ngày hóa đơn là chuỗi rỗng, KHÔNG nổ `NoneType`.
3. Hai key khai trong `_sort_map()` phải trỏ vào CỘT CÓ THẬT (cùng bẫy của bao-CR-404),
   và vì `_cond_map()` lấy thẳng `_sort_map()` nên bộ lọc điều kiện có luôn.
4. Hai cột lên ĐỦ file Excel của CẢ HAI màn (Tiến độ + Đơn mua hàng), và trên màn Tiến độ
   nhãn ngày hóa đơn rút gọn đúng kiểu cột "Số HĐ" đã làm.
"""
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.core.auth import get_perm_profile
from app.modules.purchase_order import export as po_ex
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_progress import controller as pp
from app.modules.purchase_progress import export as ex
from app.modules.user.model import User


def req(qs: str):
    return SimpleNamespace(query_params=QueryParams(qs))


@pytest.fixture
def nguoi_xem_het(db, cap_quyen):
    user = User(email="ct409@test.local", employee_id=0, is_active=True)
    db.add(user)
    db.flush()
    cap_quyen(user.id, "purchase_order", scope="all", read=True)
    db.commit()
    return user


@pytest.fixture
def don_162(db):
    """Dựng lại đúng cảnh của ticket 51: đơn PO00162, dòng NHG5218.

    Số hóa đơn + ngày hóa đơn ghi ở LẦN GIAO (ô trên dòng hàng để trống — đời thật
    không ai nhập), còn ngày giao chứng từ cho kế toán ghi ở DÒNG HÀNG.
    """
    po = PurchaseOrder(code="PO00162", status="approved", supplier_name="Bao bì Cẩm Hùng",
                       order_date="2026-09-10")
    db.add(po)
    db.flush()
    it = POItem(po_id=po.id, product_code="NHG5218", product_name="Nhãn giấy",
                qty_order=100, price=1000, invoice_no="", invoice_date="",
                document_delivery_date="2026-09-14")
    db.add(it)
    db.flush()
    db.add(PODelivery(po_id=po.id, po_item_id=it.id, delivery_no=1, received_qty=100,
                      invoice_no="279", invoice_date="2026-09-14"))
    db.commit()
    return po, it


def _hang(db, user, kw: str = "") -> list[dict]:
    prof = get_perm_profile(db, user)
    q = pp._build_query(req(f"q={kw}"), db, user, prof, True, True)
    return [pp._row(po, it, dl, True) for po, it, dl in q.all()]


def test_row_carries_both_document_dates(db, nguoi_xem_het, don_162):
    """Chốt chính — hai ngày phải đi ra tới hàng, đúng giá trị đã nhập."""
    (r,) = _hang(db, nguoi_xem_het)
    assert r["document_delivery_date"] == "2026-09-14"
    assert r["delivery_invoice_date"] == "2026-09-14"
    # Ô hóa đơn trên DÒNG HÀNG vẫn trống — đừng lấy nhầm nguồn rồi tưởng là mất dữ liệu
    assert r["invoice_no"] == ""
    assert r["delivery_invoice_no"] == "279"


def test_line_without_delivery_gives_empty_invoice_date(db, nguoi_xem_het):
    """Dòng hàng chưa giao lần nào: ngày hóa đơn rỗng, không được là None."""
    po = PurchaseOrder(code="PO00163", status="approved", order_date="2026-09-11")
    db.add(po)
    db.flush()
    db.add(POItem(po_id=po.id, product_code="NHG9999", qty_order=5, price=10,
                  document_delivery_date=""))
    db.commit()

    (r,) = _hang(db, nguoi_xem_het, "NHG9999")
    assert r["delivery_invoice_date"] == ""
    assert r["document_delivery_date"] == ""


def test_both_dates_are_sortable_and_filterable():
    """Khai một cột không có thật thì `hasattr` dưới đây đỏ ngay — bẫy của bao-CR-404.

    `_cond_map()` lấy thẳng `_sort_map()`, nên khai ở một chỗ là mở cả sắp xếp lẫn
    bộ lọc điều kiện; kiểm luôn để sau này ai rút một trong hai thì biết.
    """
    smap = pp._sort_map()
    for key, model in (("document_delivery_date", POItem),
                       ("delivery_invoice_date", PODelivery)):
        col = smap[key]
        assert col.class_ is model
        assert hasattr(col.class_, col.key)
    cond = pp._cond_map(True)
    assert "document_delivery_date" in cond and "delivery_invoice_date" in cond


def test_sort_by_invoice_date_runs_against_real_column(db, nguoi_xem_het, don_162):
    """Chạy thật một lượt sắp xếp — cột ảo thì nổ ở đây chứ không nổ trên màn người dùng."""
    prof = get_perm_profile(db, nguoi_xem_het)
    q = pp._build_query(req("sort_by=delivery_invoice_date&sort_dir=desc"), db,
                        nguoi_xem_het, prof, True, True)
    assert [po.code for po, _it, _dl in q.all()] == ["PO00162"]


def test_both_columns_reach_the_two_excel_files():
    """Đại ca đã duyệt cho file xuất màn ĐMH mọc thêm hai cột này (dùng chung `COLS`)."""
    tien_do = {c.key: c.label for c in ex.columns_for(True)}
    assert tien_do["document_delivery_date"] == "Ngày giao chứng từ KT"
    # Màn Tiến độ chỉ có MỘT nguồn hóa đơn nên nhãn rút gọn, y như cột "Số HĐ" (PROGRESS_RENAME)
    assert tien_do["delivery_invoice_date"] == "Ngày HĐ"

    don_mua_hang = {c.key: c.label for c in po_ex.line_columns(True)}
    assert don_mua_hang["document_delivery_date"] == "Ngày giao chứng từ KT"
    # Bên ĐMH giữ chú "(giao)" vì ở đó còn cột số HĐ của dòng hàng, không chú thì đọc ra hai nghĩa
    assert don_mua_hang["delivery_invoice_date"] == "Ngày HĐ (giao)"


def test_hidden_supplier_does_not_drop_the_new_dates(db, nguoi_xem_het, don_162):
    """Hai ngày này KHÔNG phải dữ liệu nhà cung cấp — người thiếu `supplier.read` vẫn phải thấy."""
    po, it = don_162
    dl = db.query(PODelivery).filter(PODelivery.po_item_id == it.id).one()
    r = pp._row(po, it, dl, False)
    assert r["document_delivery_date"] == "2026-09-14"
    assert r["delivery_invoice_date"] == "2026-09-14"
    assert "supplier_name" not in r
