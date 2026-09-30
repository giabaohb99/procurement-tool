"""bao-CR-524 — bỏ phòng ảo «Thu mua chung», phòng thu mua mặc định là «Sản xuất -Thu mua».

Khách chốt 30/09/2026. Trước CR này `0` ở `handler_dept_id` (YCMH · YCBG · ĐMH), `department_id`
(công nợ · YCTT) và `tab_category_assignee.department_id` mang nghĩa «Thu mua chung» — một phòng
không có trong danh mục. Nay phòng thu mua mặc định là phòng THẬT mang mã cấu hình được
(`central_purchasing_dept_code`, mặc định `PBA017`), tra mã → id ở MỘT chỗ
(`core/central_purchasing.py`), không gõ cứng id.

Các ca canh ở đây:
  · phiếu mới không nhờ phòng nào ghi id thật; «Trả về thu mua» ghi id thật;
  · người `dept_proc` của phòng PBA017 thấy phiếu thu mua chung — nhưng người bậc `dept` của
    phòng đó KHÔNG thấy phiếu mọi phòng (không thì trưởng phòng PBA017 duyệt bước 1 hộ cả công ty);
  · `0` còn sót vẫn được đọc là phòng mặc định ở mọi chỗ (trước và sau backfill không gãy);
  · script backfill: xem thử không ghi, ghi thật đổi đúng dòng, chạy lại vô hại, xung đột thì
    bỏ qua chứ không xóa;
  · ô chọn NSTM của phiếu thu mua chung.
"""
import json
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException
from starlette.requests import Request

from app.core import app_settings
from app.core.auth import get_perm_profile, perm_cache_clear
from app.core.central_purchasing import (get_central_dept_id, is_central_dept,
                                         normalize_handler_dept_id)
from app.core.scoping import apply_scope, holds_handling_dept
from app.modules.audit.model import AuditLog
from app.modules.catalog.model import ItemGroup
from app.modules.category_assignee import controller as ca_ctl
from app.modules.category_assignee import service as ca_service
from app.modules.category_assignee.model import CategoryAssignee
from app.modules.category_assignee.schema import CategoryAssigneeCreate
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.payable import service as pay_service
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_order.schema import POCreate
from app.modules.purchase_request import controller as pr_ctl
from app.modules.purchase_request import service as pr_service
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import PRCreate, TransferDeptIn
from app.modules.role.model import Permission, Role
from app.modules.survey_request import service as sr_service
from app.modules.survey_request.schema import SurveyRequestCreate
from app.modules.user.model import User, UserRole, UserScope

from scripts.backfill_central_purchasing_dept import run_backfill


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


_n = {"i": 0}


def _person(db, seed, dept_id: int, scope: str | None, *, approve: bool = False,
            exclude_dept_ids: tuple[int, ...] = ()):
    """Nhân sự ở phòng `dept_id`; `scope` ≠ None thì có tài khoản giữ quyền YCMH bậc đó."""
    _n["i"] += 1
    n = _n["i"]
    emp = Employee(code=f"T524{n:02d}", full_name=f"Người 524-{n}", company_id=seed.company_id,
                   department_id=dept_id or 0, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"T524{n:02d}", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    if scope:
        role = Role(code=f"R524{n:02d}", name="Vai trò test")
        db.add(role)
        db.flush()
        for entity in ("purchase_request", "survey_request"):
            db.add(Permission(role_id=role.id, entity=entity, scope=scope, can_read=True,
                              can_create=True, can_write=True, can_approve=approve))
        db.add(UserRole(user_id=user.id, role_id=role.id))
        for did in exclude_dept_ids:
            db.add(UserScope(user_id=user.id, role_id=role.id, entity="", dim="department",
                             value=str(did), is_exclude=True))
    db.commit()
    perm_cache_clear()
    return SimpleNamespace(user=user, emp=emp)


@pytest.fixture
def depts(db, seed):
    """Phòng PBA017 thật + nhà máy (phòng tự mua) + một phòng thường."""
    central = Department(code="PBA017", name="Sản xuất -Thu mua", company_id=seed.company_id,
                         is_active=True)
    factory = Department(code="NM524", name="Nhà máy", company_id=seed.company_id, is_active=True)
    marketing = Department(code="MKT524", name="Marketing", company_id=seed.company_id, is_active=True)
    db.add_all([central, factory, marketing])
    db.commit()
    #  Nhà máy là phòng TỰ MUA: có người giữ YCMH bậc `dept_proc` (bao-CR-480).
    f_mgr = _person(db, seed, factory.id, "dept_proc", approve=True)
    return SimpleNamespace(central=central.id, factory=factory.id, marketing=marketing.id, f_mgr=f_mgr)


def _pr(db, seed, code: str, dept_id: int, handler: int, status: str = "approved") -> PurchaseRequest:
    pr = PurchaseRequest(code=code, company_id=seed.company_id, department_id=dept_id,
                         department="Phòng lập", handler_dept_id=handler, status=status,
                         requester_id=seed.emp_req_id, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_name="Hàng", item_group="Nhãn", line_status="no_po",
                               created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    return pr


def _visible_codes(db, user) -> set[str]:
    profile = get_perm_profile(db, user)
    return {r.code for r in apply_scope(db.query(PurchaseRequest), PurchaseRequest,
                                        "purchase_request", user, profile).all()}


def _data(resp) -> dict:
    return json.loads(resp.body)["data"]


# ── Trợ giúp tra mã → id ─────────────────────────────────────────────────────────────────

def test_central_department_is_resolved_by_code_never_by_id(db, seed, depts):
    assert get_central_dept_id(db) == depts.central
    assert is_central_dept(db, depts.central) and is_central_dept(db, 0)
    assert not is_central_dept(db, depts.factory)
    assert normalize_handler_dept_id(db, 0) == depts.central
    assert normalize_handler_dept_id(db, depts.factory) == depts.factory
    #  Đổi mã ở màn Cấu hình → trỏ sang phòng khác, không cần deploy.
    app_settings._cache["central_purchasing_dept_code"] = "MKT524"
    assert get_central_dept_id(db) == depts.marketing
    #  Mã không có trong danh mục → 0 = quay về đúng hành vi cũ, không gãy chỗ nào.
    app_settings._cache["central_purchasing_dept_code"] = "KHONG-CO"
    assert get_central_dept_id(db) == 0 and normalize_handler_dept_id(db, 0) == 0


def test_setting_key_is_registered_and_shown_on_the_settings_screen():
    from app.modules.setting import service as setting_service
    assert app_settings.REGISTRY["central_purchasing_dept_code"] == ("str", "CENTRAL_PURCHASING_DEPT_CODE")
    assert any(f["key"] == "central_purchasing_dept_code" for f in setting_service.FIELDS)
    assert app_settings.get("central_purchasing_dept_code") == "PBA017"


# ── Phiếu mới ────────────────────────────────────────────────────────────────────────────

def test_new_documents_not_delegated_get_the_real_central_id(db, seed, depts):
    untouched = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester_id=seed.emp_req_id,
                                                  department_id=depts.marketing, purpose="không tick"),
                                     user_id=seed.u_req_id)
    chose_zero = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester_id=seed.emp_req_id,
                                                   department_id=depts.marketing, handler_dept_id=0,
                                                   purpose="tick, để trống"), user_id=seed.u_req_id)
    factory = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester_id=depts.f_mgr.emp.id,
                                                department_id=depts.factory, purpose="nhà máy"),
                                   user_id=seed.u_req_id)
    assert untouched.handler_dept_id == depts.central
    assert chose_zero.handler_dept_id == depts.central, "gửi 0 = nhờ phòng thu mua mặc định, ghi id thật"
    assert factory.handler_dept_id == depts.factory, "phòng tự mua vẫn tự nhận phiếu của mình (CR-480)"

    sr = sr_service.create_sr(db, SurveyRequestCreate(company_id=seed.company_id, requester_id=seed.emp_req_id,
                                                      department_id=depts.marketing, purpose="YCBG"),
                              user_id=seed.u_req_id)
    assert sr.handler_dept_id == depts.central

    lone = po_service.create_po(db, POCreate(company_id=seed.company_id, supplier_code="NX",
                                             supplier_name="NCC", department_id=depts.marketing),
                                user_id=seed.u_req_id)
    assert lone.handler_dept_id == depts.central, "đơn lẻ không qua YCMH cũng thuộc phòng mặc định"


def test_update_sending_zero_is_stored_as_the_central_id(db, seed, depts):
    from app.modules.purchase_request.schema import PRUpdate
    pr = _pr(db, seed, "PYC-524-UPD", depts.marketing, depts.factory, status="draft")
    pr_service.update_pr(db, pr.id, PRUpdate(handler_dept_id=0), user_id=seed.u_req_id)
    db.refresh(pr)
    assert pr.handler_dept_id == depts.central


def test_order_created_from_a_legacy_zero_request_lands_on_central(db, seed, depts):
    _pr(db, seed, "PYC-524-CU", depts.marketing, 0, status="dispatched")
    po = po_service.create_po(db, POCreate(company_id=seed.company_id, pr_code="PYC-524-CU",
                                           supplier_code="NX", supplier_name="NCC",
                                           department_id=depts.marketing), user_id=seed.u_req_id)
    assert po.handler_dept_id == depts.central
    assert pay_service.debt_dept_of(po, db) == depts.central


# ── Trả về thu mua ───────────────────────────────────────────────────────────────────────

def test_return_to_purchasing_sets_the_central_id_and_refuses_when_already_there(db, seed, depts):
    admin = _person(db, seed, depts.central, "all", approve=True)
    pr = _pr(db, seed, "PYC-524-TRA", depts.factory, depts.factory)
    out = _data(pr_ctl.return_dept_(pr.id, TransferDeptIn(reason="Nhà máy không mua được"),
                                    BackgroundTasks(), db, admin.user))
    db.refresh(pr)
    assert pr.handler_dept_id == depts.central and out["handler_dept_id"] == depts.central
    assert out["handler_dept_name"] == "Sản xuất -Thu mua"
    assert out["can_return_dept"] is False, "đang ở phòng mặc định thì không còn gì để trả về"
    log = (db.query(AuditLog).filter(AuditLog.entity == "purchase_request", AuditLog.entity_id == pr.id)
           .order_by(AuditLog.id.desc()).first())
    assert log.action == "return_dept" and "Nhà máy -> Sản xuất -Thu mua" in log.message

    for handler in (depts.central, 0):   # id thật lẫn `0` cũ đều là «đang ở thu mua»
        again = _pr(db, seed, f"PYC-524-TRA-{handler}", depts.factory, handler)
        with pytest.raises(HTTPException) as e:
            pr_ctl.return_dept_(again.id, TransferDeptIn(reason="x"), BackgroundTasks(), db, admin.user)
        assert e.value.status_code == 400


def test_central_ticket_can_now_be_transferred_to_its_requesting_department(db, seed, depts):
    """Luật cũ «0 và đích = phòng lập → trùng phòng» là di tích trước CR-480; nay 0 = thu mua."""
    admin = _person(db, seed, depts.central, "all", approve=True)
    pr = _pr(db, seed, "PYC-524-CHUYEN", depts.factory, 0)
    out = _data(pr_ctl.transfer_dept_(pr.id, TransferDeptIn(handler_dept_id=depts.factory, reason="Nhà máy tự mua"),
                                      BackgroundTasks(), db, admin.user))
    assert out["handler_dept_id"] == depts.factory


# ── Phạm vi ──────────────────────────────────────────────────────────────────────────────

def test_dept_proc_of_the_central_department_sees_central_tickets_old_and_new(db, seed, depts):
    c_mgr = _person(db, seed, depts.central, "dept_proc", approve=True)
    _pr(db, seed, "PYC-524-MOI", depts.marketing, depts.central)
    _pr(db, seed, "PYC-524-CU0", depts.marketing, 0)                  # chưa backfill
    _pr(db, seed, "PYC-524-NM", depts.factory, depts.factory)          # nhà máy tự mua
    seen = _visible_codes(db, c_mgr.user)
    assert {"PYC-524-MOI", "PYC-524-CU0"} <= seen
    assert "PYC-524-NM" not in seen
    #  Quản lý thu mua nhà máy KHÔNG thấy phiếu thu mua chung.
    f_seen = _visible_codes(db, depts.f_mgr.user)
    assert "PYC-524-NM" in f_seen and not ({"PYC-524-MOI", "PYC-524-CU0"} & f_seen)


def test_dept_scope_of_the_central_department_does_not_see_every_departments_tickets(db, seed, depts):
    """Chốt chống nở phạm vi: trưởng phòng PBA017 (bậc `dept`) chỉ thấy phiếu phòng MÌNH lập."""
    head = _person(db, seed, depts.central, "dept", approve=True)
    _pr(db, seed, "PYC-524-MKT", depts.marketing, depts.central, status="submitted")
    _pr(db, seed, "PYC-524-MKT0", depts.marketing, 0, status="submitted")
    _pr(db, seed, "PYC-524-CUA-TM", depts.central, depts.central, status="submitted")
    seen = _visible_codes(db, head.user)
    assert "PYC-524-CUA-TM" in seen
    assert not ({"PYC-524-MKT", "PYC-524-MKT0"} & seen)


def test_excluding_the_central_department_also_excludes_leftover_zero(db, seed, depts):
    buyer = _person(db, seed, depts.factory, "proc", exclude_dept_ids=(depts.central,))
    _pr(db, seed, "PYC-524-EX-ID", depts.marketing, depts.central)
    _pr(db, seed, "PYC-524-EX-0", depts.marketing, 0)
    _pr(db, seed, "PYC-524-EX-NM", depts.marketing, depts.factory)
    assert _visible_codes(db, buyer.user) >= {"PYC-524-EX-NM"}
    assert not ({"PYC-524-EX-ID", "PYC-524-EX-0"} & _visible_codes(db, buyer.user))


def test_unknown_central_code_never_hides_zero_tickets_behind_a_null(db, seed, depts):
    """Mã cấu hình sai → câu truy vấn con ra NULL; `NOT (... NULL)` từng nuốt mọi phiếu `0`."""
    app_settings._cache["central_purchasing_dept_code"] = "KHONG-CO"
    buyer = _person(db, seed, depts.central, "proc", exclude_dept_ids=(depts.factory,))
    _pr(db, seed, "PYC-524-NULL", depts.marketing, 0)
    assert "PYC-524-NULL" in _visible_codes(db, buyer.user)


# ── `0` còn sót được đọc là phòng mặc định ──────────────────────────────────────────────

def test_leftover_zero_reads_as_central_everywhere(db, seed, depts):
    c_mgr = _person(db, seed, depts.central, "dept_proc", approve=True)
    pr = _pr(db, seed, "PYC-524-DOC", depts.marketing, 0)
    out = pr_ctl._out(db, pr, c_mgr.user)
    assert out["handler_dept_id"] == depts.central
    assert out["handler_dept_name"] == "Sản xuất -Thu mua"
    assert out["can_return_dept"] is False
    assert holds_handling_dept(get_perm_profile(db, c_mgr.user), "purchase_request", pr,
                               get_central_dept_id(db))
    assert pr_service.dispatch_context(db, pr)["handler_dept_id"] == 0, \
        "điều kiện bỏ qua điều phối (CR-497) vẫn thấy phiếu thu mua chung là 0"
    moi = _pr(db, seed, "PYC-524-DOC2", depts.marketing, depts.central)
    assert pr_service.dispatch_context(db, moi)["handler_dept_id"] == 0
    po = PurchaseOrder(code="PO-524-CU", company_id=seed.company_id, handler_dept_id=0, status="approved",
                       created_by=seed.u_req_id)
    db.add(po)
    db.flush()
    assert pay_service.debt_dept_of(po, db) == depts.central
    assert pay_service.debt_dept_of(po) == 0, "không có db → giữ đúng số trên đơn như trước"


def test_leftover_zero_assignment_rows_still_drive_auto_assign(db, seed, depts):
    """Dòng phân công `0` cũ (bộ «Thu mua chung») vẫn là bộ của phòng mặc định; dòng id thật thắng."""
    nhan = db.query(ItemGroup).filter(ItemGroup.name == "Nhãn").one()
    db.query(CategoryAssignee).delete()
    db.add(CategoryAssignee(department_id=0, item_group_id=nhan.id, primary_employee_id=seed.emp_backup_id))
    db.commit()
    pr = _pr(db, seed, "PYC-524-GAN", depts.marketing, depts.central)
    assert ca_service.auto_assign_by_category(db, pr, allow_global=False) == 1, \
        "phòng mặc định dùng bộ của chính nó kể cả khi không được rơi về bộ chung"
    assert pr_service.items_of(db, pr.id)[0].assignee == seed.emp_backup_code
    db.add(CategoryAssignee(department_id=depts.central, item_group_id=nhan.id,
                            primary_employee_id=seed.emp_nstm_id))
    db.commit()
    assert ca_service.resolve_for_group(db, "Nhãn", depts.central).code == seed.emp_nstm_code


# ── Bảng phân công ──────────────────────────────────────────────────────────────────────

def test_assignment_written_with_zero_is_stored_on_the_central_department(db, seed, depts):
    thung = db.query(ItemGroup).filter(ItemGroup.name == "Thùng").one()
    db.query(CategoryAssignee).delete()
    db.commit()
    row = ca_service.create(db, CategoryAssigneeCreate(item_group_id=thung.id,
                                                       primary_employee_id=seed.emp_nstm_id,
                                                       department_id=0), user_id=seed.u_req_id)
    assert row.department_id == depts.central


def test_legacy_zero_row_blocks_a_duplicate_and_bulk_moves_it_to_the_real_id(db, seed, depts):
    thung = db.query(ItemGroup).filter(ItemGroup.name == "Thùng").one()
    db.query(CategoryAssignee).delete()
    legacy = CategoryAssignee(department_id=0, item_group_id=thung.id, primary_employee_id=seed.emp_nstm_id)
    db.add(legacy)
    db.commit()
    with pytest.raises(HTTPException) as e:
        ca_service.create(db, CategoryAssigneeCreate(item_group_id=thung.id, primary_employee_id=seed.emp_nstm_id,
                                                     department_id=depts.central), user_id=seed.u_req_id)
    assert e.value.status_code == 400
    ca_service.bulk_upsert(db, [thung.id], seed.emp_backup_id, 0, seed.u_req_id, department_id=0)
    db.refresh(legacy)
    assert legacy.department_id == depts.central and legacy.primary_employee_id == seed.emp_backup_id
    assert db.query(CategoryAssignee).filter(CategoryAssignee.item_group_id == thung.id).count() == 1


def test_assignment_list_shows_the_real_department_and_filters_old_rows_with_new(db, seed, depts):
    nhan = db.query(ItemGroup).filter(ItemGroup.name == "Nhãn").one()
    thung = db.query(ItemGroup).filter(ItemGroup.name == "Thùng").one()
    db.query(CategoryAssignee).delete()
    db.add(CategoryAssignee(department_id=0, item_group_id=nhan.id, primary_employee_id=seed.emp_nstm_id))
    db.add(CategoryAssignee(department_id=depts.central, item_group_id=thung.id,
                            primary_employee_id=seed.emp_nstm_id))
    db.add(CategoryAssignee(department_id=depts.factory, item_group_id=nhan.id,
                            primary_employee_id=seed.emp_nstm_id))
    db.commit()

    def _list(qs: str) -> list[dict]:
        req = Request({"type": "http", "query_string": qs.encode(), "headers": []})
        return _data(ca_ctl.list_(req, "item_group_name", "asc", "", "", {"offset": 0, "limit": 50},
                                  db, None))["items"]

    rows = _list(f"department_id__eq={depts.central}")
    assert {r["item_group_name"] for r in rows} == {"Nhãn", "Thùng"}, "dòng `0` cũ đi chung nhóm với dòng mới"
    assert {r["department_id"] for r in rows} == {depts.central}
    assert {r["department_name"] for r in rows} == {"Sản xuất -Thu mua"}
    assert not any(r["department_name"] is None for r in _list(""))


# ── Ô chọn NSTM của phiếu thu mua chung ─────────────────────────────────────────────────

def test_staff_picker_for_a_central_ticket(db, seed, depts):
    c_staff = _person(db, seed, depts.central, "assigned")        # NSTM thường của phòng PBA017
    c_mgr = _person(db, seed, depts.central, "dept_proc")          # quản lý thu mua PBA017
    other_buyer = _person(db, seed, depts.marketing, "proc")       # admin thu mua ngồi phòng khác
    f_buyer = _person(db, seed, depts.factory, "proc")             # người thu mua của nhà máy
    worker = _person(db, seed, depts.central, None)                # không có vai trò thu mua
    for handler in (depts.central, 0):
        pr = _pr(db, seed, f"PYC-524-NSTM-{handler}", depts.marketing, handler)
        ids = {e.id for e in ca_service.assignable_staff(db, pr)}
        assert {c_staff.emp.id, c_mgr.emp.id, other_buyer.emp.id} <= ids
        assert f_buyer.emp.id not in ids and depts.f_mgr.emp.id not in ids and worker.emp.id not in ids
        ca_service.check_assignee_allowed(db, pr, c_mgr.emp.code)
        with pytest.raises(HTTPException):
            ca_service.check_assignee_allowed(db, pr, f_buyer.emp.code)
    factory_pr = _pr(db, seed, "PYC-524-NSTM-NM", depts.factory, depts.factory)
    assert {e.id for e in ca_service.assignable_staff(db, factory_pr)} == {depts.f_mgr.emp.id, f_buyer.emp.id}


# ── Script backfill ─────────────────────────────────────────────────────────────────────

def _backfill_world(db, seed, depts):
    nhan = db.query(ItemGroup).filter(ItemGroup.name == "Nhãn").one()
    thung = db.query(ItemGroup).filter(ItemGroup.name == "Thùng").one()
    db.query(CategoryAssignee).delete()
    w = SimpleNamespace()
    w.pr0 = _pr(db, seed, "PYC-524-BF0", depts.marketing, 0)
    w.pr_nm = _pr(db, seed, "PYC-524-BFNM", depts.factory, depts.factory)
    w.po0 = PurchaseOrder(code="PO-524-BF0", company_id=seed.company_id, handler_dept_id=0,
                          status="approved", created_by=seed.u_req_id)
    w.po_nm = PurchaseOrder(code="PO-524-BFNM", company_id=seed.company_id, handler_dept_id=depts.factory,
                            status="approved", created_by=seed.u_req_id)
    db.add_all([w.po0, w.po_nm])
    db.flush()
    w.pay_central = Payable(company_id=seed.company_id, department_id=0, po_id=w.po0.id, ref_id=1,
                            supplier_code="NX", total=10)
    w.pay_no_order = Payable(company_id=seed.company_id, department_id=0, po_id=0, ref_id=2,
                             supplier_code="NX", total=10)
    w.pay_stale = Payable(company_id=seed.company_id, department_id=0, po_id=w.po_nm.id, ref_id=3,
                          supplier_code="NX", total=10)
    db.add_all([w.pay_central, w.pay_no_order, w.pay_stale])
    db.flush()
    w.req_central = PaymentRequest(code="YCTT-524-A", company_id=seed.company_id, department_id=0)
    w.req_manual = PaymentRequest(code="YCTT-524-B", company_id=seed.company_id, department_id=0)
    w.req_mixed = PaymentRequest(code="YCTT-524-C", company_id=seed.company_id, department_id=0)
    db.add_all([w.req_central, w.req_manual, w.req_mixed])
    db.flush()
    db.add_all([PaymentRequestLine(request_id=w.req_central.id, payable_id=w.pay_central.id),
                PaymentRequestLine(request_id=w.req_manual.id, payable_id=0),
                PaymentRequestLine(request_id=w.req_mixed.id, payable_id=w.pay_central.id),
                PaymentRequestLine(request_id=w.req_mixed.id, payable_id=w.pay_no_order.id)])
    w.ca_free = CategoryAssignee(department_id=0, item_group_id=nhan.id, primary_employee_id=seed.emp_nstm_id)
    w.ca_conflict = CategoryAssignee(department_id=0, item_group_id=thung.id, primary_employee_id=seed.emp_nstm_id)
    w.ca_taken = CategoryAssignee(department_id=depts.central, item_group_id=thung.id,
                                  primary_employee_id=seed.emp_backup_id)
    db.add_all([w.ca_free, w.ca_conflict, w.ca_taken])
    db.commit()
    return w


def test_backfill_dry_run_counts_but_writes_nothing(db, seed, depts):
    w = _backfill_world(db, seed, depts)
    report = run_backfill(db, apply=False)
    assert report["purchase_request"]["changed"] == 1
    assert report["purchase_order"]["changed"] == 1
    assert report["payable"] == {"changed": 1, "skipped_no_order": 1, "skipped_other_dept": 1}
    assert report["payment_request"] == {"changed": 1, "skipped_no_payable": 1, "skipped_other_dept": 1}
    assert report["category_assignee"]["changed"] == 1
    assert [c["id"] for c in report["category_assignee"]["conflicts"]] == [w.ca_conflict.id]
    for obj in (w.pr0, w.po0, w.pay_central, w.req_central, w.ca_free):
        db.refresh(obj)
    assert w.pr0.handler_dept_id == 0 and w.po0.handler_dept_id == 0
    assert w.pay_central.department_id == 0 and w.req_central.department_id == 0
    assert w.ca_free.department_id == 0


def test_backfill_apply_changes_exactly_the_right_rows_and_is_idempotent(db, seed, depts):
    w = _backfill_world(db, seed, depts)
    run_backfill(db, apply=True)
    for obj in (w.pr0, w.pr_nm, w.po0, w.po_nm, w.pay_central, w.pay_no_order, w.pay_stale,
                w.req_central, w.req_manual, w.req_mixed, w.ca_free, w.ca_conflict, w.ca_taken):
        db.refresh(obj)
    assert w.pr0.handler_dept_id == depts.central and w.pr_nm.handler_dept_id == depts.factory
    assert w.po0.handler_dept_id == depts.central and w.po_nm.handler_dept_id == depts.factory
    assert w.pay_central.department_id == depts.central
    assert w.pay_no_order.department_id == 0, "nợ không có đơn: 0 = không gắn phòng, giữ nguyên"
    assert w.pay_stale.department_id == 0, "nợ lệch phòng xử lý của đơn: không tự đoán, để resync lo"
    assert w.req_central.department_id == depts.central
    assert w.req_manual.department_id == 0 and w.req_mixed.department_id == 0
    assert w.ca_free.department_id == depts.central
    assert w.ca_conflict.department_id == 0, "xung đột: bỏ qua"
    assert db.query(CategoryAssignee).count() == 3, "không xóa dòng nào"

    again = run_backfill(db, apply=True)
    assert again["purchase_request"]["changed"] == 0 and again["purchase_order"]["changed"] == 0
    assert again["payable"]["changed"] == 0 and again["payment_request"]["changed"] == 0
    assert again["category_assignee"]["changed"] == 0
    assert len(again["category_assignee"]["conflicts"]) == 1


def test_backfill_refuses_when_the_central_code_is_not_in_the_catalog(db, seed):
    app_settings._cache["central_purchasing_dept_code"] = "KHONG-CO"
    assert "error" in run_backfill(db, apply=True)
