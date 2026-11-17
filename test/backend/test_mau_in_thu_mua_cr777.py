"""duoc-CR-777 — dữ liệu "Mẫu thu mua" của màn In YCMH từ ĐMH (`GET /api/purchase-orders/{pid}/purchasing-print`).

Chốt của anh Được (17/11/2026):
1. Người đề xuất = người ĐANG ĐĂNG NHẬP, kèm chữ ký tài khoản của chính họ.
2. Trưởng phòng ban / bộ phận = QUẢN LÝ TRỰC TIẾP của người đó, kèm chữ ký; chưa gán thì để trống.
3. NCC và bảng hàng theo ĐMH (SL đặt, đơn giá, VAT), bỏ dòng đã Hủy; NCC che khi thiếu `supplier.read`.
4. Chỉ người ĐỌC được đúng đơn đó mới lấy được dữ liệu: thiếu quyền đọc -> 403, ngoài phạm vi -> 404.
"""
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.auth import perm_cache_clear
from app.modules.employee.model import Employee
from app.modules.purchase_order.controller import get_po_purchasing_print
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.user.model import User


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


@pytest.fixture
def w(db, seed, cap_quyen):
    manager = Employee(code="NSU777M", full_name="Trần Quản Lý", position="Trưởng phòng", company_id=seed.company_id,
                       is_active=True)
    db.add(manager)
    db.flush()
    buyer_emp = Employee(code="NSU777B", full_name="Lê Thu Mua", position="Nhân viên thu mua",
                         company_id=seed.company_id, manager_id=manager.id, is_active=True)
    db.add(buyer_emp)
    db.flush()
    buyer = db.get(User, seed.u_nstm_id)
    buyer.employee_id = buyer_emp.id
    buyer.signature = "/files/sig-buyer.png"
    manager_user = User(email="cr777-manager@test.local", employee_id=manager.id, is_active=True,
                        signature="/files/sig-manager.png")
    db.add(manager_user)
    cap_quyen(buyer.id, "purchase_order", scope="all", read=True, print=True)

    po = PurchaseOrder(code="PO0777", status="approved", company_id=seed.company_id, supplier_code="NCC77",
                       supplier_name="NCC Bảy Bảy", order_date="2026-11-17", currency="VND", pr_code="PR-777")
    db.add(po)
    db.flush()
    db.add_all([
        POItem(po_id=po.id, product_code="TH01", product_name="Thùng 5L", unit="Thùng", qty_order=80, price=9500,
               vat=8, progress_status="ordered"),
        POItem(po_id=po.id, product_code="TH02", product_name="Nắp", unit="Cái", qty_order=10, price=1000, vat=0,
               progress_status="cancelled"),
    ])
    db.commit()
    return SimpleNamespace(db=db, seed=seed, buyer=buyer, po=po, manager=manager, cap_quyen=cap_quyen)


def _data(w, user):
    resp = get_po_purchasing_print(w.po.id, w.db, user)
    return json.loads(resp.body)["data"]


def test_proposer_is_logged_in_user_and_head_is_direct_manager(w):
    data = _data(w, w.buyer)
    assert data["proposer"]["name"] == "Lê Thu Mua"
    assert data["proposer"]["signature"] == "/files/sig-buyer.png"
    assert data["manager"]["name"] == "Trần Quản Lý"
    assert data["manager"]["position"] == "Trưởng phòng"
    assert data["manager"]["signature"] == "/files/sig-manager.png"


def test_lines_follow_the_purchase_order_and_skip_cancelled(w):
    data = _data(w, w.buyer)
    assert [(i["product_code"], i["qty"], i["price"], i["vat"], i["amount"]) for i in data["items"]] == [
        ("TH01", 80.0, 9500.0, 8.0, 820800.0)]
    assert (data["subtotal"], data["vat"], data["total"]) == (760000.0, 60800.0, 820800.0)


def test_supplier_comes_from_the_order_and_is_hidden_without_supplier_read(w):
    hidden = _data(w, w.buyer)
    assert hidden["supplier"] == {"code": "", "name": ""} and hidden["supplier_hidden"] is True

    w.cap_quyen(w.buyer.id, "supplier", scope="all", read=True)
    perm_cache_clear()
    shown = _data(w, w.buyer)
    assert shown["supplier"] == {"code": "NCC77", "name": "NCC Bảy Bảy"} and shown["supplier_hidden"] is False


def test_no_direct_manager_leaves_the_head_blank(w):
    emp = w.db.get(Employee, w.buyer.employee_id)
    emp.manager_id = 0
    w.db.commit()
    data = _data(w, w.buyer)
    assert data["manager"] == {"employee_id": 0, "name": "", "signature": "", "position": ""}


def test_order_outside_read_scope_is_404(w, seed):
    """Người chỉ đọc được đơn CỦA MÌNH không lấy được dữ liệu đơn người khác (cùng 404 với đơn không tồn tại)."""
    outsider = w.db.get(User, seed.u_req_id)
    w.cap_quyen(outsider.id, "purchase_order", scope="own", read=True, print=True)
    perm_cache_clear()
    with pytest.raises(HTTPException) as err:
        get_po_purchasing_print(w.po.id, w.db, outsider)
    assert err.value.status_code == 404


def test_print_only_without_read_is_blocked_by_the_route_guard(w, seed):
    """Cổng route là quyền ĐỌC đơn mua hàng: người chỉ có quyền In (không Đọc) bị chặn 403 — không thấy mẫu."""
    import inspect

    from app.core.auth import require
    from app.modules.purchase_order import controller

    source = inspect.getsource(controller.get_po_purchasing_print)
    assert 'require("purchase_order", "read")' in source
    printer = w.db.get(User, seed.u_req_id)
    w.cap_quyen(printer.id, "purchase_order", scope="all", print=True)
    perm_cache_clear()
    with pytest.raises(HTTPException) as err:
        require("purchase_order", "read")(user=printer, db=w.db)
    assert err.value.status_code == 403
