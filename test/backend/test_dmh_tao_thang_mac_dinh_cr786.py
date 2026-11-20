"""bao-CR-786 — ĐMH tạo thẳng (không YCMH nguồn) điền mặc định theo người lập, đại ca chốt 20/11/2026.

- Phòng xử lý: theo đúng luật YCMH — người của phòng tự mua → chính phòng đó, còn lại → phòng thu mua mặc định.
  Người lập chọn rõ (kể cả 0 = phòng thu mua mặc định) thì giữ.
- Bộ phận trống → phòng người lập; Trưởng phòng phê duyệt trống → trưởng phòng của phòng đó (trừ khi chính người
  lập là trưởng phòng).
- Đơn có YCMH nguồn: không đổi gì so với trước.
"""
from types import SimpleNamespace

import pytest

from app.core.auth import perm_cache_clear
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.edit_service import default_po_approver_id
from app.modules.purchase_order.schema import POCreate
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole

_n = {"i": 0}


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


def _person(db, seed, dept_id: int, scope: str | None = None):
    _n["i"] += 1
    n = _n["i"]
    emp = Employee(code=f"T786{n:02d}", full_name=f"Người 786-{n}", company_id=seed.company_id,
                   department_id=dept_id, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"T786{n:02d}", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    if scope:
        role = Role(code=f"R786{n:02d}", name="Vai trò test")
        db.add(role)
        db.flush()
        db.add(Permission(role_id=role.id, entity="purchase_request", scope=scope, can_read=True, can_create=True))
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    perm_cache_clear()
    return SimpleNamespace(user=user, emp=emp)


@pytest.fixture
def depts(db, seed):
    central = Department(code="PBA017", name="Sản xuất -Thu mua", company_id=seed.company_id, is_active=True)
    factory = Department(code="NM786", name="Nhà máy", company_id=seed.company_id, is_active=True)
    it = Department(code="IT786", name="IT", company_id=seed.company_id, is_active=True)
    db.add_all([central, factory, it])
    db.commit()
    _person(db, seed, factory.id, "dept_proc")   # nhà máy là phòng tự mua
    return SimpleNamespace(central=central.id, factory=factory.id, it=it.id)


def _direct(db, seed, user_id, **kw):
    kw.setdefault("company_id", seed.company_id)
    return po_service.create_po(db, POCreate(supplier_code="NX", supplier_name="NCC", **kw), user_id=user_id)


def test_factory_buyer_direct_order_defaults_to_own_department(db, seed, depts):
    buyer = _person(db, seed, depts.factory)
    po = _direct(db, seed, buyer.user.id)
    assert po.handler_dept_id == depts.factory
    assert po.department_id == depts.factory, "bộ phận trống thì theo phòng người lập"


def test_other_department_direct_order_defaults_to_central(db, seed, depts):
    it_staff = _person(db, seed, depts.it)
    po = _direct(db, seed, it_staff.user.id)
    assert po.handler_dept_id == depts.central


def test_explicit_choice_is_kept_even_zero(db, seed, depts):
    buyer = _person(db, seed, depts.factory)
    assert _direct(db, seed, buyer.user.id, handler_dept_id=depts.it).handler_dept_id == depts.it
    assert _direct(db, seed, buyer.user.id, handler_dept_id=0).handler_dept_id == depts.central


def test_approver_defaults_to_head_of_creator_department(db, seed, depts):
    head = _person(db, seed, depts.it)
    db.get(Department, depts.it).manager_id = head.emp.id
    db.commit()
    staff = _person(db, seed, depts.it)
    po = _direct(db, seed, staff.user.id)
    assert po.approver_employee_id == head.emp.id
    #  Chính trưởng phòng lập đơn thì không tự gán mình duyệt.
    assert default_po_approver_id(db, depts.it, head.user.id) == 0
    #  Chọn rõ người khác thì giữ.
    other = _direct(db, seed, staff.user.id, approver_employee_id=seed.emp_tp_id)
    assert other.approver_employee_id == seed.emp_tp_id


def test_nspt_defaults_to_creator(db, seed, depts):
    staff = _person(db, seed, depts.it)
    po = _direct(db, seed, staff.user.id)
    assert po.nspt_id == staff.emp.id


# ── bao-CR-787: màn tạo hiện đúng mặc định; hồ sơ thiếu công ty thì lấy công ty của phòng ──────────────

def test_creator_defaults_show_factory_handler_and_fall_back_to_department_company(db, seed, depts):
    from app.modules.purchase_order.edit_service import creator_order_defaults
    buyer = _person(db, seed, depts.factory)
    buyer.emp.company_id = 0          # hồ sơ chưa gán công ty (gặp thật trên prod: NSU012)
    db.commit()
    got = creator_order_defaults(db, buyer.user.id)
    assert got["handler_dept_id"] == depts.factory
    assert got["handler_dept_name"] == "Nhà máy"
    assert got["company_id"] == seed.company_id, "hồ sơ trống công ty thì theo công ty của phòng"
    po = _direct(db, seed, buyer.user.id, company_id=0)
    assert po.company_id == seed.company_id
    assert po.handler_dept_id == depts.factory


def test_creator_defaults_for_other_department_show_central(db, seed, depts):
    from app.modules.purchase_order.edit_service import creator_order_defaults
    it_staff = _person(db, seed, depts.it)
    got = creator_order_defaults(db, it_staff.user.id)
    assert got["handler_dept_id"] == depts.central
    assert got["handler_dept_name"] == "Sản xuất -Thu mua"


def test_company_falls_back_to_creator_last_order_when_profile_and_department_are_blank(db, seed, depts):
    """bao-CR-788 — hồ sơ và phòng đều chưa gán công ty (gặp thật trên prod) → công ty của đơn gần nhất người đó lập."""
    from app.modules.purchase_order.edit_service import creator_order_defaults
    buyer = _person(db, seed, depts.factory)
    buyer.emp.company_id = 0
    db.get(Department, depts.factory).company_id = 0
    db.commit()
    assert creator_order_defaults(db, buyer.user.id)["company_id"] == 0
    _direct(db, seed, buyer.user.id, company_id=seed.company_id)
    assert creator_order_defaults(db, buyer.user.id)["company_id"] == seed.company_id
