"""Đặt xe TỰ LÁI — người yêu cầu đóng vai tài xế.

- Điều phối viên CHỈ gán xe (không cần tài xế).
- Người yêu cầu (requester) là tài xế: chấp nhận / bắt đầu / hoàn tất.
- "Chuyến của tôi" gồm cả chuyến tự lái của chính mình.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.employee.model import Employee
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.schema import CompleteIn, DispatchIn, VehicleBookingCreate
from app.modules.vehicle_booking.service import (
    approve_booking,
    create_booking,
    dispatch_booking,
    driver_accept,
    driver_complete,
    driver_start,
    filter_my_trips,
    serialize_booking,
)


def _actor(db, *, uid=101):
    emp = Employee(code='NV900', full_name='Người Tự Lái', email='self@dego.vn',
                   department_id=7, company_id=3)
    db.add(emp)
    db.flush()
    return SimpleNamespace(id=uid, employee_id=emp.id, email='self@dego.vn')


def _payload(**over):
    data = dict(request_type=1, purpose='Tự lái đi họp', start_location='VP',
                end_location='Q1', start_time='2026-09-10T08:00', end_time='2026-09-10T10:00',
                passenger_count=1, is_self_drive=True, license_number='B2-12345',
                license_class='B2')
    data.update(over)
    return VehicleBookingCreate(**data)


def test_create_stores_self_drive_and_license(db):
    actor = _actor(db)
    b = create_booking(db, _payload(), actor, submit=False)
    assert b.is_self_drive is True
    assert (b.license_number, b.license_class) == ('B2-12345', 'B2')
    assert b.requester_id == actor.id


def test_dispatch_needs_only_vehicle(db):
    actor = _actor(db)
    veh = m.Vehicle(license_plate='51A-777.77', model='Vios')
    db.add(veh)
    db.flush()
    b = create_booking(db, _payload(), actor, submit=True)
    approve_booking(db, b, actor)
    # Điều phối chỉ gán XE (assigned_driver_id để trống).
    dispatch_booking(db, b, DispatchIn(assigned_vehicle_id=veh.id), actor)
    assert b.status == m.BK_DISPATCHED
    assert b.driver_status == m.DRV_WAITING
    assert b.assigned_vehicle_id == veh.id
    assert not b.assigned_driver_id

    out = serialize_booking(db, b, viewer=actor)
    assert 'tự lái' in out['assigned_driver_label'].lower()
    assert out['is_assigned_driver'] is True  # người yêu cầu = tài xế


def test_requester_drives_full_flow(db):
    actor = _actor(db)
    veh = m.Vehicle(license_plate='51A-888.88', model='Innova')
    db.add(veh)
    db.flush()
    b = create_booking(db, _payload(), actor, submit=True)
    approve_booking(db, b, actor)
    dispatch_booking(db, b, DispatchIn(assigned_vehicle_id=veh.id), actor)

    driver_accept(db, b, actor)
    assert b.driver_status == m.DRV_ACCEPTED
    driver_start(db, b, actor)
    assert b.driver_status == m.DRV_ONGOING
    driver_complete(db, b, CompleteIn(distance_km=12, cost=0), actor)
    assert b.status == m.BK_COMPLETED and b.driver_status == m.DRV_COMPLETED


def test_non_requester_driver_cannot_drive_self_trip(db):
    actor = _actor(db, uid=101)
    veh = m.Vehicle(license_plate='51A-999.99', model='X')
    other_user = 202
    drv = m.Driver(name='Tài xế khác', phone='09', user_id=other_user)
    db.add_all([veh, drv])
    db.flush()
    b = create_booking(db, _payload(), actor, submit=True)
    approve_booking(db, b, actor)
    dispatch_booking(db, b, DispatchIn(assigned_vehicle_id=veh.id), actor)
    # Một tài xế KHÁC (có hồ sơ) không được thao tác chuyến tự lái của người khác.
    with pytest.raises(HTTPException):
        driver_accept(db, b, SimpleNamespace(id=other_user))


def test_self_drive_conflict_only_on_vehicle(db):
    #  Tự lái không có tài xế (driver_id 0) → chỉ chống trùng theo XE, không báo
    #  trùng "tài xế" giữa các chuyến tự lái với nhau.
    actor = _actor(db)
    v1 = m.Vehicle(license_plate='51A-AAA.11', model='A')
    v2 = m.Vehicle(license_plate='51A-BBB.22', model='B')
    db.add_all([v1, v2])
    db.flush()
    b1 = create_booking(db, _payload(start_time='2026-09-10T08:00', end_time='2026-09-10T10:00'), actor, submit=True)
    approve_booking(db, b1, actor)
    dispatch_booking(db, b1, DispatchIn(assigned_vehicle_id=v1.id), actor)

    # Xe KHÁC, giờ chồng → KHÔNG trùng (dù cùng driver_id 0).
    b2 = create_booking(db, _payload(start_time='2026-09-10T09:00', end_time='2026-09-10T11:00'), actor, submit=True)
    approve_booking(db, b2, actor)
    assert dispatch_booking(db, b2, DispatchIn(assigned_vehicle_id=v2.id), actor).status == m.BK_DISPATCHED

    # Cùng XE, giờ chồng → trùng.
    b3 = create_booking(db, _payload(start_time='2026-09-10T09:30', end_time='2026-09-10T11:30'), actor, submit=True)
    approve_booking(db, b3, actor)
    with pytest.raises(HTTPException):
        dispatch_booking(db, b3, DispatchIn(assigned_vehicle_id=v1.id), actor)


def test_my_trips_includes_self_drive(db):
    actor = _actor(db)
    veh = m.Vehicle(license_plate='51A-111.22', model='Y')
    db.add(veh)
    db.flush()
    b = create_booking(db, _payload(), actor, submit=True)
    approve_booking(db, b, actor)
    dispatch_booking(db, b, DispatchIn(assigned_vehicle_id=veh.id), actor)

    mine = filter_my_trips(db.query(m.VehicleBooking), db, actor).all()
    assert [t.id for t in mine] == [b.id]
