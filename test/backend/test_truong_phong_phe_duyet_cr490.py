"""bao-CR-490 — «Trưởng phòng phê duyệt» + hai người ký chọn được trên bản in nội bộ.

Đại ca chốt 25/09/2026: ba chứng từ YCMH · YCBG · ĐMH có cột `approver_employee_id` = NHÂN SỰ
thực bấm Duyệt ở chặng trưởng phòng; bản in nội bộ cho chọn ô ký hiện người duyệt hay trưởng
phòng theo hồ sơ phòng ban (`Department.manager_id`); mẫu thuế để trống. Bài này canh:
  · bấm Duyệt ở cả ba đường API là cột được ghi; ĐMH hủy duyệt thì xóa;
  · serializer trả `approver_employee_id/_name` + `dept_head_*`; phiếu cũ (cột 0) không vỡ;
  · bản in YCMH/ĐMH: có cột thì tên người duyệt tra theo NHÂN SỰ; không có thì lùi về nhật ký.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks

from app.core.audit import record
from app.core.print_signers import approver_fields, department_head_block, stamp_approver
from app.modules.department.model import Department
from app.modules.purchase_order import controller as po_ctl
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_order.schema import RejectIn
from app.modules.purchase_request import controller as pr_ctl
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import ApproveIn
from app.modules.survey_request import controller as sr_ctl
from app.modules.survey_request.model import SurveyRequest
from app.modules.user.model import User

USER = SimpleNamespace(id=1)


def _tp_user_id(db) -> int:
    return db.query(User).filter(User.email == "DEMOTP").first().id


@pytest.fixture(autouse=True)
def _quiet(monkeypatch, cap_quyen):
    for module in (pr_ctl, po_ctl):
        monkeypatch.setattr(module, "trigger_notification", lambda **kw: None)
    monkeypatch.setattr(pr_ctl, "_notify_assigned", lambda *a, **kw: None)
    monkeypatch.setattr(pr_ctl, "_in_approve_scope", lambda db, user, pid: True)
    monkeypatch.setattr(pr_ctl.service, "dispatch_enabled", lambda: True)
    monkeypatch.setattr(sr_ctl, "_notify", lambda *a, **kw: None)
    monkeypatch.setattr(sr_ctl, "_in_scope", lambda db, sid, u, action: None)
    monkeypatch.setattr(po_ctl, "_in_scope", lambda db, pid, u, action: None)
    for entity in ("purchase_request", "survey_request", "purchase_order"):
        cap_quyen(USER.id, entity, scope="all", read=True, write=True, approve=True)


@pytest.fixture
def dept_with_head(db, seed):
    """Phòng lập phiếu có trưởng phòng theo hồ sơ = DEMOTP; người bấm Duyệt là USER (= TESTREQ)."""
    dept = db.get(Department, seed.dept_id) if hasattr(seed, "dept_id") else \
        db.query(Department).filter(Department.code == "DEPT01").first()
    dept.manager_id = seed.emp_tp_id
    db.commit()
    return dept


def _pr(db, seed, dept, code="PYC-490"):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department=dept.name, department_id=dept.id,
                         head_of_dept_id=seed.emp_tp_id, status="submitted",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP01", product_name="Hàng", item_group="Nhãn",
                               qty=1, unit="cái", price=1, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    db.refresh(pr)
    return pr


def test_helpers_read_employee_of_user_and_department_head(db, seed, dept_with_head):
    pr = _pr(db, seed, dept_with_head)
    stamp_approver(db, pr, _tp_user_id(db))
    assert pr.approver_employee_id == seed.emp_tp_id
    head = department_head_block(db, dept_with_head.id)
    assert head["employee_id"] == seed.emp_tp_id and head["name"] == "Trưởng Phòng"
    fields = approver_fields(db, pr)
    assert fields["approver_employee_name"] == "Trưởng Phòng"
    assert fields["dept_head_name"] == "Trưởng Phòng"
    assert department_head_block(db, 0) == {"employee_id": 0, "name": "", "signature": ""}


def test_pr_approve_stamps_the_approver_and_print_uses_the_employee(db, seed, dept_with_head):
    pr = _pr(db, seed, dept_with_head)
    approver_emp = db.get(User, USER.id).employee_id

    pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=USER)
    db.refresh(pr)

    assert pr.approver_employee_id == approver_emp
    out = pr_ctl._out(db, pr)
    assert out["approver_employee_id"] == approver_emp
    assert out["approver_employee_name"] == "Người YC"
    assert out["dept_head_name"] == "Trưởng Phòng", "trưởng phòng theo hồ sơ khác người bấm Duyệt"
    assert out["approver_name"] == "Người YC"


def test_pr_print_falls_back_to_audit_for_old_tickets(db, seed, dept_with_head):
    pr = _pr(db, seed, dept_with_head, "PYC-490-OLD")
    pr.status = "approved"
    db.commit()
    record(db, _tp_user_id(db), "purchase_request", pr.id, "approved")
    out = pr_ctl._approval_signers(db, pr)
    assert out["approver_name"] == "Trưởng Phòng", "cột 0 → tra nhật ký như trước CR-490"


def test_sr_approve_stamps_the_approver(db, seed, dept_with_head):
    s = SurveyRequest(code="YCBG-490", company_id=seed.company_id, requester="Người YC",
                      requester_id=seed.emp_req_id, department=dept_with_head.name,
                      department_id=dept_with_head.id, status="submitted",
                      created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(s)
    db.commit()
    sr_ctl.approve_(s.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(s)
    assert s.approver_employee_id == db.get(User, USER.id).employee_id
    out = sr_ctl._out(db, s)
    assert out["approver_employee_name"] == "Người YC" and out["dept_head_name"] == "Trưởng Phòng"


def test_po_approve_stamps_and_unapprove_clears(db, seed, dept_with_head):
    po = PurchaseOrder(code="PO-490", company_id=seed.company_id, department=dept_with_head.name,
                       department_id=dept_with_head.id, supplier_code="NCCA", supplier_name="NCC",
                       order_date="2026-09-01", status="submitted",
                       created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(po)
    db.commit()
    po_ctl.approve_po(po.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(po)
    assert po.approver_employee_id == db.get(User, USER.id).employee_id
    signers = po_ctl.resolve_print_signers(db, po)
    assert signers["approver_name"] == "Người YC"
    assert signers["dept_head_name"] == "Trưởng Phòng"

    po_ctl.unapprove_po(po.id, RejectIn(reason="sai giá"), db=db, user=USER)
    db.refresh(po)
    assert po.approver_employee_id == 0
