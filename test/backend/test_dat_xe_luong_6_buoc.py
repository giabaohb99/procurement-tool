"""Phase 6.9 Đặt xe — kịch bản ĐẦY ĐỦ luồng 6 bước (happy path + hai nhánh trả/từ chối).

Chạy được ngay ở tầng service (SQLite) — khác E2E trình duyệt (Playwright) cần cả
stack + tài khoản demo cho 3 vai trò Đặt xe, để chạy trên host. Ở đây khẳng định
máy trạng thái chạy đúng suốt: tạo → duyệt → điều phối → nhận → bắt đầu → hoàn tất.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.employee.model import Employee
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.schema import (
    CompleteIn,
    DispatchIn,
    ReasonIn,
    VehicleBookingCreate,
)
from app.modules.vehicle_booking.service import (
    approve_booking,
    create_booking,
    dispatch_booking,
    driver_accept,
    driver_complete,
    driver_reject,
    driver_start,
    reject_booking,
    return_booking,
)


def _actor(db):
    emp = Employee(code='NV900', full_name='Người Tạo', email='c@dego.vn',
                   department_id=7, company_id=3)
    db.add(emp)
    db.flush()
    return SimpleNamespace(id=101, employee_id=emp.id, email='c@dego.vn')


def _payload():
    return VehicleBookingCreate(request_type=1, purpose='Đón đối tác', start_location='VP',
                                end_location='Sân bay', start_time='2026-09-10T08:00',
                                end_time='2026-09-10T12:00', passenger_count=3)


def _fleet(db):
    v = m.Vehicle(license_plate='51A-999.99', model='Innova')
    d = m.Driver(name='Tài Xế', phone='0909')
    db.add_all([v, d])
    db.flush()
    return v, d


def test_full_six_step_happy_path(db):
    actor = _actor(db)
    v, d = _fleet(db)

    # 1) Tạo + gửi duyệt
    b = create_booking(db, _payload(), actor, submit=True)
    assert b.status == m.BK_PENDING

    # 2) Duyệt
    approve_booking(db, b, actor)
    assert b.status == m.BK_APPROVED

    # 3) Điều phối (gán xe + tài xế)
    dispatch_booking(db, b, DispatchIn(assigned_vehicle_id=v.id, assigned_driver_id=d.id), actor)
    assert (b.status, b.driver_status) == (m.BK_DISPATCHED, m.DRV_WAITING)

    # 4) Tài xế nhận
    driver_accept(db, b, actor)
    assert b.driver_status == m.DRV_ACCEPTED

    # 5) Bắt đầu (chấm giờ đi)
    driver_start(db, b, actor)
    assert b.driver_status == m.DRV_ONGOING and b.actual_start_time

    # 6) Hoàn tất (km + chi phí)
    driver_complete(db, b, CompleteIn(distance_km=42.5, cost=350000), actor)
    assert b.status == m.BK_COMPLETED
    assert b.driver_status == m.DRV_COMPLETED
    assert b.actual_end_time and b.distance_km == 42.5 and b.cost == 350000


def test_return_branch_then_resubmit(db):
    actor = _actor(db)
    b = create_booking(db, _payload(), actor, submit=True)
    return_booking(db, b, ReasonIn(reason='Thiếu người tham gia'), actor)
    assert b.status == m.BK_RETURNED
    assert 'Thiếu người tham gia' in b.note


def test_reject_branch_locks(db):
    actor = _actor(db)
    b = create_booking(db, _payload(), actor, submit=True)
    reject_booking(db, b, ReasonIn(reason='Không cần thiết'), actor)
    assert b.status == m.BK_REJECTED
    # Đã từ chối thì không duyệt lại được.
    with pytest.raises(HTTPException):
        approve_booking(db, b, actor)


def test_driver_reject_returns_to_dispatch(db):
    actor = _actor(db)
    v, d = _fleet(db)
    b = create_booking(db, _payload(), actor, submit=True)
    approve_booking(db, b, actor)
    dispatch_booking(db, b, DispatchIn(assigned_vehicle_id=v.id, assigned_driver_id=d.id), actor)
    driver_reject(db, b, ReasonIn(reason='Kẹt chuyến khác'), actor)
    assert b.driver_status == m.DRV_REJECTED
    assert b.status == m.BK_DISPATCHED  # chờ điều phối lại
