"""bao-CR-753 — chỉ người được chọn ở ô "Trưởng phòng phê duyệt" mới quyết phiếu (chủ hệ thống chốt 12/11/2026).

Ca prod: ĐMH PO00901 chờ duyệt, ô người duyệt = Lê Thị Ngọc Mi, nhưng tài khoản quản trị vẫn thấy và bấm được
Duyệt. Luật: phiếu có `approver_employee_id` thì ở bước chờ duyệt CHỈ nhân sự đó được Duyệt / Trả về / Từ chối
(ĐMH thêm Hủy duyệt sau khi duyệt) — kể cả quản trị. Ô trống → luật cũ. Bước khác không bị chặn.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.core.designated_approver import is_designated_approver
from app.modules.department.model import Department
from app.modules.purchase_order import controller as po_ctl
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_order.schema import RejectIn as PORejectIn
from app.modules.purchase_request import controller as pr_ctl
from app.modules.purchase_request import service as pr_service
from app.modules.purchase_request.model import PurchaseRequestItem
from app.modules.purchase_request.schema import ApproveIn, PRCreate, ReasonIn
from app.modules.purchase_request.schema import RejectIn as PRRejectIn
from app.modules.survey_request import controller as sr_ctl
from app.modules.survey_request.model import SurveyRequest
from app.modules.survey_request.schema import RejectIn as SRRejectIn
from app.modules.survey_request.schema import SurveyRequestCreate

#  Tài khoản quản trị không gắn nhân sự — có đủ quyền, nhưng không phải người được chọn.
ADMIN = SimpleNamespace(id=1, employee_id=0)


@pytest.fixture(autouse=True)
def _quiet(monkeypatch, cap_quyen):
    for ctl in (pr_ctl, po_ctl):
        monkeypatch.setattr(ctl, "trigger_notification", lambda **kw: None)
    monkeypatch.setattr(sr_ctl, "_notify", lambda *a, **kw: None)
    monkeypatch.setattr(pr_ctl, "_notify_assigned", lambda *a, **kw: None)
    monkeypatch.setattr(pr_ctl, "_in_approve_scope", lambda db, user, pid: True)
    monkeypatch.setattr(pr_ctl, "_can_return_requester", lambda db, user, pr: True)
    monkeypatch.setattr(pr_ctl.service, "dispatch_enabled", lambda: True)
    monkeypatch.setattr(pr_ctl, "_in_scope", lambda db, pid, u, action: pr_service.get_pr(db, pid))
    monkeypatch.setattr(sr_ctl, "_in_scope", lambda db, sid, u, action: db.get(SurveyRequest, sid))
    monkeypatch.setattr(po_ctl, "_in_scope", lambda db, pid, u, action: db.get(PurchaseOrder, pid))
    monkeypatch.setattr(sr_ctl.service, "auto_assign", lambda *a, **kw: None)
    for entity in ("purchase_request", "survey_request", "purchase_order"):
        cap_quyen(ADMIN.id, entity, scope="all", read=True, write=True, approve=True, cancel=True)


def _chosen(seed):
    """Người được chọn = trưởng phòng của seed (nhân sự `emp_tp_id`)."""
    return SimpleNamespace(id=2, employee_id=seed.emp_tp_id)


def _dept(db, seed):
    return db.get(Department, seed.dept_id)


def _po(db, seed, approver, status="submitted", code="PO-753"):
    dept = _dept(db, seed)
    po = PurchaseOrder(code=code, company_id=seed.company_id, department=dept.name, department_id=dept.id,
                       supplier_code="NCCA", supplier_name="NCC", order_date="2026-11-12", status=status,
                       approver_employee_id=approver, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(po)
    db.commit()
    return po


def _pr(db, seed, approver):
    dept = _dept(db, seed)
    pr = pr_service.create_pr(db, PRCreate(company_id=seed.company_id, requester="Người YC",
                                           requester_id=seed.emp_req_id, department=dept.name,
                                           head_of_dept_id=seed.emp_tp_id), seed.u_req_id)
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP01", product_name="Hàng", item_group="Nhãn",
                               qty=1, unit="cái", price=1, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    pr.approver_employee_id = approver
    pr.status = "submitted"
    db.commit()
    return pr


def _sr(db, seed, approver):
    from app.modules.survey_request import service as sr_service
    dept = _dept(db, seed)
    s = sr_service.create_sr(db, SurveyRequestCreate(company_id=seed.company_id, requester="Người YC",
                                                     requester_id=seed.emp_req_id, department=dept.name,
                                                     head_of_dept_id=seed.emp_tp_id), seed.u_req_id)
    s.approver_employee_id = approver
    s.status = "submitted"
    db.commit()
    return s


def _forbidden(fn, *a, **kw):
    with pytest.raises(HTTPException) as e:
        fn(*a, **kw)
    assert e.value.status_code == 403
    assert "người được chọn duyệt" in e.value.detail
    return e.value.detail


# ── Hàm dùng chung ───────────────────────────────────────────────────────────

def test_rule_empty_approver_keeps_old_behaviour():
    doc = SimpleNamespace(approver_employee_id=0)
    assert is_designated_approver(doc, ADMIN)


def test_rule_only_the_chosen_employee():
    doc = SimpleNamespace(approver_employee_id=7)
    assert is_designated_approver(doc, SimpleNamespace(id=5, employee_id=7))
    assert not is_designated_approver(doc, SimpleNamespace(id=7, employee_id=0)), "so ID NHÂN SỰ, không so user.id"
    assert not is_designated_approver(doc, ADMIN)


# ── ĐMH ──────────────────────────────────────────────────────────────────────

def test_po_admin_cannot_approve_reject_or_return_when_someone_else_is_chosen(db, seed):
    po = _po(db, seed, seed.emp_tp_id)
    detail = _forbidden(po_ctl.approve_po, po.id, BackgroundTasks(), db=db, user=ADMIN)
    assert "Chỉ " in detail
    _forbidden(po_ctl.reject_po, po.id, PORejectIn(reason="x"), BackgroundTasks(), db=db, user=ADMIN)
    _forbidden(po_ctl.return_po, po.id, PORejectIn(reason="x"), BackgroundTasks(), db=db, user=ADMIN)
    db.refresh(po)
    assert po.status == "submitted"


def test_po_chosen_approver_approves_and_only_they_can_unapprove(db, seed):
    po = _po(db, seed, seed.emp_tp_id)
    po_ctl.approve_po(po.id, BackgroundTasks(), db=db, user=_chosen(seed))
    db.refresh(po)
    assert po.status == "approved"
    _forbidden(po_ctl.unapprove_po, po.id, PORejectIn(reason="sửa"), db=db, user=ADMIN)
    po_ctl.unapprove_po(po.id, PORejectIn(reason="sửa"), db=db, user=_chosen(seed))
    db.refresh(po)
    assert po.status == "draft"


def test_po_without_chosen_approver_keeps_old_rule(db, seed):
    po = _po(db, seed, 0, code="PO-753-CU")
    po_ctl.approve_po(po.id, BackgroundTasks(), db=db, user=ADMIN)
    db.refresh(po)
    assert po.status == "approved"


def test_po_detail_flag(db, seed):
    po = _po(db, seed, seed.emp_tp_id)
    import json
    body = json.loads(po_ctl.get_po(po.id, db=db, user=ADMIN).body)
    assert body["data"]["can_decide"] is False


# ── YCMH ─────────────────────────────────────────────────────────────────────

def test_pr_admin_blocked_at_waiting_step(db, seed):
    pr = _pr(db, seed, seed.emp_tp_id)
    _forbidden(pr_ctl.approve_pr, pr.id, ApproveIn(), BackgroundTasks(), db=db, user=ADMIN)
    _forbidden(pr_ctl.reject_pr, pr.id, PRRejectIn(reason="x"), BackgroundTasks(), db=db, user=ADMIN)
    _forbidden(pr_ctl.return_pr, pr.id, ReasonIn(reason="x"), BackgroundTasks(), db=db, user=ADMIN)
    #  Nút "Từ chối" của v2 gọi đường hủy phiếu — quản trị có quyền Hủy cũng bị chặn ở bước chờ duyệt.
    _forbidden(pr_ctl.cancel_pr, pr.id, ReasonIn(reason="x"), BackgroundTasks(), db=db, user=ADMIN)
    db.refresh(pr)
    assert pr.status == "submitted"


def test_pr_chosen_approver_approves(db, seed):
    pr = _pr(db, seed, seed.emp_tp_id)
    pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=_chosen(seed))
    db.refresh(pr)
    assert pr.status == "approved"


def test_pr_other_steps_are_not_blocked(db, seed):
    """Sau duyệt (thu mua trả về lúc điều phối) — cột người duyệt không khóa nữa."""
    pr = _pr(db, seed, seed.emp_tp_id)
    pr.status = "approved"
    db.commit()
    pr_ctl._ensure_designated_if_waiting(db, pr, ADMIN)   # không ném lỗi


def test_pr_detail_flags_hide_buttons(db, seed):
    from app.modules.purchase_request import serializer as pr_ser
    pr = _pr(db, seed, seed.emp_tp_id)
    d = pr_ser._out(db, pr, ADMIN)
    assert d["can_decide"] is False and d["can_approve"] is False and d["can_return"] is False


def test_pr_without_chosen_approver_keeps_old_rule(db, seed):
    pr = _pr(db, seed, 0)
    pr_ctl.approve_pr(pr.id, ApproveIn(), BackgroundTasks(), db=db, user=ADMIN)
    db.refresh(pr)
    assert pr.status == "approved"


# ── YCBG ─────────────────────────────────────────────────────────────────────

def test_sr_admin_blocked_at_waiting_step(db, seed):
    s = _sr(db, seed, seed.emp_tp_id)
    _forbidden(sr_ctl.approve_, s.id, BackgroundTasks(), db=db, user=ADMIN)
    _forbidden(sr_ctl.reject_, s.id, SRRejectIn(reason="x"), BackgroundTasks(), db=db, user=ADMIN)
    _forbidden(sr_ctl.cancel_, s.id, SRRejectIn(reason="x"), BackgroundTasks(), db=db, user=ADMIN)
    db.refresh(s)
    assert s.status == "submitted"


def test_sr_chosen_approver_approves(db, seed):
    s = _sr(db, seed, seed.emp_tp_id)
    sr_ctl.approve_(s.id, BackgroundTasks(), db=db, user=_chosen(seed))
    db.refresh(s)
    assert s.status == "processing"


def test_sr_other_steps_are_not_blocked(db, seed):
    s = _sr(db, seed, seed.emp_tp_id)
    s.status = "processing"
    db.commit()
    sr_ctl._ensure_designated_if_waiting(db, s, ADMIN)


def test_sr_detail_flag(db, seed):
    from app.modules.survey_request import serializer as sr_ser
    s = _sr(db, seed, seed.emp_tp_id)
    d = sr_ser._out(db, s, ADMIN)
    assert d["can_decide"] is False and d["can_return_requester"] is False


# ── Tổng quan (bảng YCMH / ĐMH gần đây, duyệt nhanh) ─────────────────────────

def test_dashboard_recent_rows_carry_can_decide(db, seed, cap_quyen):
    import json

    from app.modules.dashboard import controller as dash_ctl
    for entity in ("purchase_request", "purchase_order"):
        cap_quyen(ADMIN.id, entity, scope="all", read=True)
    pr = _pr(db, seed, seed.emp_tp_id)
    po = _po(db, seed, seed.emp_tp_id)
    data = json.loads(dash_ctl.overview(db=db, user=ADMIN).body)["data"]
    pr_row = next(r for r in data["recent_prs"] if r["id"] == pr.id)
    po_row = next(r for r in data["recent_pos"] if r["id"] == po.id)
    assert pr_row["can_decide"] is False and po_row["can_decide"] is False
    mine = json.loads(dash_ctl.overview(db=db, user=_chosen(seed)).body)["data"]
    assert all(r["can_decide"] for r in mine["recent_prs"])
