"""duoc-CR-744 — màn Tiến độ mua hàng: mọi cột đều sắp xếp được tại server.

Lỗi người dùng báo: bảng không bật cột nào sắp xếp được, dù `_sort_map()` đã nhận gần đủ khóa.
Bật lên rồi thì lộ thêm bốn cột xếp sai nếu đi thẳng theo cột lưu:

1. Hai cột thành tiền là cột TÍNH (SL × đơn giá × (1+VAT) × tỷ giá) — không nằm trong DB.
2. Công ty bày TÊN mà cột lưu id.
3. Tiến độ / Hồ sơ CT bày NHÃN mà cột lưu MÃ — xếp theo chữ cái của mã là lộn dòng đời.
4. Không có `supplier.read` thì xếp theo cột NCC bị bỏ qua (thứ tự đủ để mò ra NCC).

Bài canh cuối: mọi cột của bảng (trừ STT) đều có cách xếp.
"""
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.core.auth import get_perm_profile
from app.modules.company.model import Company
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_progress import controller as pp
from app.modules.purchase_progress import export as ex
from app.modules.purchase_progress.sort_expressions import get_computed_sort_expression
from app.modules.user.model import User

#  Khóa cột trên bảng của màn (frontend-v2 `purchase-progress-page.tsx`) — bài canh dò từng khóa.
SCREEN_KEYS = [
    "po_code", "misa_code", "pr_code", "company", "department", "supplier_name", "nspt",
    "order_date", "product_code", "product_name", "item_group", "unit", "qty_order", "price",
    "currency", "exchange_rate", "order_amount", "progress_status", "delivery_no",
    "warehouse_code", "carrier_name", "received_qty", "received_date", "delivery_invoice_date",
    "diff_regulated", "amount", "document_delivery_date", "document_status",
]


def req(qs: str):
    """Request giả — `_build_query` chỉ đụng tới `.query_params`."""
    return SimpleNamespace(query_params=QueryParams(qs))


@pytest.fixture
def viewer(db, cap_quyen):
    user = User(email="sort743pp@test.local", employee_id=0, is_active=True)
    db.add(user)
    db.flush()
    cap_quyen(user.id, "purchase_order", scope="all", read=True)
    db.commit()
    return user


def _add(db, code: str, *, company_id=1, qty=1, price=0, vat=0, rate=0, received=None,
         progress="", document="none", supplier_name="", supplier_code=""):
    po = PurchaseOrder(code=code, status="approved", company_id=company_id,
                       document_status=document, supplier_name=supplier_name,
                       supplier_code=supplier_code, order_date="2026-10-01")
    db.add(po)
    db.flush()
    it = POItem(po_id=po.id, product_code="SP1", qty_order=qty, price=price, vat=vat,
                exchange_rate=rate, progress_status=progress)
    db.add(it)
    db.flush()
    if received is not None:
        db.add(PODelivery(po_id=po.id, po_item_id=it.id, delivery_no=1, received_qty=received))
    db.flush()


def _rows(db, user, qs: str, show_supplier: bool = True) -> list[dict]:
    prof = get_perm_profile(db, user)
    q = pp._build_query(req(qs), db, user, prof, True, show_supplier)
    return [ex.row_values(po, it, dl, show_supplier) for po, it, dl in q.all()]


def _codes(db, user, qs: str, show_supplier: bool = True) -> list[str]:
    return [r["po_code"] for r in _rows(db, user, qs, show_supplier)]


def test_thanh_tien_dh_xep_theo_so_da_quy_doi_va_cong_vat(db, viewer):
    # 10 × 100 = 1.000 nhưng nhân tỷ giá 25.000 thì thành lớn nhất; VAT 10% đẩy B vượt C.
    _add(db, "A-USD", qty=10, price=100, rate=25000)          # 25.000.000
    _add(db, "B-VAT", qty=1, price=1_000_000, vat=10)          # 1.100.000
    _add(db, "C-PLAIN", qty=1, price=1_050_000)                # 1.050.000, tỷ giá 0 đọc thành 1
    db.commit()

    rows = _rows(db, viewer, "sort_by=order_amount&sort_dir=desc")
    assert [r["po_code"] for r in rows] == ["A-USD", "B-VAT", "C-PLAIN"]
    amounts = [r["order_amount"] for r in rows]
    assert amounts == sorted(amounts, reverse=True)


def test_thanh_tien_nhan_hang_chua_giao_tinh_la_0(db, viewer):
    _add(db, "A-NONE", qty=5, price=1000)                      # chưa có lần giao
    _add(db, "B-SOME", qty=5, price=1000, received=2)
    _add(db, "C-ALL", qty=5, price=1000, received=5)
    db.commit()

    rows = _rows(db, viewer, "sort_by=amount&sort_dir=asc")
    assert [r["po_code"] for r in rows] == ["A-NONE", "B-SOME", "C-ALL"]


def test_tien_do_xep_theo_dong_doi_khong_theo_chu_cai_cua_ma(db, viewer):
    #  Theo chữ cái của MÃ: completed < doc_pending < doc_sent < not_ordered < ordered < received.
    for code, progress in (("A", "completed"), ("B", "doc_sent"), ("C", "received"),
                           ("D", ""), ("E", "cancelled"), ("F", "ordered")):
        _add(db, code, progress=progress)
    db.commit()

    asc = _codes(db, viewer, "sort_by=progress_status&sort_dir=asc")
    #  Ô trống hiện là "Chưa đặt hàng" nên đứng đầu; Hủy đơn (ngoại lệ) đứng sau Hoàn thành.
    assert asc == ["D", "F", "C", "B", "A", "E"]


def test_ho_so_ct_xep_theo_thu_tu_bo_ma(db, viewer):
    _add(db, "A-FULL", document="full")
    _add(db, "B-NONE", document="none")
    _add(db, "C-PART", document="partial")
    db.commit()
    assert _codes(db, viewer, "sort_by=document_status&sort_dir=asc") == ["B-NONE", "C-PART", "A-FULL"]


def test_cong_ty_xep_theo_ten(db, viewer):
    db.add_all([Company(id=1, code="ZZ", name="Zeta Holding"),
                Company(id=2, code="AA", name="Alpha Farm")])
    db.flush()
    _add(db, "A-ZETA", company_id=1)
    _add(db, "B-ALPHA", company_id=2)
    db.commit()
    assert _codes(db, viewer, "sort_by=company&sort_dir=asc") == ["B-ALPHA", "A-ZETA"]


def test_ncc_xep_theo_chu_dang_hien_va_bi_bo_qua_khi_khong_co_quyen(db, viewer):
    _add(db, "A", supplier_name="Gamma")
    _add(db, "B", supplier_name="", supplier_code="BETA-CODE")   # ô hiện mã NCC
    _add(db, "C", supplier_name="Alpha")
    db.commit()

    assert _codes(db, viewer, "sort_by=supplier_name&sort_dir=asc") == ["C", "B", "A"]
    default = _codes(db, viewer, "", show_supplier=False)
    assert _codes(db, viewer, "sort_by=supplier_name&sort_dir=desc", show_supplier=False) == default
    assert _codes(db, viewer, "sort_by=carrier_name&sort_dir=desc", show_supplier=False) == default


def test_moi_cot_cua_bang_deu_xep_duoc():
    """Thêm cột mới lên bảng mà quên khai cách xếp thì lại có cột bấm không ăn — đúng lỗi này."""
    smap = pp._sort_map()
    missing = [k for k in SCREEN_KEYS
               if k not in smap and get_computed_sort_expression(k) is None]
    assert missing == []
