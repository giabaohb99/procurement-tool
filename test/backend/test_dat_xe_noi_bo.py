"""Nghiệp vụ tạo & sửa phiếu Đặt xe nội bộ (MVP).

Kiểm ở tầng service để khỏi dựng cả lớp RBAC của endpoint. Ba chỗ dễ sai nhất:
- lưu nháp vs gửi duyệt phải ra đúng trạng thái (BK_DRAFT vs BK_PENDING);
- điểm dừng lưu chuỗi JSON, tách lại đúng thứ tự và loại ô rỗng;
- CHỈ sửa được khi phiếu còn nháp / bị trả về — vào luồng rồi phải chặn.
"""
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.employee.model import Employee
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.schema import (
    VehicleBookingCreate,
    VehicleBookingResponse,
    VehicleBookingUpdate,
)
from app.modules.vehicle_booking.service import (
    apply_keyword_search,
    create_booking,
    update_booking,
)


def _actor(db, *, dept=7, company=3):
    """Người tạo có hồ sơ nhân sự (để service snapshot tên + phạm vi)."""
    emp = Employee(code="NV900", full_name="Phạm Tài Xế", email="tx@dego.vn",
                   department_id=dept, company_id=company)
    db.add(emp)
    db.flush()
    return SimpleNamespace(id=101, employee_id=emp.id, email="tx@dego.vn")


def _car_payload(**over):
    data = dict(request_type=1, purpose="Đi thăm khách hàng",
                start_location="VP", end_location="Q7",
                stops=["Kho Q4", "  ", "Bãi Q1"], start_time="2026-09-01T08:00",
                end_time="2026-09-01T10:00", passenger_count=3)
    data.update(over)
    return VehicleBookingCreate(**data)


def test_save_draft_stays_draft(db):
    actor = _actor(db)
    b = create_booking(db, _car_payload(), actor, submit=False)
    assert b.status == m.BK_DRAFT
    assert b.code.startswith("DX")
    # Snapshot người tạo + phạm vi lấy từ hồ sơ nhân sự.
    assert b.requester == "Phạm Tài Xế"
    assert (b.department_id, b.company_id) == (7, 3)


def test_submit_goes_pending(db):
    actor = _actor(db)
    b = create_booking(db, _car_payload(), actor, submit=True)
    assert b.status == m.BK_PENDING


def test_stops_are_serialized_and_trimmed_in_order(db):
    actor = _actor(db)
    b = create_booking(db, _car_payload(), actor, submit=False)
    # Ô rỗng bị loại; thứ tự giữ nguyên.
    assert json.loads(b.stops) == ["Kho Q4", "Bãi Q1"]
    # Response tách chuỗi JSON trở lại thành list.
    out = VehicleBookingResponse.model_validate(b)
    assert out.stops == ["Kho Q4", "Bãi Q1"]


def test_response_carries_number_and_label(db):
    actor = _actor(db)
    b = create_booking(db, _car_payload(request_type=2, purpose="Giao hàng",
                                        goods_name="Thùng", sender_name="A",
                                        sender_phone="1", receiver_name="B",
                                        receiver_phone="2"),
                       actor, submit=True)
    out = VehicleBookingResponse.model_validate(b)
    assert out.request_type == 2
    assert out.request_type_label == "Đặt xe giao hàng"
    assert out.status == m.BK_PENDING
    assert out.status_label == "Chờ duyệt"


def test_blank_purpose_rejected(db):
    actor = _actor(db)
    with pytest.raises(HTTPException):
        create_booking(db, _car_payload(purpose="   "), actor, submit=False)


def test_unknown_type_falls_back_to_car(db):
    actor = _actor(db)
    b = create_booking(db, _car_payload(request_type=99), actor, submit=False)
    assert b.request_type == m.TYPE_CAR


def test_update_allowed_while_draft(db):
    actor = _actor(db)
    b = create_booking(db, _car_payload(), actor, submit=False)
    b2 = update_booking(db, b, VehicleBookingUpdate(purpose="Đổi mục đích",
                                                    stops=["Điểm mới"]),
                        actor, submit=True)
    assert b2.purpose == "Đổi mục đích"
    assert json.loads(b2.stops) == ["Điểm mới"]
    assert b2.status == m.BK_PENDING  # submit=True đẩy tiếp sang chờ duyệt


def test_update_blocked_after_entering_flow(db):
    actor = _actor(db)
    b = create_booking(db, _car_payload(), actor, submit=True)  # đã Chờ duyệt
    with pytest.raises(HTTPException):
        update_booking(db, b, VehicleBookingUpdate(purpose="X"), actor, submit=False)


def test_keyword_search_matches_code_and_purpose(db):
    actor = _actor(db)
    create_booking(db, _car_payload(purpose="Đón đối tác sân bay"), actor, submit=False)
    create_booking(db, _car_payload(purpose="Giao chứng từ"), actor, submit=False)
    hit = apply_keyword_search(db.query(m.VehicleBooking), "sân bay").all()
    assert len(hit) == 1 and "sân bay" in hit[0].purpose
    # Bỏ trống thì không lọc.
    assert apply_keyword_search(db.query(m.VehicleBooking), "  ").count() == 2
