"""bao-CR-554 — (1) phiếu khảo sát chưa duyệt cả phiếu khi còn dòng chưa quyết; (2) «Trả về» dùng
được cả khi phiếu ĐÃ DUYỆT ở Khảo sát · YCBG · YCMH (ĐMH đã có «Hủy duyệt» từ CR-108).

Đại ca chốt 02/10/2026: dòng «xong» = Đã duyệt hoặc Không duyệt; quản lý hủy duyệt thì phiếu về
Bị trả lại để nhân viên sửa rồi gửi lại.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.modules.purchase_request import controller as pr_ctl
from app.modules.purchase_request import service as pr_service
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import ReasonIn, RejectIn
from app.modules.survey import controller as sv_ctl
from app.modules.survey import service as sv_service
from app.modules.survey.model import Survey, SurveyProductLine, SurveySupplierLine
from app.modules.survey_request import controller as sr_ctl
from app.modules.survey_request import service as sr_service
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine

USER = SimpleNamespace(id=1)


@pytest.fixture(autouse=True)
def _world(monkeypatch, cap_quyen):
    for module in (pr_ctl, sv_ctl):
        monkeypatch.setattr(module, "trigger_notification", lambda **kw: None)
    monkeypatch.setattr(sr_ctl, "_notify", lambda *a, **kw: None)
    monkeypatch.setattr(sv_ctl, "_sync_ycks_options", lambda *a, **kw: None)
    for entity in ("purchase_request", "survey", "survey_request"):
        cap_quyen(USER.id, entity, scope="all", read=True, write=True, approve=True, cancel=True)


# ── Khảo sát ────────────────────────────────────────────────────────────────

def _survey(db, status="submitted", lines=()):
    s = Survey(code=f"KS-554-{status}-{len(lines)}", survey_type="combined", status=status, item_group="Nhãn")
    db.add(s)
    db.flush()
    for i, state in enumerate(lines):
        model = SurveySupplierLine if i % 2 else SurveyProductLine
        db.add(model(survey_id=s.id, supplier_code="NX", line_approve=state))
    db.commit()
    db.refresh(s)
    return s


@pytest.mark.parametrize("state", ["Chờ duyệt", "Thiếu thông tin", ""])
def test_survey_with_undecided_line_cannot_be_approved(db, state):
    s = _survey(db, lines=("Đã duyệt", state))
    with pytest.raises(HTTPException) as error:
        sv_ctl.approve_(s.id, BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 400 and "1 dòng" in error.value.detail
    db.refresh(s)
    assert s.status == "submitted"


def test_survey_with_all_lines_decided_is_approved(db):
    s = _survey(db, lines=("Đã duyệt", "Không duyệt", "Đã duyệt"))
    sv_ctl.approve_(s.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(s)
    assert s.status == "approved"


def test_survey_count_undecided_covers_both_tables(db):
    s = _survey(db, lines=("Chờ duyệt", "Chờ duyệt", "Đã duyệt"))
    assert sv_service.count_undecided_lines(db, s.id) == 2


def test_approved_survey_can_be_returned(db):
    s = _survey(db, status="approved")
    sv_ctl.reject_(s.id, RejectIn(reason="Giá chưa đúng"), BackgroundTasks(), db=db, user=USER)
    db.refresh(s)
    assert s.status == "rejected"


@pytest.mark.parametrize("status", ["draft", "rejected", "cancelled"])
def test_survey_return_blocked_outside_submitted_or_approved(db, status):
    s = _survey(db, status=status)
    with pytest.raises(HTTPException) as error:
        sv_ctl.reject_(s.id, RejectIn(reason="x"), BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 400


# ── YCBG ────────────────────────────────────────────────────────────────────

def _sr(db, seed, status="processing", assignee="DEMONV"):
    sr = SurveyRequest(code=f"YCBG-554-{status}", department="Phòng Test", status=status,
                       created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(sr)
    db.flush()
    db.add(SurveyRequestLine(survey_request_id=sr.id, item_group="Nhãn", assignee=assignee,
                             received_date="2026-10-01"))
    db.commit()
    db.refresh(sr)
    return sr


def test_processing_sr_can_be_returned_and_assignees_cleared(db, seed):
    sr = _sr(db, seed)
    sr_ctl.reject_(sr.id, RejectIn(reason="Sai phân loại"), BackgroundTasks(), db=db, user=USER)
    db.refresh(sr)
    assert sr.status == "rejected"
    line = sr_service.lines_of(db, sr.id)[0]
    assert (line.assignee, line.received_date) == ("", "")


def test_sr_with_completed_line_cannot_be_returned(db, seed):
    sr = _sr(db, seed)
    sr_service.lines_of(db, sr.id)[0].is_completed = True
    db.commit()
    with pytest.raises(HTTPException) as error:
        sr_ctl.reject_(sr.id, RejectIn(reason="x"), BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 400
    assert sr_ctl._out(db, sr, USER)["can_return_requester"] is False


def test_submitted_sr_keeps_assignee_when_returned(db, seed):
    sr = _sr(db, seed, status="submitted")
    assert sr_ctl._out(db, sr, USER)["can_return_requester"] is True
    sr_ctl.reject_(sr.id, RejectIn(reason="x"), BackgroundTasks(), db=db, user=USER)
    assert sr_service.lines_of(db, sr.id)[0].assignee == "DEMONV"


# ── YCMH ────────────────────────────────────────────────────────────────────

def _pr(db, seed, status="approved", line_status="no_po"):
    pr = PurchaseRequest(code=f"PYC-554-{status}-{line_status}", company_id=seed.company_id,
                         requester="Người YC", requester_id=seed.emp_req_id, department="Phòng Test",
                         head_of_dept_id=seed.emp_req_id, status=status,
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP01", product_name="Hàng", item_group="Nhãn",
                               qty=1, unit="cái", price=1, line_status=line_status, assignee="DEMONV",
                               created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    db.refresh(pr)
    return pr


def test_approver_can_return_approved_pr_without_po(db, seed, monkeypatch):
    monkeypatch.setattr(pr_ctl, "_in_approve_scope", lambda db, user, pid: True)
    pr = _pr(db, seed)
    assert pr_ctl._out(db, pr, USER)["can_return"] is True
    pr_ctl.return_pr(pr.id, ReasonIn(reason="Sửa số lượng"), BackgroundTasks(), db=db, user=USER)
    db.refresh(pr)
    assert pr.status == "rejected"
    assert pr_service.items_of(db, pr.id)[0].assignee == ""


@pytest.mark.parametrize("line_status", ["not_ordered", "ordered", "received"])
def test_pr_with_po_line_cannot_be_returned(db, seed, line_status):
    pr = _pr(db, seed, line_status=line_status)
    assert pr_ctl._out(db, pr, USER)["can_return"] is False
    with pytest.raises(HTTPException) as error:
        pr_ctl.return_pr(pr.id, ReasonIn(reason="x"), BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 400
    db.refresh(pr)
    assert pr.status == "approved"


def test_pr_cancelled_line_does_not_block_return(db, seed):
    pr = _pr(db, seed, status="dispatched", line_status="cancelled")
    assert pr_service.can_return_requester(db, pr) is True
