"""Duyệt dấu (Yêu cầu đóng dấu) — luồng 2 cổng ở tầng service.

Tạo → gửi duyệt (BẮT BUỘC ≥1 công ty + TBP + ≥1 chứng từ) → TBP duyệt → Văn thư
hoàn thành (đóng dấu). Một phiếu gắn NHIỀU công ty (bảng nối).
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.attachment.model import FileLink
from app.modules.employee.model import Employee
from app.modules.seal_request import model as m
from app.modules.seal_request.schema import CompleteSealIn, ReasonIn, SealRequestCreate
from app.modules.seal_request.service import (
    approve_seal,
    complete_seal,
    create_seal_request,
    get_company_ids,
    reject_seal,
    return_seal,
    serialize_seal_request,
    submit_seal_request,
)

CTY_A, CTY_B, TBP_UID = 11, 22, 500


def _actor(db, *, uid=101):
    emp = Employee(code="NV900", full_name="Lâm Bích Dư", email="lbd@dego.vn",
                   phone="0939858582", position="Staff", department_id=7, company_id=3)
    db.add(emp)
    db.flush()
    return SimpleNamespace(id=uid, employee_id=emp.id, email="lbd@dego.vn")


def _attach(db, req_id):
    """Giả lập NSYC đã upload 1 chứng từ."""
    db.add(FileLink(file_id=1, entity="seal_request", entity_id=req_id, doc_type="signed_doc"))
    db.flush()


def _payload(**over):
    data = dict(purpose="Duyệt dấu Hợp đồng Hồ Gia - Dego",
                company_ids=[CTY_A, CTY_B], first_approver_id=TBP_UID)
    data.update(over)
    return SealRequestCreate(**data)


def _ready(db, actor):
    req = create_seal_request(db, _payload(), actor, submit=False)
    _attach(db, req.id)
    return req


def test_serialize_handles_datetime_created_at(db):
    #  Regression: model_validate(req) từng vỡ 500 vì created_at là datetime.
    actor = _actor(db)
    req = create_seal_request(db, _payload(), actor, submit=False)
    out = serialize_seal_request(db, req)
    assert isinstance(out["created_at"], str)
    assert out["status_label"] == "Nháp"
    assert out["company_ids"] == [CTY_A, CTY_B]


def test_create_draft_generates_dd_code_and_companies(db):
    actor = _actor(db)
    req = create_seal_request(db, _payload(), actor, submit=False)
    assert req.status == m.SEAL_DRAFT
    assert req.code.startswith("DD")
    assert req.company_id == CTY_A                    # công ty CHÍNH = đầu danh sách
    assert get_company_ids(db, req.id) == [CTY_A, CTY_B]
    assert req.requester == "Lâm Bích Dư"


def test_submit_requires_company_approver_and_doc(db):
    actor = _actor(db)
    # Thiếu công ty → chặn.
    req = create_seal_request(db, _payload(company_ids=[]), actor, submit=False)
    _attach(db, req.id)
    with pytest.raises(HTTPException):
        submit_seal_request(db, req, actor)
    # Thiếu TBP → chặn.
    req2 = create_seal_request(db, _payload(first_approver_id=0), actor, submit=False)
    _attach(db, req2.id)
    with pytest.raises(HTTPException):
        submit_seal_request(db, req2, actor)
    # Thiếu chứng từ → chặn.
    req3 = create_seal_request(db, _payload(), actor, submit=False)
    with pytest.raises(HTTPException):
        submit_seal_request(db, req3, actor)
    assert req3.status == m.SEAL_DRAFT


def test_full_flow_two_gates(db):
    actor = _actor(db)
    req = _ready(db, actor)
    submit_seal_request(db, req, actor)
    assert req.status == m.SEAL_PENDING
    approve_seal(db, req, actor)          # cổng 1: TBP
    assert req.status == m.SEAL_APPROVED
    complete_seal(db, req, CompleteSealIn(note="Đóng dấu 2 bản"), actor)  # cổng 2: Văn thư
    assert req.status == m.SEAL_COMPLETED
    assert "Đã đóng dấu xong" in req.note
    assert "Đóng dấu 2 bản" in req.note


def test_return_then_resubmit(db):
    actor = _actor(db)
    req = _ready(db, actor)
    submit_seal_request(db, req, actor)
    return_seal(db, req, ReasonIn(reason="Thiếu chữ ký trang 2"), actor)
    assert req.status == m.SEAL_RETURNED
    assert "Thiếu chữ ký trang 2" in req.note
    submit_seal_request(db, req, actor)
    assert req.status == m.SEAL_PENDING


def test_reject_locks(db):
    actor = _actor(db)
    req = _ready(db, actor)
    submit_seal_request(db, req, actor)
    reject_seal(db, req, ReasonIn(reason="Không cần đóng dấu"), actor)
    assert req.status == m.SEAL_REJECTED
    with pytest.raises(HTTPException):
        approve_seal(db, req, actor)


def test_clerk_can_return_from_approved(db):
    actor = _actor(db)
    req = _ready(db, actor)
    submit_seal_request(db, req, actor)
    approve_seal(db, req, actor)
    return_seal(db, req, ReasonIn(reason="Chụp lại chữ ký rõ hơn"), actor)
    assert req.status == m.SEAL_RETURNED


def test_complete_only_from_approved(db):
    actor = _actor(db)
    req = _ready(db, actor)
    submit_seal_request(db, req, actor)
    with pytest.raises(HTTPException):
        complete_seal(db, req, CompleteSealIn(), actor)
