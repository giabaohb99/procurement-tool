"""CR-080 — bộ lọc điều kiện cho hai màn Tiến độ (mua hàng · báo giá).

Hai màn này là JOIN nhiều bảng nên whitelist không thể là "model + danh sách tên cột" như các
màn CRUD; nó là MAP {tên field trên URL: cột thật}. Ba thứ được kiểm ở đây:

1. `apply_operator_filters_map` — lọc đúng trên query join, có bí danh (`delivery_invoice_no` ->
   `PODelivery.invoice_no`), field ngoài map thì bỏ qua.
2. `_cond_map` của hai controller — không ai lọc được cột NCC/vận chuyển khi thiếu `supplier.read`
   (cột đã che trên bảng thì lọc theo cũng là đường rò), và luôn phủ đủ cột sort được.
3. Ô lọc cố định còn lại phải là cột TÍNH — thứ bộ lọc điều kiện KHÔNG làm được (bảo hiểm cho
   quyết định gỡ bớt ô lọc trên hai màn).
"""
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.core.filter_operators import apply_operator_filters_map
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_progress import controller as pp
from app.modules.survey_progress import controller as sp


def req(qs: str):
    """Request giả — chỉ .query_params được dùng."""
    return SimpleNamespace(query_params=QueryParams(qs))


# ── 1. Lọc trên query JOIN ba bảng ──────────────────────────────────────────────
@pytest.fixture
def progress_rows(db):
    """3 dòng ĐMH: khác NCC, khác SL đặt, khác số hóa đơn ở lần giao."""
    data = [
        ("PO001", "NCC01", 10, "HD-001"),
        ("PO002", "NCC02", 50, "HD-002"),
        ("PO003", "NCC01", 100, ""),
    ]
    for code, ncc, qty, inv in data:
        po = PurchaseOrder(code=code, status="approved", supplier_code=ncc,
                           supplier_name=f"Công ty {ncc}", order_date="2026-08-01")
        db.add(po); db.flush()
        it = POItem(po_id=po.id, product_code="SP1", qty_order=qty, price=1000)
        db.add(it); db.flush()
        db.add(PODelivery(po_id=po.id, po_item_id=it.id, delivery_no=1, invoice_no=inv))
    db.commit()


def _codes(db, qs: str, colmap: dict) -> set[str]:
    q = (db.query(PurchaseOrder, POItem, PODelivery)
         .join(POItem, POItem.po_id == PurchaseOrder.id)
         .outerjoin(PODelivery, PODelivery.po_item_id == POItem.id))
    return {po.code for po, _it, _dl in apply_operator_filters_map(q, colmap, req(qs)).all()}


def test_loc_duoc_cot_cua_bang_con_tren_query_join(db, progress_rows):
    m = pp._cond_map(True)
    assert _codes(db, "qty_order__gte=50", m) == {"PO002", "PO003"}
    assert _codes(db, "supplier_code__eq=NCC01", m) == {"PO001", "PO003"}


def test_bi_danh_tro_dung_cot_that(db, progress_rows):
    """`delivery_invoice_no` trên URL = `PODelivery.invoice_no` — đổi tên vì `invoice_no` của
    dòng hàng đã chiếm key đó."""
    m = pp._cond_map(True)
    assert _codes(db, "delivery_invoice_no__contains=HD-00", m) == {"PO001", "PO002"}
    assert _codes(db, "delivery_invoice_no__isnull=true", m) == {"PO003"}


def test_field_ngoai_map_bi_bo_qua_khong_vo_trang(db, progress_rows):
    m = pp._cond_map(True)
    assert _codes(db, "khong_ton_tai__eq=x", m) == {"PO001", "PO002", "PO003"}
    # Operator lạ cũng vậy — người dùng sửa tay URL thì coi như không lọc
    assert _codes(db, "qty_order__khonghop=5", m) == {"PO001", "PO002", "PO003"}


def test_nhieu_dieu_kien_mac_dinh_la_va(db, progress_rows):
    m = pp._cond_map(True)
    assert _codes(db, "supplier_code__eq=NCC01&qty_order__gte=50", m) == {"PO003"}
    assert _codes(db, "supplier_code__eq=NCC02&qty_order__gte=50&conjunction=or",
                  m) == {"PO002", "PO003"}


def test_khong_co_supplier_read_thi_khong_loc_duoc_theo_ncc(db, progress_rows):
    """Cột NCC bị che trên bảng thì lọc theo cũng phải vô hiệu — nếu không, lọc rồi đếm số dòng
    còn lại là mò ra được nhà cung cấp của đơn."""
    assert _codes(db, "supplier_code__eq=NCC01", pp._cond_map(False)) == {"PO001", "PO002", "PO003"}


# ── 2. Whitelist của hai màn ────────────────────────────────────────────────────
def test_cond_map_tien_do_mua_hang_che_dung_cum_ncc():
    full, limited = pp._cond_map(True), pp._cond_map(False)
    for k in pp._SUPPLIER_HIDDEN:
        assert k not in limited
    assert set(pp._SUPPLIER_HIDDEN) & set(full) == {
        "supplier_code", "supplier_name", "carrier_code", "carrier_name",
        "shipping_unit_price", "shipping_amount"}
    # Cột nào sort được tại server thì cũng lọc được (trừ company_id — đã có ô Công ty riêng)
    assert set(pp._sort_map()) - set(full) == {"company_id"}


def test_cond_map_tien_do_bao_gia_che_ma_dong_noi_bo_va_co_bi_danh_assignee():
    full, limited = sp._cond_map(True), sp._cond_map(False)
    assert "internal_line_code" in full and "internal_line_code" not in limited
    # `assignee` là bí danh dễ đọc của cùng cột với `assignee_name` (giá trị = MÃ nhân sự)
    assert full["assignee"] is full["assignee_name"]
    assert set(sp._sort_map()) - set(full) == {"company_id"}


# ── 3. Ô lọc cố định giữ lại phải là cột TÍNH ──────────────────────────────────
def test_o_loc_co_dinh_giu_lai_khong_the_thay_bang_bo_loc_dieu_kien():
    """`recv_state` (tổng SL nhận mọi lần giao), `state` (Tiến độ dòng) và `late` là cột TÍNH —
    không có cột DB tương ứng nên bộ lọc điều kiện không làm được, phải ở lại thanh lọc."""
    for k in ("recv_state", "received_qty_sum"):
        assert k not in pp._cond_map(True)
    for k in ("state", "progress_state", "days_late", "handling_days", "option_count"):
        assert k not in sp._cond_map(True)
