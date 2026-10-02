"""bao-CR-553 — YCTT thêm ô «Trưởng bộ phận» (in ở dòng «Trưởng phòng ban/bộ phận» của bản in).

Đại ca chốt 01/10/2026: chị Mi duyệt nhưng bản in nội bộ phải ghi anh Dững ở dòng đó; ô Giám đốc
và ô TP duyệt giữ nguyên. 02/10: bỏ ô «Người duyệt», chỉ giữ ô này; gửi duyệt báo như cũ.
"""
import json

import pytest
from pydantic import ValidationError

from app.modules.payment_request import controller as ctl
from app.modules.payment_request import service
from app.modules.payment_request.model import PaymentRequest
from app.modules.payment_request.schema import LineIn, PRequestCreate, PRequestUpdate
from app.modules.user.model import User


def _create(db, seed, **extra) -> PaymentRequest:
    data = PRequestCreate(supplier_code="NX", company_id=seed.company_id, request_date="2026-10-01",
                          lines=[LineIn(po_code="PO-CR553", invoice_no="HD1", amount=1000)], **extra)
    return service.create_requests(db, data, seed.u_req_id)[0]


def test_create_keeps_head_and_fills_head_name(db, seed):
    req = _create(db, seed, head_of_dept_id=seed.emp_tp_id)
    assert (req.head_of_dept_id, req.head_of_dept) == (seed.emp_tp_id, "Trưởng Phòng")


def test_create_without_head_leaves_it_empty(db, seed):
    req = _create(db, seed)
    assert (req.head_of_dept_id, req.head_of_dept) == (0, "")


def test_update_draft_changes_head(db, seed):
    req = _create(db, seed)
    service.update_request(db, req.id, PRequestUpdate(head_of_dept_id=seed.emp_backup_id), seed.u_req_id)
    assert db.get(PaymentRequest, req.id).head_of_dept == "NSTM Dự Phòng"


def test_head_name_is_capped_at_255():
    with pytest.raises(ValidationError):
        PRequestUpdate(head_of_dept="x" * 256)


def test_submit_notifies_approvers_as_before(db, seed, monkeypatch):
    sent = []
    monkeypatch.setattr(ctl, "trigger_notification", lambda **kw: sent.append(kw))
    ctl._notify_pay(db, None, _create(db, seed, head_of_dept_id=seed.emp_tp_id), "pay_submitted")
    assert "recipient_ids" not in sent[0], "ô Trưởng bộ phận chỉ để in, không đổi người được báo"


def test_print_uses_head_of_dept_over_creator_manager(db, seed, cap_quyen):
    req = _create(db, seed, head_of_dept_id=seed.emp_tp_id)
    cap_quyen(seed.u_req_id, "payment_request", scope="all", read=True, print=True)
    resp = ctl.print_(req.id, db=db, user=db.get(User, seed.u_req_id))
    assert json.loads(resp.body)["data"]["dept_manager"] == "Trưởng Phòng"


def test_department_managers_lists_department_heads(db, seed):
    from app.modules.department.model import Department
    db.get(Department, seed.dept_id).manager_id = seed.emp_tp_id
    db.commit()
    resp = ctl.department_managers_(db=db, user=db.get(User, seed.u_req_id))
    ids = {r["employee_id"] for r in json.loads(resp.body)["data"]["items"]}
    assert seed.emp_tp_id in ids
