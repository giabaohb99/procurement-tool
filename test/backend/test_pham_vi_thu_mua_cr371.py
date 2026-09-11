"""bao-CR-371 — phạm vi "Thu mua (được giao + đã duyệt)" phải theo phiếu tới HẾT vòng đời.

Lỗi gặp trên prod: tài khoản Admin thu mua đặt phạm vi `proc` ở Yêu cầu mua hàng, mở phiếu
PYC08092605 (trạng thái `purchased`) thì nhận "Không tìm thấy phiếu ... hoặc bạn không có
quyền truy cập". Nguyên nhân: `_role_scope_cond` chỉ nhận hai trạng thái `approved` và
`dispatched`, nên phiếu vừa chạy sang `processing` là rơi khỏi phạm vi — trừ khi người đó
tình cờ là người tạo / người yêu cầu / người được gán.

Ca test dựng một người thu mua KHÔNG dính gì tới phiếu (không tạo, không yêu cầu, không
được gán, không có dòng nào mang mã mình) để chỉ còn đúng nhánh trạng thái quyết định.
"""
import pytest

from app.core.auth import get_perm_profile, perm_cache_clear
from app.core.scoping import apply_scope
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


def _proc_user(db, seed, entity: str):
    """Một người thu mua có quyền đọc `entity` với phạm vi `proc`, không dính phiếu nào."""
    from app.modules.employee.model import Employee
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import User, UserRole
    emp = Employee(code="PROC371", full_name="Admin Thu Mua", company_id=seed.company_id,
                   department_id=seed.dept_id, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email="PROC371", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    role = Role(code=f"RPROC371{entity[:4]}", name="Admin thu mua")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity=entity, scope="proc", can_read=True))
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    perm_cache_clear()
    return user


def _visible_pr_statuses(db, seed, user, statuses):
    """Trong các trạng thái đưa vào, người này thấy được những trạng thái nào."""
    for i, st in enumerate(statuses):
        db.add(PurchaseRequest(code=f"PYC371{i:02d}", company_id=seed.company_id,
                               department="Phòng Test", status=st,
                               requester_id=seed.emp_req_id,
                               created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.flush()
    profile = get_perm_profile(db, user)
    rows = apply_scope(db.query(PurchaseRequest), PurchaseRequest,
                       "purchase_request", user, profile).all()
    return {r.status for r in rows}


ALL_PR_STATUSES = ["draft", "submitted", "approved", "dispatched", "processing",
                   "purchasing", "purchased", "completed", "rejected", "cancelled"]


def test_proc_scope_sees_purchase_request_through_whole_lifecycle(db, seed):
    user = _proc_user(db, seed, "purchase_request")
    seen = _visible_pr_statuses(db, seed, user, ALL_PR_STATUSES)
    assert seen == {"approved", "dispatched", "processing", "purchasing", "purchased", "completed"}


def test_proc_scope_still_hides_purchase_request_before_approval(db, seed):
    """Nới phạm vi KHÔNG được nới sang phiếu chưa duyệt — nháp/chờ duyệt là việc của bộ phận."""
    user = _proc_user(db, seed, "purchase_request")
    seen = _visible_pr_statuses(db, seed, user, ["draft", "submitted", "rejected"])
    assert seen == set()


def test_proc_scope_sees_purchase_order_after_goods_received(db, seed):
    """Cùng lỗi ở Đơn mua hàng: nhận hàng xong (`partial`/`received`) đơn không được biến mất."""
    user = _proc_user(db, seed, "purchase_order")
    for i, st in enumerate(["draft", "submitted", "approved", "partial", "received", "completed"]):
        db.add(PurchaseOrder(code=f"DMH371{i:02d}", company_id=seed.company_id,
                             department="Phòng Test", status=st,
                             created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.flush()
    profile = get_perm_profile(db, user)
    rows = apply_scope(db.query(PurchaseOrder), PurchaseOrder,
                       "purchase_order", user, profile).all()
    assert {r.status for r in rows} == {"approved", "partial", "received", "completed"}
