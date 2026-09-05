"""Duyệt dấu PHA 5 — nối runtime luồng duyệt (approval_bridge).

- Cờ TẮT (mặc định) / bật mà chưa khai luồng → gửi duyệt vẫn ĐƯỜNG CŨ (Chờ duyệt,
  không mở phiên) — không đổi hành vi đang chạy.
- Bộ máy gọi ngược đúng: hết bước → Đã duyệt; từ chối → Từ chối; trả → Yêu cầu
  chỉnh sửa; rút → Nháp.
- Đang chạy phiên nhiều bước thì KHÓA nút duyệt cổng-1 (block_legacy_path).
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.approval.flow_model import ApprovalSwitch
from app.modules.approval.instance_model import INSTANCE_RUNNING, ApprovalInstance
from app.modules.attachment.model import FileLink
from app.modules.employee.model import Employee
from app.modules.seal_request import approval_bridge as bridge
from app.modules.seal_request import model as m
from app.modules.seal_request.schema import SealRequestCreate
from app.modules.seal_request.service import create_seal_request, submit_seal_request


def _actor(db, *, uid=101):
    emp = Employee(code="NV900", full_name="Người Tạo", email="c@dego.vn",
                   department_id=7, company_id=3)
    db.add(emp)
    db.flush()
    return SimpleNamespace(id=uid, employee_id=emp.id, email="c@dego.vn")


def _draft_ready(db, actor):
    st = m.SealType(name="Dấu tròn công ty")
    db.add(st)
    db.flush()
    req = create_seal_request(db, SealRequestCreate(purpose="Đóng dấu HĐ", seal_type_id=st.id),
                              actor, submit=False)
    db.add(FileLink(file_id=1, entity="seal_request", entity_id=req.id, doc_type="signed_doc"))
    db.flush()
    return req


def _pending(db):
    actor = _actor(db)
    req = _draft_ready(db, actor)
    req.status = m.SEAL_PENDING
    db.flush()
    return req


def _switch_on(db):
    db.add(ApprovalSwitch(entity="seal_request", is_enabled=True))
    db.flush()


# ── Gửi duyệt: cờ tắt / chưa khai luồng ────────────────────────────────────────

def test_submit_uses_legacy_when_engine_off(db):
    actor = _actor(db)
    req = _draft_ready(db, actor)
    submit_seal_request(db, req, actor)
    assert req.status == m.SEAL_PENDING
    assert bridge.running_instance(db, req.id) is None


def test_submit_falls_back_when_switch_on_but_no_flow(db):
    _switch_on(db)  # bật cờ nhưng CHƯA khai luồng nào cho seal_request
    actor = _actor(db)
    req = _draft_ready(db, actor)
    submit_seal_request(db, req, actor)
    assert req.status == m.SEAL_PENDING
    assert bridge.running_instance(db, req.id) is None


# ── Bộ máy gọi ngược khi phiên kết thúc ────────────────────────────────────────

def test_on_approved_marks_approved(db):
    req = _pending(db)
    bridge._on_approved(db, req.id, SimpleNamespace(updated_by=5, finish_reason=""))
    db.refresh(req)
    assert req.status == m.SEAL_APPROVED


def test_on_rejected_marks_rejected_with_reason(db):
    req = _pending(db)
    bridge._on_rejected(db, req.id, SimpleNamespace(updated_by=5, finish_reason="Sai mẫu dấu"))
    db.refresh(req)
    assert req.status == m.SEAL_REJECTED
    assert "Sai mẫu dấu" in req.note


def test_on_returned_marks_returned(db):
    req = _pending(db)
    bridge._on_returned(db, req.id, SimpleNamespace(updated_by=5, finish_reason="Thiếu chữ ký"))
    db.refresh(req)
    assert req.status == m.SEAL_RETURNED
    assert "Thiếu chữ ký" in req.note


def test_on_withdrawn_marks_draft(db):
    req = _pending(db)
    bridge._on_withdrawn(db, req.id, SimpleNamespace(updated_by=5, finish_reason=""))
    db.refresh(req)
    assert req.status == m.SEAL_DRAFT


# ── Chốt chặn đường cũ (cổng 1) ────────────────────────────────────────────────

def test_block_legacy_path_no_running_instance_is_noop(db):
    req = _pending(db)
    bridge.block_legacy_path(db, req)  # không có phiên → không ném


def test_block_legacy_path_raises_when_instance_running(db):
    req = _pending(db)
    db.add(ApprovalInstance(entity="seal_request", entity_id=req.id,
                            status=INSTANCE_RUNNING, flow_id=1))
    db.flush()
    with pytest.raises(HTTPException):
        bridge.block_legacy_path(db, req)


def test_entity_context_carries_routing_fields(db):
    req = _pending(db)
    ctx = bridge.entity_context(req)
    assert ctx["id"] == req.id
    assert set(ctx) >= {"id", "company_id", "department_id", "requester_id"}
