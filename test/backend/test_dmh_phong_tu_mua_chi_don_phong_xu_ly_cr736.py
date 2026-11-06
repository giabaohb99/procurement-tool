"""bao-CR-736 — người mua của phòng tự mua (bậc `dept_proc`) chỉ thấy ĐMH do chính phòng mình XỬ LÝ.

Ca thật 06/11/2026: NSU012 (Dego Organic, hai vai trò ĐMH bậc `dept_proc`) thấy PO00890 — YCMH của
Dego Organic nhưng phòng SX - Thu mua xử lý, người khác là NSPT. Người chủ chốt: đơn đó KHÔNG được
hiện; chỉ hiện đơn phòng mình xử lý, đơn mình lập, đơn mình là NSPT. Không mở thêm vế người yêu cầu.
"""
import pytest

from app.core.auth import get_perm_profile, perm_cache_clear
from app.core.scoping import apply_scope
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


@pytest.fixture
def depts(db, seed):
    factory = Department(code="NM736", name="Nhà máy", company_id=seed.company_id, is_active=True)
    purchasing = Department(code="TM736", name="Thu mua", company_id=seed.company_id, is_active=True)
    db.add_all([factory, purchasing])
    db.flush()
    return factory.id, purchasing.id


def _buyer(db, seed, dept_id: int, scope: str = "dept_proc", code: str = "B736"):
    emp = Employee(code=code, full_name=f"Người mua {code}", company_id=seed.company_id,
                   department_id=dept_id, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"{code}@x", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    role = Role(code=f"R{code}", name="Vai trò test")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity="purchase_order", scope=scope, can_read=True))
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    perm_cache_clear()
    return user, emp


def _po(db, seed, code, dept_id, handler_dept_id, status="approved", created_by=None, nspt_id=0):
    db.add(PurchaseOrder(code=code, company_id=seed.company_id, department_id=dept_id, department="",
                         handler_dept_id=handler_dept_id, status=status, nspt_id=nspt_id,
                         created_by=created_by or seed.u_req_id, updated_by=seed.u_req_id))
    db.flush()


def _visible(db, user) -> set[str]:
    profile = get_perm_profile(db, user)
    q = apply_scope(db.query(PurchaseOrder), PurchaseOrder, "purchase_order", user, profile)
    return {r.code for r in q.all()}


def test_factory_buyer_does_not_see_own_department_orders_handled_by_central_purchasing(db, seed, depts):
    factory, purchasing = depts
    user, _ = _buyer(db, seed, factory)
    _po(db, seed, "PO-NM-TM-XU-LY", factory, purchasing)       # ca PO00890
    _po(db, seed, "PO-NM-TU-MUA", factory, factory)
    _po(db, seed, "PO-TM-NHO-NM", purchasing, factory)
    _po(db, seed, "PO-TM", purchasing, purchasing)
    assert _visible(db, user) == {"PO-NM-TU-MUA", "PO-TM-NHO-NM"}


def test_factory_buyer_still_sees_orders_they_created_or_are_nspt_on(db, seed, depts):
    factory, purchasing = depts
    user, emp = _buyer(db, seed, factory)
    _po(db, seed, "PO-MINH-LAP", factory, purchasing, created_by=user.id)
    _po(db, seed, "PO-MINH-NSPT", purchasing, purchasing, nspt_id=emp.id)
    _po(db, seed, "PO-NGUOI-KHAC", factory, purchasing)
    assert _visible(db, user) == {"PO-MINH-LAP", "PO-MINH-NSPT"}


def test_factory_buyer_does_not_pick_up_unapproved_orders_of_own_handling(db, seed, depts):
    factory, _ = depts
    user, _ = _buyer(db, seed, factory)
    _po(db, seed, "PO-NHAP", factory, factory, status="draft")
    _po(db, seed, "PO-DA-DUYET", factory, factory)
    assert _visible(db, user) == {"PO-DA-DUYET"}


def test_dept_proc_buyer_without_department_sees_nothing(db, seed, depts):
    factory, _ = depts
    user, _ = _buyer(db, seed, 0)
    _po(db, seed, "PO-BAT-KY", factory, factory)
    assert _visible(db, user) == set()


def test_dept_scope_unchanged_still_sees_orders_requested_by_own_department(db, seed, depts):
    """Bậc `dept` (trưởng phòng) không đổi: vẫn thấy đơn của phòng mình yêu cầu."""
    factory, purchasing = depts
    user, _ = _buyer(db, seed, factory, scope="dept", code="H736")
    _po(db, seed, "PO-NM-TM-XU-LY", factory, purchasing)
    assert "PO-NM-TM-XU-LY" in _visible(db, user)
