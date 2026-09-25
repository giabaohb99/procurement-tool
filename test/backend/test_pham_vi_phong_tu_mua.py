"""bao-CR-414 — "Phòng ban tự mua hàng": bậc `dept_proc` + cột phòng được nhờ `handler_dept_id`.

Ba bộ phạm vi đã chốt với khách:
  · THU MUA TOÀN QUYỀN — `pur_manager` bậc `all`, không đổi gì.
  · NHÀ MÁY — quản lý thu mua CỦA PHÒNG (bậc `dept_proc`): đúng nhánh `proc` NHƯNG chỉ trong
    phòng mình (phòng lập phiếu HOẶC phòng được nhờ). Phòng khác không thấy.
  · THU MUA TRỪ NHÀ MÁY — bậc `proc` + ô «Loại trừ phòng ban» = nhà máy. bao-CR-480 (đại
    ca chốt 24/09/2026) đổi cột so sánh sang PHÒNG XỬ LÝ: không thấy phiếu nhà máy ĐANG MUA
    (kể cả phiếu phòng khác nhờ nhà máy), nhưng thấy phiếu nhà máy xin mà thu mua chung mua.

Dựng hai phòng (`Nhà máy` / `Thu mua`) và người xem KHÔNG dính phiếu (không tạo, không yêu
cầu, không được gán) để chỉ còn nhánh phòng ban quyết định.
"""
import pytest

from app.core.auth import get_perm_profile, perm_cache_clear
from app.core.scoping import apply_scope, approves_only_in_dept_proc
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.role.model import Permission, Role
from app.modules.survey_request.model import SurveyRequest
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


def _viewer(db, seed, entity: str, scope: str, dept_id: int | None, *,
            approve: bool = False, exclude_dept_ids: tuple[int, ...] = ()):
    """Một người thu mua có quyền đọc `entity` với bậc `scope`, ở phòng `dept_id`, không dính phiếu nào."""
    _counter["n"] += 1
    n = _counter["n"]
    emp = Employee(code=f"V414{n:02d}", full_name=f"Người xem {n}", company_id=seed.company_id,
                   department_id=dept_id or 0, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"V414{n:02d}", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    role = Role(code=f"R414{n:02d}", name="Vai trò test")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity=entity, scope=scope, can_read=True, can_approve=approve))
    db.add(UserRole(user_id=user.id, role_id=role.id))
    for did in exclude_dept_ids:
        db.add(UserScope(user_id=user.id, role_id=role.id, entity="", dim="department",
                         value=str(did), is_exclude=True))
    db.flush()
    perm_cache_clear()
    return user


def _add_pr(db, seed, code: str, dept_id: int, status: str = "approved", handler_dept_id: int = 0):
    db.add(PurchaseRequest(code=code, company_id=seed.company_id, department_id=dept_id,
                           department="", handler_dept_id=handler_dept_id, status=status,
                           requester_id=seed.emp_req_id,
                           created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.flush()


def _visible_pr_codes(db, user) -> set[str]:
    profile = get_perm_profile(db, user)
    rows = apply_scope(db.query(PurchaseRequest), PurchaseRequest, "purchase_request", user, profile).all()
    return {r.code for r in rows}


def _seed_three_prs(db, seed, factory_id, purchasing_id):
    """Ba phiếu đã duyệt: của nhà máy · của thu mua · của thu mua NHỜ nhà máy xử lý."""
    _add_pr(db, seed, "PYC-NM", factory_id)
    _add_pr(db, seed, "PYC-TM", purchasing_id)
    _add_pr(db, seed, "PYC-TM-NHO-NM", purchasing_id, handler_dept_id=factory_id)


# ── Bậc `dept_proc` — quản lý thu mua CỦA PHÒNG ─────────────────────────────────────────

def test_dept_proc_sees_only_own_department_and_handed_over_tickets(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    _seed_three_prs(db, seed, factory_id, purchasing_id)
    user = _viewer(db, seed, "purchase_request", "dept_proc", factory_id)
    assert _visible_pr_codes(db, user) == {"PYC-NM", "PYC-TM-NHO-NM"}


def test_dept_proc_still_hides_own_department_tickets_before_approval(db, seed, two_departments):
    """`dept_proc` là `proc` thu hẹp — vẫn KHÔNG thấy nháp/chờ duyệt của phòng mình."""
    factory_id, _ = two_departments
    _add_pr(db, seed, "PYC-NHAP", factory_id, status="draft")
    _add_pr(db, seed, "PYC-CHO", factory_id, status="submitted")
    _add_pr(db, seed, "PYC-DUYET", factory_id, status="approved")
    _add_pr(db, seed, "PYC-MUA", factory_id, status="purchased")
    user = _viewer(db, seed, "purchase_request", "dept_proc", factory_id)
    assert _visible_pr_codes(db, user) == {"PYC-DUYET", "PYC-MUA"}


def test_dept_proc_without_department_sees_nothing(db, seed, two_departments):
    """Chưa gắn phòng thì chặn (cùng luật bậc `dept`), không được rơi về `proc` toàn công ty."""
    factory_id, purchasing_id = two_departments
    _seed_three_prs(db, seed, factory_id, purchasing_id)
    user = _viewer(db, seed, "purchase_request", "dept_proc", None)
    assert _visible_pr_codes(db, user) == set()


def test_dept_proc_on_survey_request_sees_every_non_draft_ticket_of_own_department(db, seed, two_departments):
    """YCBG: quản lý thu mua của phòng phải thấy phiếu từ lúc gửi duyệt để duyệt + gán NSTM."""
    factory_id, purchasing_id = two_departments
    for code, dept, status, handler in [
        ("YCBG-NM-NHAP", factory_id, "draft", 0),
        ("YCBG-NM-CHO", factory_id, "submitted", 0),
        ("YCBG-NM-DUYET", factory_id, "approved", 0),
        ("YCBG-TM-DUYET", purchasing_id, "approved", 0),
        ("YCBG-TM-NHO-NM", purchasing_id, "submitted", factory_id),
    ]:
        db.add(SurveyRequest(code=code, company_id=seed.company_id, department_id=dept,
                             department="", handler_dept_id=handler, status=status,
                             requester_id=seed.emp_req_id,
                             created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.flush()
    user = _viewer(db, seed, "survey_request", "dept_proc", factory_id)
    profile = get_perm_profile(db, user)
    rows = apply_scope(db.query(SurveyRequest), SurveyRequest, "survey_request", user, profile).all()
    assert {r.code for r in rows} == {"YCBG-NM-CHO", "YCBG-NM-DUYET", "YCBG-TM-NHO-NM"}


# ── Bậc `proc` + loại trừ phòng — thu mua chung trừ nhà máy ─────────────────────────────

def test_proc_scope_unchanged_when_no_exclude(db, seed, two_departments):
    """Chưa gán bậc mới, chưa loại trừ gì thì y như trước: thấy mọi phiếu đã duyệt."""
    factory_id, purchasing_id = two_departments
    _seed_three_prs(db, seed, factory_id, purchasing_id)
    user = _viewer(db, seed, "purchase_request", "proc", purchasing_id)
    assert _visible_pr_codes(db, user) == {"PYC-NM", "PYC-TM", "PYC-TM-NHO-NM"}


def test_proc_with_department_exclude_filters_by_handling_department(db, seed, two_departments):
    """bao-CR-480 — loại trừ so PHÒNG XỬ LÝ, không so phòng lập.

    Trước CR này bài kiểm mong `{"PYC-TM", "PYC-NM-NHO-TM"}`: phiếu nhà máy xin mà thu mua
    chung mua (`PYC-NM`, handler = 0) bị GIẤU khỏi quản lý thu mua chung — tức họ không thấy
    đơn nhân viên mình đang mua — còn phiếu phòng khác nhờ nhà máy mua thì lại thấy.
    """
    factory_id, purchasing_id = two_departments
    _add_pr(db, seed, "PYC-NM", factory_id)                                      # nhà máy xin, thu mua chung mua
    _add_pr(db, seed, "PYC-NM-TU-MUA", factory_id, handler_dept_id=factory_id)   # nhà máy tự mua
    _add_pr(db, seed, "PYC-TM", purchasing_id)
    _add_pr(db, seed, "PYC-TM-NHO-NM", purchasing_id, handler_dept_id=factory_id)  # nhờ nhà máy mua
    _add_pr(db, seed, "PYC-NM-NHO-TM", factory_id, handler_dept_id=purchasing_id)
    _add_pr(db, seed, "PYC-NM-NHO-KHAC", factory_id, handler_dept_id=999)
    user = _viewer(db, seed, "purchase_request", "proc", purchasing_id, exclude_dept_ids=(factory_id,))
    assert _visible_pr_codes(db, user) == {"PYC-NM", "PYC-TM", "PYC-NM-NHO-TM", "PYC-NM-NHO-KHAC"}


# ── Bậc `dept` — trưởng phòng cũng thấy phiếu được nhờ cho phòng mình ──────────────────

def test_dept_scope_sees_tickets_handed_over_to_own_department(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    _add_pr(db, seed, "PYC-NM", factory_id, status="draft")
    _add_pr(db, seed, "PYC-TM", purchasing_id, status="draft")
    _add_pr(db, seed, "PYC-TM-NHO-NM", purchasing_id, status="submitted", handler_dept_id=factory_id)
    user = _viewer(db, seed, "purchase_request", "dept", factory_id)
    assert _visible_pr_codes(db, user) == {"PYC-NM", "PYC-TM-NHO-NM"}


# ── Tắt tự gán theo nhóm hàng khi người duyệt chỉ có bậc `dept_proc` ──────────────────

def test_approves_only_in_dept_proc_is_true_for_factory_manager(db, seed, two_departments):
    factory_id, _ = two_departments
    user = _viewer(db, seed, "purchase_request", "dept_proc", factory_id, approve=True)
    assert approves_only_in_dept_proc(get_perm_profile(db, user), "purchase_request") is True


def test_approves_only_in_dept_proc_is_false_for_full_manager(db, seed, two_departments):
    _, purchasing_id = two_departments
    user = _viewer(db, seed, "purchase_request", "all", purchasing_id, approve=True)
    assert approves_only_in_dept_proc(get_perm_profile(db, user), "purchase_request") is False


def test_approves_only_in_dept_proc_is_false_when_a_global_approve_grant_also_exists(
        db, seed, two_departments):
    """Có thêm một grant `proc`/`all` biết duyệt thì vẫn tự gán như cũ."""
    factory_id, _ = two_departments
    user = _viewer(db, seed, "purchase_request", "dept_proc", factory_id, approve=True)
    role = Role(code="R414-EXTRA", name="Thêm bậc proc")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity="purchase_request", scope="proc",
                      can_read=True, can_approve=True))
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    perm_cache_clear()
    assert approves_only_in_dept_proc(get_perm_profile(db, user), "purchase_request") is False


def test_approves_only_in_dept_proc_is_false_without_approve_permission(db, seed, two_departments):
    """Chỉ đọc bậc `dept_proc`, không duyệt → không phải người điều phối, trả False."""
    factory_id, _ = two_departments
    user = _viewer(db, seed, "purchase_request", "dept_proc", factory_id, approve=False)
    assert approves_only_in_dept_proc(get_perm_profile(db, user), "purchase_request") is False


# ── GĐ2: bảng phân công theo PHÒNG — tra theo phòng đang xử lý, rơi về bộ chung có điều kiện ──

def _add_employee(db, seed, code: str, dept_id: int):
    emp = Employee(code=code, full_name=f"NSTM {code}", company_id=seed.company_id,
                   department_id=dept_id, is_active=True)
    db.add(emp)
    db.flush()
    return emp


def _add_pr_line(db, seed, pr_code: str, item_group: str):
    from app.modules.purchase_request.model import PurchaseRequestItem
    pr = db.query(PurchaseRequest).filter(PurchaseRequest.code == pr_code).one()
    ln = PurchaseRequestItem(pr_id=pr.id, item_group=item_group, product_name="x", qty=1,
                             created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(ln)
    db.flush()
    return pr, ln


@pytest.fixture
def factory_assignee_table(db, seed, two_departments):
    """Bộ chung (phòng 0) đã có sẵn từ seed test: Nhãn/Thùng → emp_nstm. Thêm bộ RIÊNG của nhà máy
    cho Nhãn → NM01; Thùng thì nhà máy KHÔNG khai."""
    from app.modules.catalog.model import ItemGroup
    from app.modules.category_assignee.model import CategoryAssignee
    factory_id, purchasing_id = two_departments
    nm01 = _add_employee(db, seed, "NM01", factory_id)
    g_nhan = db.query(ItemGroup).filter(ItemGroup.name == "Nhãn").one()
    db.add(CategoryAssignee(department_id=factory_id, item_group_id=g_nhan.id,
                            primary_employee_id=nm01.id, backup_employee_id=0))
    db.flush()
    return factory_id, purchasing_id, nm01


def test_auto_assign_uses_department_rows_for_the_handling_department(db, seed, factory_assignee_table):
    from app.modules.category_assignee.service import auto_assign_by_category
    factory_id, _, nm01 = factory_assignee_table
    _add_pr(db, seed, "PYC-NM-NHAN", factory_id)
    pr, ln = _add_pr_line(db, seed, "PYC-NM-NHAN", "Nhãn")
    assert auto_assign_by_category(db, pr, allow_global=False) == 1
    assert ln.assignee == nm01.code


def test_auto_assign_dept_only_does_not_fall_back_to_shared_rows(db, seed, factory_assignee_table):
    """Phòng chưa khai Thùng, người điều phối chỉ có bậc `dept_proc` → dòng để trống, KHÔNG lấy
    NSTM của bộ chung (đó là người của thu mua chung)."""
    from app.modules.category_assignee.service import auto_assign_by_category
    factory_id, _, _ = factory_assignee_table
    _add_pr(db, seed, "PYC-NM-THUNG", factory_id)
    pr, ln = _add_pr_line(db, seed, "PYC-NM-THUNG", "Thùng")
    assert auto_assign_by_category(db, pr, allow_global=False) == 0
    assert not ln.assignee


def test_auto_assign_full_manager_falls_back_to_shared_rows(db, seed, factory_assignee_table):
    """Người điều phối toàn quyền: phân loại phòng chưa khai riêng thì rơi về bộ chung."""
    from app.modules.category_assignee.service import auto_assign_by_category
    factory_id, _, nm01 = factory_assignee_table
    _add_pr(db, seed, "PYC-NM-HAI", factory_id)
    pr, ln_nhan = _add_pr_line(db, seed, "PYC-NM-HAI", "Nhãn")
    _, ln_thung = _add_pr_line(db, seed, "PYC-NM-HAI", "Thùng")
    assert auto_assign_by_category(db, pr, allow_global=True) == 2
    assert ln_nhan.assignee == nm01.code            # bộ riêng của phòng thắng bộ chung
    assert ln_thung.assignee == seed.emp_nstm_code  # phòng chưa khai → bộ chung


def test_auto_assign_resolves_by_handler_department_when_ticket_is_handed_over(db, seed, factory_assignee_table):
    """Thu mua lập phiếu NHỜ nhà máy xử lý → tra bộ của nhà máy, không phải của phòng lập."""
    from app.modules.category_assignee.service import auto_assign_by_category
    factory_id, purchasing_id, nm01 = factory_assignee_table
    _add_pr(db, seed, "PYC-TM-NHO-NM", purchasing_id, handler_dept_id=factory_id)
    pr, ln = _add_pr_line(db, seed, "PYC-TM-NHO-NM", "Nhãn")
    assert auto_assign_by_category(db, pr, allow_global=True) == 1
    assert ln.assignee == nm01.code


def test_auto_assign_without_new_tier_behaves_exactly_as_before(db, seed, factory_assignee_table):
    """Luật "phạm vi là công tắc": phòng thu mua không có bộ riêng, người điều phối như cũ →
    kết quả y hệt trước GĐ2 (bộ chung gán emp_nstm)."""
    from app.modules.category_assignee.service import auto_assign_by_category
    _, purchasing_id, _ = factory_assignee_table
    _add_pr(db, seed, "PYC-TM-CU", purchasing_id)
    pr, ln = _add_pr_line(db, seed, "PYC-TM-CU", "Nhãn")
    assert auto_assign_by_category(db, pr) == 1
    assert ln.assignee == seed.emp_nstm_code


def test_resolve_for_group_prefers_department_row_then_shared_row(db, seed, factory_assignee_table):
    from app.modules.category_assignee.service import resolve_for_group
    factory_id, _, nm01 = factory_assignee_table
    assert resolve_for_group(db, "Nhãn", factory_id).code == nm01.code
    assert resolve_for_group(db, "Thùng", factory_id).code == seed.emp_nstm_code
    assert resolve_for_group(db, "Thùng", factory_id, allow_global=False) is None
    assert resolve_for_group(db, "Nhãn").code == seed.emp_nstm_code   # gọi kiểu cũ = bộ chung


def test_bulk_upsert_keeps_shared_and_department_rows_apart(db, seed, two_departments):
    from app.modules.catalog.model import ItemGroup
    from app.modules.category_assignee.model import CategoryAssignee
    from app.modules.category_assignee.service import bulk_upsert
    factory_id, _ = two_departments
    nm01 = _add_employee(db, seed, "NM01", factory_id)
    g = db.query(ItemGroup).filter(ItemGroup.name == "Nhãn").one()
    before = db.query(CategoryAssignee).filter(CategoryAssignee.item_group_id == g.id).count()
    assert bulk_upsert(db, [g.id], nm01.id, 0, seed.u_req_id, department_id=factory_id) == 1
    assert bulk_upsert(db, [g.id], nm01.id, 0, seed.u_req_id, department_id=factory_id) == 1  # lần 2 = cập nhật
    rows = db.query(CategoryAssignee).filter(CategoryAssignee.item_group_id == g.id).all()
    assert len(rows) == before + 1
    shared = [r for r in rows if r.department_id == 0]
    assert shared and shared[0].primary_employee_id == seed.emp_nstm_id   # bộ chung không bị đè


def test_create_rejects_duplicate_pair_but_allows_same_group_in_another_department(db, seed, two_departments):
    from fastapi import HTTPException
    from app.modules.catalog.model import ItemGroup
    from app.modules.category_assignee.schema import CategoryAssigneeCreate
    from app.modules.category_assignee.service import create
    factory_id, _ = two_departments
    g = db.query(ItemGroup).filter(ItemGroup.name == "Nhãn").one()
    with pytest.raises(HTTPException):     # bộ chung đã có Nhãn
        create(db, CategoryAssigneeCreate(item_group_id=g.id, primary_employee_id=seed.emp_nstm_id), seed.u_req_id)
    row = create(db, CategoryAssigneeCreate(item_group_id=g.id, department_id=factory_id,
                                            primary_employee_id=seed.emp_nstm_id), seed.u_req_id)
    assert row.department_id == factory_id


# ── Cột phòng được nhờ chép xuống chứng từ con ─────────────────────────────────────────

def test_purchase_order_inherits_handler_department_from_purchase_request(db, seed, two_departments):
    from app.modules.purchase_order.service import _handler_dept_of_pr
    factory_id, purchasing_id = two_departments
    _add_pr(db, seed, "PYC-NHO", purchasing_id, handler_dept_id=factory_id)
    _add_pr(db, seed, "PYC-KHONG-NHO", purchasing_id)
    assert _handler_dept_of_pr(db, "PYC-NHO") == factory_id
    assert _handler_dept_of_pr(db, "PYC-KHONG-NHO") == 0
    assert _handler_dept_of_pr(db, "") == 0
    assert _handler_dept_of_pr(db, "PYC-KHONG-CO") == 0
