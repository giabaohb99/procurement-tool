"""bao-CR-568 — YCMH sinh từ YCBG có thể chưa có mã VTBB: chốt xử lý vẫn được, nhưng tạo đơn thì
dòng phải có mã, và nhân sự thu mua (hoặc quản lý) gắn / đổi mã được SAU điều phối.

Đại ca chốt 02/10/2026: «làm logic như ở YCBG, chốt được không có mã VTBB luôn, nhưng muốn mua
hàng thì trên option đó phải có mã … nhân sự thu mua có thể đổi mã trên đó».
"""
import pytest
from fastapi import HTTPException

from app.modules.product.model import Product
from app.modules.purchase_request import controller as C
from app.modules.purchase_request import option_service as OS
from app.modules.purchase_request import service as SV
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import ItemStatusIn, ItemStatusItem
from app.modules.user.model import User


@pytest.fixture(autouse=True)
def _options_on(monkeypatch):
    monkeypatch.setattr(OS, "options_enabled", lambda: True)


def _pr(db, seed, code="", status="dispatched"):
    pr = PurchaseRequest(code="PYC-CR568", company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test", department_id=seed.dept_id,
                         status=status, request_date="2026-10-02",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    it = PurchaseRequestItem(pr_id=pr.id, product_code=code, product_name="Nhãn từ YCBG", item_group="Nhãn",
                             qty=10, unit="cuộn", price=1000, vat_pct=8, amount=10800,
                             assignee=seed.emp_nstm_code, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(it)
    db.commit()
    return pr, it


def _product(db, code="SP-CR568"):
    db.add(Product(code=code, name="Nhãn CR568", item_group="Nhãn", unit="cuộn", is_active=True,
                   created_by=0, updated_by=0))
    db.commit()
    return code


def _nstm(db, seed, cap_quyen):
    cap_quyen(seed.u_nstm_id, "purchase_request", scope="assigned", read=True, write=True)
    cap_quyen(seed.u_nstm_id, "supplier", scope="all", read=True)
    return db.get(User, seed.u_nstm_id)


def _set_code(db, pr, it, user, code):
    return C.update_item_status(pr.id, ItemStatusIn(items=[ItemStatusItem(id=it.id, product_code=code)]),
                                db=db, user=user)


def test_nstm_assigns_code_after_dispatch(db, seed, cap_quyen):
    pr, it = _pr(db, seed)
    code = _product(db)
    _set_code(db, pr, it, _nstm(db, seed, cap_quyen), code)
    db.refresh(it)
    assert it.product_code == code


def test_unknown_or_inactive_code_is_rejected(db, seed, cap_quyen):
    pr, it = _pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    with pytest.raises(HTTPException) as e:
        _set_code(db, pr, it, user, "KHONG-CO")
    assert e.value.status_code == 400 and "danh mục" in e.value.detail
    db.add(Product(code="SP-NGUNG", name="x", is_active=False, created_by=0, updated_by=0))
    db.commit()
    with pytest.raises(HTTPException) as e:
        _set_code(db, pr, it, user, "SP-NGUNG")
    assert "ngừng dùng" in e.value.detail


def test_code_locked_once_line_is_on_an_order(db, seed, cap_quyen):
    pr, it = _pr(db, seed, code="SP-A")
    it.line_status = SV.LINE_STATUS_NOT_ORDERED
    db.commit()
    code = _product(db)
    with pytest.raises(HTTPException) as e:
        _set_code(db, pr, it, _nstm(db, seed, cap_quyen), code)
    assert "đã lên đơn" in e.value.detail


def test_duplicate_code_on_same_request_is_rejected(db, seed, cap_quyen):
    pr, it = _pr(db, seed)
    code = _product(db)
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code=code, product_name="Dòng khác", item_group="Nhãn",
                               qty=1, unit="cuộn", price=1, amount=1, assignee=seed.emp_nstm_code,
                               created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    with pytest.raises(HTTPException) as e:
        _set_code(db, pr, it, _nstm(db, seed, cap_quyen), code)
    assert e.value.status_code == 400


def test_other_persons_line_is_silently_skipped(db, seed):
    """Luật cũ của `update_item_status`: NSTM không phải quản lý thì chỉ đụng dòng của mình —
    dòng người khác bị bỏ qua im lặng (phạm vi `assigned` ở tầng controller còn chặn sớm hơn,
    nên gọi thẳng service để kiểm đúng nhánh này)."""
    pr, it = _pr(db, seed)
    it.assignee = seed.emp_backup_code
    db.commit()
    code = _product(db)
    SV.update_item_status(db, pr.id, ItemStatusIn(items=[ItemStatusItem(id=it.id, product_code=code)]),
                          seed.u_nstm_id, emp_code=seed.emp_nstm_code, is_manager=False)
    db.refresh(it)
    assert it.product_code == ""


def test_generate_orders_skips_lines_without_code(db, seed, cap_quyen):
    pr, it = _pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    C._out(db, pr, user)          # sinh phương án 0, tick chọn sẵn
    with pytest.raises(HTTPException) as e:
        C.generate_orders_from_options(pr.id, db=db, user=user)
    assert "chưa có mã VTBB" in e.value.detail
    _set_code(db, pr, it, user, _product(db))
    out = C.generate_orders_from_options(pr.id, db=db, user=user)
    import json
    data = json.loads(out.body)["data"]
    assert len(data["orders"]) == 1 and data["skipped"]["no_code"] == 0
