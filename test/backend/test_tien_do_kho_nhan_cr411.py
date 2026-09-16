"""bao-CR-411 — cột Kho của màn Tiến độ mua hàng phải hiện cả khi CHƯA nhận hàng (ticket prod 50).

Cảnh cũ: ô Kho chỉ lấy kho của LẦN GIAO, mà lần giao chỉ sinh ra lúc đi nhận hàng. Đơn chưa
nhận thì ô trống trơn — đúng lúc người theo đơn cần biết hàng sẽ về đâu để đi kiểm thì không
có gì để đọc. Đo trên dữ liệu thật: 240/240 dòng hàng đều đã khai «Kho nhận mặc định»
(`POItem.warehouse_code`), nhưng 78 hàng chưa có lần giao nào.

Chốt của đại ca: GỘP CHUNG vào cột «Kho» sẵn có, giữ nguyên MÃ kho (không đổi sang tên).

Bốn chốt ở đây:

1. Có lần giao và lần giao đã chọn kho -> giữ kho của lần giao (không được để kho mặc định
   của dòng đè lên kho thực nhận).
2. Chưa có lần giao, hoặc có mà bỏ trống ô kho -> lùi về kho mặc định của dòng hàng.
3. Trống cả hai phía -> chuỗi rỗng, KHÔNG phải None.
4. Sắp xếp + lọc điều kiện chạy trên CÙNG biểu thức lùi đó. Trỏ thẳng vào cột của lần giao
   thì hàng lùi bày ra mã kho nhưng lọc theo chính mã ấy lại không ra nó — lệch âm thầm.
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
    user = User(email="ct411@test.local", employee_id=0, is_active=True)
    db.add(user)
    db.flush()
    cap_quyen(user.id, "purchase_order", scope="all", read=True)
    db.commit()
    return user


def _them_dong(db, code: str, kho_dong: str, kho_giao: str | None):
    """Một đơn một dòng. `kho_giao=None` nghĩa là CHƯA phát sinh lần giao nào."""
    po = PurchaseOrder(code=code, status="approved", order_date="2026-09-15")
    db.add(po)
    db.flush()
    it = POItem(po_id=po.id, product_code=f"SP-{code}", qty_order=10, price=1000,
                warehouse_code=kho_dong)
    db.add(it)
    db.flush()
    if kho_giao is not None:
        db.add(PODelivery(po_id=po.id, po_item_id=it.id, delivery_no=1,
                          warehouse_code=kho_giao, received_qty=0))
    db.commit()
    return po, it


def _hang(db, user, qs: str = "") -> list[dict]:
    prof = get_perm_profile(db, user)
    q = pp._build_query(req(qs), db, user, prof, True, True)
    return [pp._row(po, it, dl, True) for po, it, dl in q.all()]


def test_delivery_warehouse_wins_when_the_goods_were_actually_received(db, nguoi_xem_het):
    """Hàng đã về kho B thì bảng phải nói kho B, dù dòng hàng đặt mặc định kho A.

    Kho mặc định là DỰ ĐỊNH, kho của lần giao là SỰ THẬT — lấy nhầm thứ tự thì người đi kiểm
    hàng đến đúng cái kho không có hàng.
    """
    _them_dong(db, "PO00170", kho_dong="Kho B18", kho_giao="Kho C1-2")
    (r,) = _hang(db, nguoi_xem_het, "q=SP-PO00170")
    assert r["warehouse_code"] == "Kho C1-2"


def test_line_without_any_delivery_falls_back_to_the_line_default(db, nguoi_xem_het):
    """Đúng 78 hàng của prod: chưa nhận gì, trước CR này ô Kho trống trơn."""
    _them_dong(db, "PO00171", kho_dong="Kho B18", kho_giao=None)
    (r,) = _hang(db, nguoi_xem_het, "q=SP-PO00171")
    assert r["warehouse_code"] == "Kho B18"


def test_delivery_with_a_blank_warehouse_also_falls_back(db, nguoi_xem_het):
    """Lần giao đã mở nhưng chưa ai chọn kho — vẫn phải lùi, đừng chỉ xét `dl is None`."""
    _them_dong(db, "PO00172", kho_dong="Kho Lab Dego", kho_giao="")
    (r,) = _hang(db, nguoi_xem_het, "q=SP-PO00172")
    assert r["warehouse_code"] == "Kho Lab Dego"


def test_blank_on_both_sides_gives_an_empty_string_not_none(db, nguoi_xem_het):
    """Ô rỗng phải là chuỗi rỗng: None rơi xuống Excel thành chữ "None" trong ô."""
    _them_dong(db, "PO00173", kho_dong="", kho_giao=None)
    (r,) = _hang(db, nguoi_xem_het, "q=SP-PO00173")
    assert r["warehouse_code"] == ""


def test_filtering_by_warehouse_finds_the_rows_that_fell_back(db, nguoi_xem_het):
    """Chốt chống lệch: lọc theo đúng mã đang BÀY ra màn hình phải ra đúng hàng đó.

    Nếu `_cond_map()` còn trỏ thẳng `PODelivery.warehouse_code` thì hàng chưa giao hiện
    "Kho B18" nhưng lọc `warehouse_code__eq=Kho B18` trả về rỗng — không có lỗi nào đỏ lên,
    người dùng chỉ kết luận là dữ liệu bị mất.
    """
    _them_dong(db, "PO00174", kho_dong="Kho B18", kho_giao=None)
    _them_dong(db, "PO00175", kho_dong="Kho B18", kho_giao="Kho C1-2")

    rows = _hang(db, nguoi_xem_het, "warehouse_code__eq=Kho B18")
    assert [r["po_code"] for r in rows] == ["PO00174"]

    rows = _hang(db, nguoi_xem_het, "warehouse_code__contains=C1-2")
    assert [r["po_code"] for r in rows] == ["PO00175"]


def test_sort_by_warehouse_runs_against_a_real_expression(db, nguoi_xem_het):
    """Chạy thật một lượt sắp xếp — biểu thức sai thì nổ ở đây chứ không nổ trên màn hình."""
    _them_dong(db, "PO00176", kho_dong="Kho B18", kho_giao=None)
    _them_dong(db, "PO00177", kho_dong="Kho B18", kho_giao="An Nông")
    prof = get_perm_profile(db, nguoi_xem_het)
    q = pp._build_query(req("sort_by=warehouse_code&sort_dir=asc"), db,
                        nguoi_xem_het, prof, True, True)
    assert [po.code for po, _it, _dl in q.all()] == ["PO00177", "PO00176"]


def test_the_warehouse_column_still_ships_in_both_excel_files():
    """`row_values` dùng chung cho cả file xuất màn ĐMH, nên nhánh lùi chảy sang đó luôn."""
    assert {c.key: c.label for c in ex.columns_for(True)}["warehouse_code"] == "Kho"
    assert "warehouse_code" in {c.key for c in po_ex.line_columns(True)}


def test_hidden_supplier_does_not_drop_the_warehouse(db, nguoi_xem_het):
    """Kho nhận là kho CỦA MÌNH, không phải dữ liệu nhà cung cấp — ai cũng được thấy."""
    po, it = _them_dong(db, "PO00178", kho_dong="Kho B18", kho_giao=None)
    r = pp._row(po, it, None, False)
    assert r["warehouse_code"] == "Kho B18"
    assert "supplier_name" not in r
