"""bao-CR-499 — ô «Trưởng phòng phê duyệt» CHỌN được, báo người được chọn, bản in in người thực duyệt.

Đại ca chốt 26/09/2026 (qua ERP Agent 2, xác nhận lại ở phiên Erp Agent 1): giữ HAI ô tách
(«Trưởng bộ phận» CR-474 và ô này); ô này chọn được để hệ gửi mail/chuông cho người đó; bấm Duyệt
xong cột đổi thành người THỰC duyệt; bản in in tên trong cột (chưa ai duyệt thì in người được chọn);
bỏ công tắc «người ký» của bao-CR-490.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks

from app.modules.department.model import Department
from app.modules.purchase_order import controller as po_ctl
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_order.schema import POCreate, POUpdate, RejectIn
from app.modules.purchase_request import controller as pr_ctl
from app.modules.purchase_request import service as pr_service
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import ApproveIn, PRCreate, PRUpdate
from app.modules.survey_request import controller as sr_ctl
from app.modules.survey_request.schema import SurveyRequestCreate, SurveyRequestUpdate
from app.modules.user.model import User

USER = SimpleNamespace(id=1)


@pytest.fixture(autouse=True)
def _quiet(monkeypatch, cap_quyen):
    monkeypatch.setattr(pr_ctl, "_notify_assigned", lambda *a, **kw: None)
    monkeypatch.setattr(pr_ctl, "_in_approve_scope", lambda db, user, pid: True)
    monkeypatch.setattr(pr_ctl.service, "dispatch_enabled", lambda: True)
    from app.modules.survey_request.model import SurveyRequest
    monkeypatch.setattr(sr_ctl, "_in_scope", lambda db, sid, u, action: db.get(SurveyRequest, sid))
    monkeypatch.setattr(sr_ctl, "_can_edit_own", lambda db, s, u: True)
    monkeypatch.setattr(po_ctl, "_in_scope", lambda db, pid, u, action: None)
    for entity in ("purchase_request", "survey_request", "purchase_order"):
        cap_quyen(USER.id, entity, scope="all", read=True, write=True, approve=True, create=True)


@pytest.fixture
def captured(monkeypatch):
    """Bắt lời gọi thông báo của cả ba controller — kiểm NGƯỜI NHẬN, không gửi gì thật."""
    calls: list[dict] = []
    monkeypatch.setattr(pr_ctl, "trigger_notification", lambda **kw: calls.append(kw))
    monkeypatch.setattr(po_ctl, "trigger_notification", lambda **kw: calls.append(kw))
    monkeypatch.setattr(sr_ctl, "_notify", lambda db, recips, *a, **kw: calls.append({"recips": list(recips)}))
    return calls


def _dept(db, seed):
    dept = db.query(Department).filter(Department.id == seed.dept_id).first() if hasattr(seed, "dept_id") \
        else db.query(Department).filter(Department.code == "DEPT01").first()
    return dept


def test_schemas_accept_the_chosen_approver():
    assert PRCreate(approver_employee_id=7).approver_employee_id == 7
    assert PRUpdate(approver_employee_id=7).model_dump(exclude_unset=True) == {"approver_employee_id": 7}
    assert SurveyRequestCreate(approver_employee_id=7).approver_employee_id == 7
    assert "approver_employee_id" in SurveyRequestUpdate(approver_employee_id=7).model_dump(exclude_unset=True)
    assert POCreate(approver_employee_id=7).approver_employee_id == 7
    assert POUpdate(approver_employee_id=7).approver_employee_id == 7


def test_pr_chosen_approver_is_notified_on_submit_and_printed_before_approval(db, seed, captured):
    dept = _dept(db, seed)
    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester="Người YC",
                                           requester_id=seed.emp_req_id, department=dept.name,
                                           head_of_dept_id=seed.emp_tp_id,
                                           approver_employee_id=seed.emp_nstm_id), seed.u_req_id)
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP01", product_name="Hàng", item_group="Nhãn",
                               qty=1, unit="cái", price=1, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert pr.approver_employee_id == seed.emp_nstm_id

    #  Chưa ai duyệt: bản in đã in NGƯỜI ĐƯỢC CHỌN ở ô «TP/BP đề xuất».
    signers = pr_ctl._approval_signers(db, pr)
    assert signers["approver_name"] == "NSTM Chính"

    pr_ctl.submit_pr(pr.id, BackgroundTasks(), db=db, user=SimpleNamespace(id=seed.u_req_id))
    submit = [c for c in captured if c.get("event") == "pr_submitted"]
    assert submit and sorted(submit[0]["extra_employee_ids"]) == sorted([seed.emp_tp_id, seed.emp_nstm_id]), \
        "cả TBP (CR-474) lẫn người được chọn duyệt đều nhận chuông"

    #  Bấm Duyệt: cột đổi thành người THỰC duyệt, bản in in người đó.
    pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=USER)
    db.refresh(pr)
    assert pr.approver_employee_id == db.get(User, USER.id).employee_id
    assert pr_ctl._approval_signers(db, pr)["approver_name"] == "Người YC"


def test_pr_update_can_change_the_chosen_approver_while_draft(db, seed):
    dept = _dept(db, seed)
    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester="Người YC",
                                           requester_id=seed.emp_req_id, department=dept.name), seed.u_req_id)
    assert pr.approver_employee_id == int(pr.head_of_dept_id or 0), "mặc định = Trưởng bộ phận"
    pr_service.update_pr(db, pr.id, PRUpdate(approver_employee_id=seed.emp_tp_id), seed.u_req_id)
    db.refresh(pr)
    assert pr.approver_employee_id == seed.emp_tp_id


def test_sr_chosen_approver_is_notified_on_submit(db, seed, captured):
    dept = _dept(db, seed)
    from app.modules.survey_request import service as sr_service
    s = sr_service.create_sr(db, SurveyRequestCreate(company_id=seed.company_id, requester="Người YC",
                                                     requester_id=seed.emp_req_id, department=dept.name,
                                                     head_of_dept_id=seed.emp_tp_id,
                                                     approver_employee_id=seed.emp_nstm_id), seed.u_req_id)
    assert s.approver_employee_id == seed.emp_nstm_id
    sr_ctl.submit_(s.id, BackgroundTasks(), db=db, user=SimpleNamespace(id=seed.u_req_id))
    recips = [c for c in captured if "recips" in c][-1]["recips"]
    emp_ids = sorted(u.employee_id for u in recips)
    assert seed.emp_nstm_id in emp_ids and seed.emp_tp_id in emp_ids
    assert len(emp_ids) == len(set(emp_ids)), "không gửi trùng một người hai lần"


def test_po_chosen_approver_is_notified_and_kept_after_unapprove(db, seed, captured):
    dept = _dept(db, seed)
    po = PurchaseOrder(code="PO-499", company_id=seed.company_id, department=dept.name,
                       department_id=dept.id, supplier_code="NCCA", supplier_name="NCC",
                       order_date="2026-09-01", status="submitted", approver_employee_id=seed.emp_tp_id,
                       created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(po)
    db.commit()
    #  Chưa duyệt: bản in in người được chọn.
    assert po_ctl.resolve_print_signers(db, po)["approver_name"] == "Trưởng Phòng"

    po_ctl.approve_po(po.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(po)
    actual = db.get(User, USER.id).employee_id
    assert po.approver_employee_id == actual
    assert po_ctl.resolve_print_signers(db, po)["approver_name"] == "Người YC"

    #  Hủy duyệt: KHÔNG xóa cột nữa — người vừa duyệt vẫn là người được chọn cho lần sau.
    po_ctl.unapprove_po(po.id, RejectIn(reason="sai giá"), db=db, user=USER)
    db.refresh(po)
    assert po.approver_employee_id == actual


# ── Hướng 1 (đại ca chốt 26/09): danh sách chọn = người DUYỆT ĐƯỢC đúng chứng từ đó ────────────

def _person(db, seed, code, dept_id, active=True):
    from app.modules.employee.model import Employee
    emp = Employee(code=code, full_name=f"NV {code}", company_id=seed.company_id, department_id=dept_id,
                   is_active=True)
    db.add(emp)
    db.flush()
    u = User(email=code, employee_id=emp.id, password_hash="x", is_active=active)
    db.add(u)
    db.flush()
    return emp, u


def test_candidates_follow_approve_scope_not_the_callers_view(db, seed, cap_quyen):
    from app.core.approver_candidates import candidates_for_draft, candidates_for_row, draft_fields
    dept = _dept(db, seed)
    other = Department(code="OTHER499", name="Phòng khác", company_id=seed.company_id, is_active=True)
    db.add(other)
    db.flush()
    head, u_head = _person(db, seed, "HEAD499", dept.id)
    far, u_far = _person(db, seed, "FAR499", other.id)
    reader, u_reader = _person(db, seed, "READ499", dept.id)
    gone, u_gone = _person(db, seed, "GONE499", dept.id, active=False)
    cap_quyen(u_head.id, "purchase_request", scope="dept", read=True, approve=True)
    cap_quyen(u_far.id, "purchase_request", scope="dept", read=True, approve=True)
    cap_quyen(u_reader.id, "purchase_request", scope="dept", read=True)
    cap_quyen(u_gone.id, "purchase_request", scope="dept", read=True, approve=True)
    db.commit()

    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester="Người YC",
                                           requester_id=seed.emp_req_id, department=dept.name), seed.u_req_id)
    ids = {c["employee_id"] for c in candidates_for_row(db, PurchaseRequest, "purchase_request", pr.id)}
    assert head.id in ids, "trưởng phòng có quyền duyệt phạm vi phòng này"
    assert far.id not in ids, "duyệt phòng KHÁC thì không duyệt nổi phiếu này"
    assert reader.id not in ids, "chỉ có quyền xem, không có quyền duyệt"
    assert gone.id not in ids, "tài khoản đã khóa"

    before = db.query(PurchaseRequest).count()
    draft = candidates_for_draft(db, PurchaseRequest, "purchase_request",
                                 draft_fields(db, SimpleNamespace(id=seed.u_req_id), department_id=dept.id))
    assert {c["employee_id"] for c in draft} == ids, "màn tạo mới ra đúng danh sách như khi sửa"
    assert db.query(PurchaseRequest).count() == before, "bản ghi tạm không được để lại"


def test_system_admin_role_is_not_offered(db, seed, cap_quyen):
    from app.core.approver_candidates import candidates_for_row
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import UserRole
    dept = _dept(db, seed)
    boss, u_boss = _person(db, seed, "ADM499", dept.id)
    role = db.query(Role).filter(Role.code == "admin").first() or Role(code="admin", name="Quản trị")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity="purchase_request", scope="all", can_read=True, can_approve=True))
    db.add(UserRole(user_id=u_boss.id, role_id=role.id))
    db.commit()
    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester="Người YC",
                                           requester_id=seed.emp_req_id, department=dept.name), seed.u_req_id)
    ids = {c["employee_id"] for c in candidates_for_row(db, PurchaseRequest, "purchase_request", pr.id)}
    assert boss.id not in ids, "quản trị hệ thống không phải «trưởng phòng» — không đưa vào ô chọn"


def test_endpoints_exist_for_all_three_documents():
    for ctl, name in ((pr_ctl, "approver_candidates_"), (sr_ctl, "approver_candidates_"),
                      (po_ctl, "approver_candidates_")):
        assert hasattr(ctl, name) and hasattr(ctl, "approver_candidates_meta")


# ── Đại ca chốt 26/09: mặc định = Trưởng bộ phận, dùng chung bộ danh sách với ô TBP ──────────────

def test_default_approver_follows_head_until_user_picks_someone_else(db, seed):
    dept = _dept(db, seed)
    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester="Người YC",
                                           requester_id=seed.emp_req_id, department=dept.name,
                                           head_of_dept_id=seed.emp_tp_id), seed.u_req_id)
    assert pr.approver_employee_id == seed.emp_tp_id, "không chọn gì → mặc định bằng TBP"

    #  Đổi TBP khi người duyệt vẫn là TBP cũ → người duyệt đi theo.
    pr_service.update_pr(db, pr.id, PRUpdate(head_of_dept_id=seed.emp_nstm_id), seed.u_req_id)
    db.refresh(pr)
    assert pr.approver_employee_id == seed.emp_nstm_id

    #  Người lập chọn riêng một người khác TBP → đổi TBP không được đè lựa chọn đó.
    pr_service.update_pr(db, pr.id, PRUpdate(approver_employee_id=seed.emp_req_id), seed.u_req_id)
    pr_service.update_pr(db, pr.id, PRUpdate(head_of_dept_id=seed.emp_tp_id), seed.u_req_id)
    db.refresh(pr)
    assert pr.approver_employee_id == seed.emp_req_id


def test_sr_default_approver_is_the_head(db, seed):
    from app.modules.survey_request import service as sr_service
    dept = _dept(db, seed)
    s = sr_service.create_sr(db, SurveyRequestCreate(company_id=seed.company_id, requester="Người YC",
                                                     requester_id=seed.emp_req_id, department=dept.name,
                                                     head_of_dept_id=seed.emp_tp_id), seed.u_req_id)
    assert s.approver_employee_id == seed.emp_tp_id


def test_pr_candidate_list_is_the_same_set_as_the_head_box(db, seed, cap_quyen):
    dept = _dept(db, seed)
    head, u_head = _person(db, seed, "HEADB499", dept.id)
    cap_quyen(u_head.id, "purchase_request", scope="dept", read=True, approve=True)
    boss, u_boss = _person(db, seed, "ALLB499", dept.id)
    cap_quyen(u_boss.id, "purchase_request", scope="all", read=True, approve=True)
    db.commit()
    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester="Người YC",
                                           requester_id=seed.emp_req_id, department=dept.name), seed.u_req_id)
    same = pr_service.dept_head_candidates(db, pr)
    got = pr_ctl.approver_candidates_(pr.id, db=db, user=USER)
    import json
    items = json.loads(got.body)["data"]["items"] if hasattr(got, "body") else got["data"]["items"]
    assert [c["employee_id"] for c in items] == [c["employee_id"] for c in same]
    ids = {c["employee_id"] for c in items}
    assert head.id in ids and boss.id not in ids, "người duyệt MỌI phiếu (thu mua toàn quyền) không vào ô này"
