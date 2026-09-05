"""Duyệt dấu (Yêu cầu đóng dấu) — luồng 2 cổng ở tầng service.

Tạo → gửi duyệt (BẮT BUỘC ≥1 chứng từ chữ ký sống) → TBP duyệt → Văn thư hoàn thành
(đóng dấu). Cùng khuôn test với Đặt xe.
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
    reject_seal,
    return_seal,
    serialize_seal_request,
    submit_seal_request,
)


def _actor(db, *, uid=101):
    emp = Employee(code="NV900", full_name="Lâm Bích Dư", email="lbd@dego.vn",
                   phone="0939858582", position="Staff", department_id=7, company_id=3)
    db.add(emp)
    db.flush()
    return SimpleNamespace(id=uid, employee_id=emp.id, email="lbd@dego.vn")


def _seal_type(db):
    st = m.SealType(name="Dấu tròn công ty")
    db.add(st)
    db.flush()
    return st


def _attach_signed(db, req_id):
    """Giả lập NSYC đã upload 1 chứng từ có chữ ký sống (doc_type=signed_doc)."""
    db.add(FileLink(file_id=1, entity="seal_request", entity_id=req_id, doc_type="signed_doc"))
    db.flush()


def _payload(st_id, **over):
    data = dict(purpose="Duyệt dấu Hợp đồng Hồ Gia - Dego", seal_type_id=st_id, copies=2)
    data.update(over)
    return SealRequestCreate(**data)


def test_serialize_handles_datetime_created_at(db):
    #  Regression: SealRequestResponse.model_validate(req) từng vỡ 500 vì created_at
    #  là datetime mà schema khai `str | None` — thiếu field_validator chuyển ISO.
    actor = _actor(db)
    st = _seal_type(db)
    req = create_seal_request(db, _payload(st.id), actor, submit=False)
    out = serialize_seal_request(db, req)
    assert isinstance(out["created_at"], str)
    assert out["status_label"] == "Nháp"


def test_create_draft_generates_dd_code(db):
    actor = _actor(db)
    st = _seal_type(db)
    req = create_seal_request(db, _payload(st.id), actor, submit=False)
    assert req.status == m.SEAL_DRAFT
    assert req.code.startswith("DD")
    assert req.company_id == 3          # auto-fill từ hồ sơ người tạo
    assert req.requester == "Lâm Bích Dư"


def test_submit_requires_signed_doc(db):
    actor = _actor(db)
    st = _seal_type(db)
    req = create_seal_request(db, _payload(st.id), actor, submit=False)
    #  Chưa đính kèm chứng từ chữ ký sống → không gửi duyệt được.
    with pytest.raises(HTTPException):
        submit_seal_request(db, req, actor)
    assert req.status == m.SEAL_DRAFT


def test_full_flow_two_gates(db):
    actor = _actor(db)
    st = _seal_type(db)
    req = create_seal_request(db, _payload(st.id), actor, submit=False)
    _attach_signed(db, req.id)

    submit_seal_request(db, req, actor)
    assert req.status == m.SEAL_PENDING

    approve_seal(db, req, actor)          # cổng 1: TBP
    assert req.status == m.SEAL_APPROVED

    complete_seal(db, req, CompleteSealIn(copies_done=2, note="Đóng dấu 2 bản"), actor)  # cổng 2: Văn thư
    assert req.status == m.SEAL_COMPLETED
    assert req.copies == 2
    assert "Đã đóng dấu 2 bản" in req.note


def test_return_then_resubmit(db):
    actor = _actor(db)
    st = _seal_type(db)
    req = create_seal_request(db, _payload(st.id), actor, submit=False)
    _attach_signed(db, req.id)
    submit_seal_request(db, req, actor)

    return_seal(db, req, ReasonIn(reason="Thiếu chữ ký trang 2"), actor)
    assert req.status == m.SEAL_RETURNED
    assert "Thiếu chữ ký trang 2" in req.note
    #  Sửa xong gửi lại → về Chờ duyệt.
    submit_seal_request(db, req, actor)
    assert req.status == m.SEAL_PENDING


def test_reject_locks(db):
    actor = _actor(db)
    st = _seal_type(db)
    req = create_seal_request(db, _payload(st.id), actor, submit=False)
    _attach_signed(db, req.id)
    submit_seal_request(db, req, actor)
    reject_seal(db, req, ReasonIn(reason="Không cần đóng dấu"), actor)
    assert req.status == m.SEAL_REJECTED
    #  Đã từ chối thì không duyệt lại được.
    with pytest.raises(HTTPException):
        approve_seal(db, req, actor)


def test_clerk_can_return_from_approved(db):
    #  Văn thư yêu cầu chỉnh sửa (phiếu ĐÃ DUYỆT) — vd chụp lại chữ ký rõ hơn.
    actor = _actor(db)
    st = _seal_type(db)
    req = create_seal_request(db, _payload(st.id), actor, submit=False)
    _attach_signed(db, req.id)
    submit_seal_request(db, req, actor)
    approve_seal(db, req, actor)
    return_seal(db, req, ReasonIn(reason="Chụp lại chữ ký rõ hơn"), actor)
    assert req.status == m.SEAL_RETURNED


def test_complete_only_from_approved(db):
    actor = _actor(db)
    st = _seal_type(db)
    req = create_seal_request(db, _payload(st.id), actor, submit=False)
    _attach_signed(db, req.id)
    submit_seal_request(db, req, actor)
    #  Chưa duyệt (đang Chờ duyệt) → Văn thư chưa được đóng dấu hoàn thành.
    with pytest.raises(HTTPException):
        complete_seal(db, req, CompleteSealIn(), actor)
