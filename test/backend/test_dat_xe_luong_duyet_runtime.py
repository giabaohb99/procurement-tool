"""Phase 6.1 Đặt xe — nối runtime luồng duyệt (approval_bridge).

Ba chỗ dễ sai nhất:
- Cờ TẮT (mặc định) hoặc bật mà chưa khai luồng → gửi duyệt vẫn đi ĐƯỜNG CŨ
  (phiếu Chờ duyệt, không mở phiên nào) — không được đổi hành vi thứ đang chạy.
- Bộ máy gọi ngược đúng: hết bước → Đã duyệt; từ chối → Từ chối; trả lại → Yêu cầu
  chỉnh sửa; rút → Nháp.
- Đang chạy phiên nhiều bước thì KHÓA ba nút duyệt một bước (block_legacy_path).
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.approval.flow_model import ApprovalSwitch
from app.modules.approval.instance_model import INSTANCE_RUNNING, ApprovalInstance
from app.modules.employee.model import Employee
from app.modules.vehicle_booking import approval_bridge as bridge
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.schema import VehicleBookingCreate
from app.modules.vehicle_booking.service import create_booking


def _actor(db, *, uid=101):
    emp = Employee(code="NV900", full_name="Người Tạo", email="c@dego.vn",
                   department_id=7, company_id=3)
    db.add(emp)
    db.flush()
    return SimpleNamespace(id=uid, employee_id=emp.id, email="c@dego.vn")


def _payload(**over):
    data = dict(request_type=1, purpose="Đi công tác", start_location="VP",
                end_location="Q7", start_time="2026-09-01T08:00",
                end_time="2026-09-01T10:00", passenger_count=1)
    data.update(over)
    return VehicleBookingCreate(**data)


def _pending(db):
    actor = _actor(db)
    b = create_booking(db, _payload(), actor, submit=False)
    b.status = m.BK_PENDING
    db.flush()
    return b


def _switch_on(db):
    db.add(ApprovalSwitch(entity="vehicle_booking", is_enabled=True))
    db.flush()


# ─────────────────────── Gửi duyệt: cờ tắt / chưa khai luồng ───────────────────────

def test_submit_uses_legacy_when_engine_off(db):
    actor = _actor(db)
    b = create_booking(db, _payload(), actor, submit=True)
    assert b.status == m.BK_PENDING
    assert bridge.running_instance(db, b.id) is None  # không mở phiên nào


def test_submit_falls_back_when_switch_on_but_no_flow(db):
    _switch_on(db)  # bật cờ nhưng CHƯA khai luồng nào cho vehicle_booking
    actor = _actor(db)
    b = create_booking(db, _payload(), actor, submit=True)
    # Không có luồng khớp → start() trả None → đi đường cũ, phiếu vẫn Chờ duyệt.
    assert b.status == m.BK_PENDING
    assert bridge.running_instance(db, b.id) is None


# ─────────────────────── Bộ máy gọi ngược khi phiên kết thúc ───────────────────────

def test_on_approved_marks_approved(db):
    b = _pending(db)
    bridge._on_approved(db, b.id, SimpleNamespace(updated_by=5, finish_reason=""))
    db.refresh(b)
    assert b.status == m.BK_APPROVED


def test_on_rejected_marks_rejected_with_reason(db):
    b = _pending(db)
    bridge._on_rejected(db, b.id, SimpleNamespace(updated_by=5, finish_reason="Sai khung giờ"))
    db.refresh(b)
    assert b.status == m.BK_REJECTED
    assert "Sai khung giờ" in b.note


def test_on_returned_marks_returned(db):
    b = _pending(db)
    bridge._on_returned(db, b.id, SimpleNamespace(updated_by=5, finish_reason="Thiếu thông tin"))
    db.refresh(b)
    assert b.status == m.BK_RETURNED
    assert "Thiếu thông tin" in b.note


def test_on_withdrawn_marks_draft(db):
    b = _pending(db)
    bridge._on_withdrawn(db, b.id, SimpleNamespace(updated_by=5, finish_reason=""))
    db.refresh(b)
    assert b.status == m.BK_DRAFT


# ─────────────────────── Chốt chặn đường cũ ───────────────────────

def test_block_legacy_path_no_running_instance_is_noop(db):
    b = _pending(db)
    bridge.block_legacy_path(db, b)  # không có phiên → không ném


def test_block_legacy_path_raises_when_instance_running(db):
    b = _pending(db)
    db.add(ApprovalInstance(entity="vehicle_booking", entity_id=b.id,
                            status=INSTANCE_RUNNING, flow_id=1))
    db.flush()
    with pytest.raises(HTTPException):
        bridge.block_legacy_path(db, b)


def test_entity_context_carries_routing_fields(db):
    b = _pending(db)
    ctx = bridge.entity_context(b)
    assert ctx["id"] == b.id
    assert ctx["department_id"] == b.department_id
    assert set(ctx) >= {"id", "request_type", "company_id", "department_id", "requester_id"}
