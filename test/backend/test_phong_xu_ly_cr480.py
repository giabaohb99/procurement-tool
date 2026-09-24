"""bao-CR-480 — «Phòng xử lý» là một ô duy nhất, lọc theo nó, và tự điền cho phòng tự mua hàng.

Ba luật, đại ca chốt 24/09/2026 sau khi xem bộ đơn mẫu trên dev:
  1. «Loại trừ phòng ban» trên chứng từ thu mua so cột PHÒNG XỬ LÝ (`handler_dept_id`),
     không so phòng lập — quản lý thu mua chung trừ nhà máy phải thấy đơn nhân viên mình
     đang mua cho nhà máy, và KHÔNG thấy đơn nhà máy mua hộ phòng khác.
  2. Người của phòng TỰ MUA HÀNG (phòng có ai đó giữ bậc `dept_proc`) lập phiếu thì phòng
     xử lý mặc định là chính phòng đó; ai khác thì thu mua chung (`0`).
  3. API trả `handler_dept_name` và phiếu cũ rỗng Phòng ban thì HIỂN THỊ theo hồ sơ nhân sự.
"""
import pytest

from app.core.auth import get_perm_profile, perm_cache_clear
from app.core.scoping import apply_scope
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request import service as pr_service
from app.modules.purchase_request.controller import _out as pr_out
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.purchase_request.schema import PRCreate, PRUpdate
from app.modules.role.model import Permission, Role
from app.modules.survey_request import service as sr_service
from app.modules.survey_request.model import SurveyRequest
from app.modules.survey_request.schema import SurveyRequestCreate
from app.modules.user.model import User, UserRole, UserScope


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


@pytest.fixture
def two_departments(db, seed):
    factory = Department(code="NM", name="Nhà máy", company_id=seed.company_id, is_active=True)
    purchasing = Department(code="TM", name="Thu mua", company_id=seed.company_id, is_active=True)
    db.add_all([factory, purchasing])
    db.flush()
    return factory.id, purchasing.id


_counter = {"n": 0}


def _person(db, seed, dept_id: int, entity: str = "purchase_request", scope: str = "proc",
            exclude_dept_ids: tuple[int, ...] = (), active: bool = True):
    """Một người ở phòng `dept_id` có quyền đọc `entity` bậc `scope`, không dính phiếu nào."""
    _counter["n"] += 1
    n = _counter["n"]
    emp = Employee(code=f"P480{n:02d}", full_name=f"Người {n}", company_id=seed.company_id,
                   department_id=dept_id or 0, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"P480{n:02d}", employee_id=emp.id, password_hash="x", is_active=active)
    db.add(user)
    db.flush()
    role = Role(code=f"R480{n:02d}", name="Vai trò test")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity=entity, scope=scope, can_read=True, can_create=True))
    db.add(UserRole(user_id=user.id, role_id=role.id))
    for did in exclude_dept_ids:
        db.add(UserScope(user_id=user.id, role_id=role.id, entity="", dim="department",
                         value=str(did), is_exclude=True))
    db.flush()
    perm_cache_clear()
    return user, emp


def _visible(db, user, model, entity) -> set[str]:
    profile = get_perm_profile(db, user)
    return {r.code for r in apply_scope(db.query(model), model, entity, user, profile).all()}


# ── 1. Loại trừ so PHÒNG XỬ LÝ — ba chứng từ thu mua ──────────────────────────────────────

def _add_po(db, seed, code, dept_id, handler_dept_id=0):
    db.add(PurchaseOrder(code=code, company_id=seed.company_id, department_id=dept_id,
                         department="", handler_dept_id=handler_dept_id, status="approved",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.flush()


def _add_sr(db, seed, code, dept_id, handler_dept_id=0):
    db.add(SurveyRequest(code=code, company_id=seed.company_id, department_id=dept_id,
                         department="", handler_dept_id=handler_dept_id, status="approved",
                         requester_id=seed.emp_req_id,
                         created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.flush()


def test_exclude_on_purchase_order_hides_orders_the_factory_is_buying(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    _add_po(db, seed, "PO-NM-XIN", factory_id)                                  # nhà máy xin, thu mua chung mua
    _add_po(db, seed, "PO-NM-TU-MUA", factory_id, handler_dept_id=factory_id)   # nhà máy tự mua
    _add_po(db, seed, "PO-TM", purchasing_id)
    _add_po(db, seed, "PO-TM-NHO-NM", purchasing_id, handler_dept_id=factory_id)  # phòng khác nhờ nhà máy
    user, _ = _person(db, seed, purchasing_id, "purchase_order", exclude_dept_ids=(factory_id,))
    assert _visible(db, user, PurchaseOrder, "purchase_order") == {"PO-NM-XIN", "PO-TM"}


def test_exclude_on_survey_request_uses_handling_department(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    _add_sr(db, seed, "SR-NM-XIN", factory_id)
    _add_sr(db, seed, "SR-NM-TU-MUA", factory_id, handler_dept_id=factory_id)
    _add_sr(db, seed, "SR-TM-NHO-NM", purchasing_id, handler_dept_id=factory_id)
    #  Bậc `proc` của YCBG chỉ thấy dòng gán mình, nên dùng bậc `all` để chỉ còn ô loại trừ nói.
    user, _ = _person(db, seed, purchasing_id, "survey_request", scope="all", exclude_dept_ids=(factory_id,))
    assert _visible(db, user, SurveyRequest, "survey_request") == {"SR-NM-XIN"}


def test_exclude_without_handler_column_still_filters_by_own_department(db, seed, two_departments):
    """Entity không có cột phòng xử lý (ở đây mượn `payable` qua model có `department_id`)
    giữ luật cũ — bài này canh nhánh `else` không bị xóa nhầm khi dọn mã."""
    from app.modules.payable.model import Payable
    factory_id, purchasing_id = two_departments
    for code, dept in (("NO-NM", factory_id), ("NO-TM", purchasing_id)):
        db.add(Payable(company_id=seed.company_id, department_id=dept, supplier_code="NX",
                       supplier_name="NX", po_code=code, source_type="po", ref_type="delivery",
                       amount=1, vat=0, total=1, paid_amount=0, remaining=1, status="open",
                       created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.flush()
    user, _ = _person(db, seed, purchasing_id, "payable", scope="company", exclude_dept_ids=(factory_id,))
    profile = get_perm_profile(db, user)
    rows = apply_scope(db.query(Payable), Payable, "payable", user, profile).all()
    assert {r.po_code for r in rows} == {"NO-TM"}


# ── 2. Phòng tự mua hàng → phòng xử lý mặc định ──────────────────────────────────────────

def test_self_purchasing_departments_come_from_dept_proc_grants(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    assert pr_service.list_self_purchasing_dept_ids(db) == set()
    _person(db, seed, factory_id, scope="dept_proc")
    assert pr_service.list_self_purchasing_dept_ids(db) == {factory_id}
    assert pr_service.default_handler_dept_id(db, factory_id) == factory_id
    assert pr_service.default_handler_dept_id(db, purchasing_id) == 0
    assert pr_service.default_handler_dept_id(db, 0) == 0


def test_inactive_account_does_not_make_a_department_self_purchasing(db, seed, two_departments):
    """Nhà máy giải tán bộ máy mua (khóa tài khoản) thì phiếu mới lại về thu mua chung."""
    factory_id, _ = two_departments
    _person(db, seed, factory_id, scope="dept_proc", active=False)
    assert pr_service.list_self_purchasing_dept_ids(db) == set()


def test_create_pr_from_factory_defaults_handler_to_own_department(db, seed, two_departments):
    factory_id, _ = two_departments
    _, factory_emp = _person(db, seed, factory_id, scope="dept_proc")
    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester=factory_emp.full_name,
                                           requester_id=factory_emp.id, department_id=factory_id,
                                           purpose="Nhà máy mua"), user_id=seed.u_req_id)
    assert pr.handler_dept_id == factory_id


def test_create_pr_keeps_an_explicit_handler_and_other_departments_default_to_shared(
        db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    _, factory_emp = _person(db, seed, factory_id, scope="dept_proc")
    # Nhà máy chủ động chọn phòng khác (ví dụ thu mua) — giữ nguyên lựa chọn.
    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester_id=factory_emp.id,
                                           department_id=factory_id, handler_dept_id=purchasing_id,
                                           purpose="Nhờ thu mua"), user_id=seed.u_req_id)
    assert pr.handler_dept_id == purchasing_id
    # Phòng KHÔNG tự mua (phòng Test của seed) → thu mua chung.
    pr2 = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester_id=seed.emp_req_id,
                                            purpose="Phòng thường"), user_id=seed.u_req_id)
    assert pr2.handler_dept_id == 0


def test_update_to_shared_purchasing_is_respected_not_refilled(db, seed, two_departments):
    """Sau khi tạo, nhà máy đổi sang «Thu mua chung» (0) là lựa chọn có chủ ý."""
    factory_id, _ = two_departments
    _, factory_emp = _person(db, seed, factory_id, scope="dept_proc")
    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester_id=factory_emp.id,
                                           department_id=factory_id, purpose="x"), user_id=seed.u_req_id)
    assert pr.handler_dept_id == factory_id
    pr = pr_service.update_pr(db, pr.id, PRUpdate(handler_dept_id=0), user_id=seed.u_req_id)
    assert pr.handler_dept_id == 0


def test_create_sr_from_factory_defaults_handler_to_own_department(db, seed, two_departments):
    factory_id, _ = two_departments
    _, factory_emp = _person(db, seed, factory_id, scope="dept_proc")
    s = sr_service.create_sr(db, SurveyRequestCreate(company_id=seed.company_id, requester_id=factory_emp.id,
                                                     department_id=factory_id, purpose="x"),
                             user_id=seed.u_req_id)
    assert s.handler_dept_id == factory_id


# ── 3. Tên phòng xử lý + phòng ban hiển thị lùi theo hồ sơ nhân sự ──────────────────────

def test_out_carries_handler_dept_name_and_blank_for_shared_purchasing(db, seed, two_departments):
    factory_id, _ = two_departments
    pr = PurchaseRequest(code="PYC-X", company_id=seed.company_id, department_id=factory_id,
                         department="Nhà máy", handler_dept_id=factory_id, status="draft",
                         requester_id=seed.emp_req_id, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    assert pr_out(db, pr)["handler_dept_name"] == "Nhà máy"
    pr.handler_dept_id = 0
    assert pr_out(db, pr)["handler_dept_name"] == ""


def test_out_shows_department_from_employee_when_ticket_left_it_blank(db, seed):
    """Phiếu lập trước bao-CR-465 còn rỗng Phòng ban: màn hình hiện theo hồ sơ nhân sự,
    nhưng KHÔNG ghi đè dữ liệu — ghi là việc của lưu / gửi duyệt."""
    pr = PurchaseRequest(code="PYC-CU", company_id=seed.company_id, department_id=0, department="",
                         status="submitted", requester_id=seed.emp_req_id,
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    d = pr_out(db, pr)
    assert d["department"] == "Phòng Test" and d["department_id"] == seed.dept_id
    db.refresh(pr)
    assert pr.department == "" and pr.department_id == 0


# ── 4. Chuyển đổi phiếu cũ của phòng tự mua (backfill) ─────────────────────────────────

def test_backfill_flips_legacy_factory_tickets_and_leaves_shared_purchasing_alone(
        db, seed, two_departments):
    """Phiếu cũ «không nhờ ai» của phòng tự mua → phòng xử lý = chính phòng đó, ở cả ba
    chứng từ; phiếu phòng thường và phiếu đã có phòng xử lý thì không đụng."""
    factory_id, purchasing_id = two_departments
    _person(db, seed, factory_id, scope="dept_proc")
    db.add(PurchaseRequest(code="PYC-NM-CU", company_id=seed.company_id, department_id=factory_id,
                           department="", handler_dept_id=0, status="submitted",
                           requester_id=seed.emp_req_id, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.add(PurchaseRequest(code="PYC-TM-CU", company_id=seed.company_id, department_id=purchasing_id,
                           department="", handler_dept_id=0, status="submitted",
                           requester_id=seed.emp_req_id, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.add(PurchaseRequest(code="PYC-NM-NHO-TM", company_id=seed.company_id, department_id=factory_id,
                           department="", handler_dept_id=purchasing_id, status="submitted",
                           requester_id=seed.emp_req_id, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    _add_sr(db, seed, "SR-NM-CU", factory_id)
    _add_po(db, seed, "PO-NM-CU", factory_id)
    _add_po(db, seed, "PO-TM-CU", purchasing_id)
    db.flush()

    assert pr_service.backfill_handling_dept(db, dry_run=True) == {
        "purchase_request": 1, "survey_request": 1, "purchase_order": 1}
    assert db.query(PurchaseRequest).filter_by(code="PYC-NM-CU").one().handler_dept_id == 0, "dry-run không ghi"

    assert pr_service.backfill_handling_dept(db) == {
        "purchase_request": 1, "survey_request": 1, "purchase_order": 1}
    by = {r.code: r.handler_dept_id for r in db.query(PurchaseRequest).all()}
    assert by["PYC-NM-CU"] == factory_id and by["PYC-TM-CU"] == 0 and by["PYC-NM-NHO-TM"] == purchasing_id
    assert db.query(SurveyRequest).filter_by(code="SR-NM-CU").one().handler_dept_id == factory_id
    pos = {r.code: r.handler_dept_id for r in db.query(PurchaseOrder).all()}
    assert pos["PO-NM-CU"] == factory_id and pos["PO-TM-CU"] == 0
    # Chạy lại: không còn gì để đổi.
    assert pr_service.backfill_handling_dept(db) == {
        "purchase_request": 0, "survey_request": 0, "purchase_order": 0}


def test_backfill_resolves_blank_department_from_requester_and_po_from_source_pr(
        db, seed, two_departments):
    """Phiếu rỗng phòng ban (trước bao-CR-465) tra hồ sơ nhân sự; ĐMH rỗng phòng thì theo YCMH nguồn."""
    factory_id, _ = two_departments
    _, factory_emp = _person(db, seed, factory_id, scope="dept_proc")
    db.add(PurchaseRequest(code="PYC-RONG", company_id=seed.company_id, department_id=0, department="",
                           handler_dept_id=0, status="approved", requester_id=factory_emp.id,
                           created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.add(PurchaseOrder(code="PO-RONG", pr_code="PYC-RONG", company_id=seed.company_id, department_id=0,
                         department="", handler_dept_id=0, status="approved",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.flush()
    assert pr_service.backfill_handling_dept(db) == {"purchase_request": 1, "survey_request": 0, "purchase_order": 1}
    pr = db.query(PurchaseRequest).filter_by(code="PYC-RONG").one()
    assert (pr.department_id, pr.department, pr.handler_dept_id) == (factory_id, "Nhà máy", factory_id)
    assert db.query(PurchaseOrder).filter_by(code="PO-RONG").one().handler_dept_id == factory_id


def test_out_fills_department_name_when_only_id_is_stored(db, seed, two_departments):
    """Phiếu dựng bằng script có id phòng mà tên rỗng (ca DEMO-CR414-NM03) — hiện tên, không ghi."""
    factory_id, _ = two_departments
    pr = PurchaseRequest(code="PYC-ID", company_id=seed.company_id, department_id=factory_id, department="",
                         status="submitted", requester_id=seed.emp_req_id,
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    assert pr_out(db, pr)["department"] == "Nhà máy"
    db.refresh(pr)
    assert pr.department == ""
