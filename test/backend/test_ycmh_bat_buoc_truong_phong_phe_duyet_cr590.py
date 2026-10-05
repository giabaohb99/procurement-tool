"""bao-CR-590 — YCMH gửi duyệt BUỘC phải có «Trưởng phòng phê duyệt».

Đại ca chốt 05/10/2026. Hai tầng giữ luật:

1. Giao diện (v1 + v2) ghi THẬT người đang hiện ở ô xuống phiếu và chặn gửi duyệt khi
   không còn ai (kiểm ở `required-fields.test.ts` / `dept-head-display.test.ts`).
2. Máy chủ: có Trưởng bộ phận thì người duyệt mặc định là TBP; chốt cuối chặn phiếu
   không người duyệt, phòng khi ai đó đổi luật mặc định sau này.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.modules.purchase_request import controller as pr_ctl
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem

USER = SimpleNamespace(id=1)


@pytest.fixture(autouse=True)
def _quiet_and_allowed(monkeypatch, cap_quyen):
    monkeypatch.setattr(pr_ctl, "trigger_notification", lambda **kw: None)
    monkeypatch.setattr(pr_ctl, "_can_edit_own", lambda db, pr, user: True)
    cap_quyen(USER.id, "purchase_request", scope="all", read=True, create=True, write=True,
              approve=True)


def _draft(db, seed, *, head_id: int, approver_id: int = 0) -> PurchaseRequest:
    pr = PurchaseRequest(code="PYC-CR590", company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test",
                         department_id=seed.dept_id, head_of_dept_id=head_id,
                         approver_employee_id=approver_id, status="draft",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP01", product_name="Hàng Nhãn",
                               item_group="Nhãn", qty=10, unit="cái", price=1000,
                               created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    db.refresh(pr)
    return pr


def test_submit_without_approver_takes_department_head(db, seed):
    pr = _draft(db, seed, head_id=seed.emp_tp_id)

    pr_ctl.submit_pr(pr.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(pr)

    assert pr.status == "submitted"
    assert pr.approver_employee_id == seed.emp_tp_id


def test_submit_keeps_the_approver_the_requester_picked(db, seed):
    pr = _draft(db, seed, head_id=seed.emp_tp_id, approver_id=seed.emp_req_id)

    pr_ctl.submit_pr(pr.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(pr)

    assert pr.approver_employee_id == seed.emp_req_id


def test_submit_blocks_when_no_approver_can_be_resolved(db, seed, monkeypatch):
    #  Chốt cuối: giả lập luật mặc định không ra ai (vd sau này luật đổi) — phiếu KHÔNG
    #  được lên Chờ duyệt mà không có người duyệt, vì không ai được báo để duyệt nó.
    import app.core.print_signers as signers

    pr = _draft(db, seed, head_id=seed.emp_tp_id)
    monkeypatch.setattr(signers, "default_approver_to_head", lambda pr, old_head=0: None)

    with pytest.raises(HTTPException) as err:
        pr_ctl.submit_pr(pr.id, BackgroundTasks(), db=db, user=USER)
    db.refresh(pr)

    assert err.value.status_code == 400
    assert "Trưởng phòng phê duyệt" in err.value.detail
    assert pr.status == "draft"
