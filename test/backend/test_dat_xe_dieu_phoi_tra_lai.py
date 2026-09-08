"""Điều phối viên trả lại / từ chối phiếu ĐANG Đã điều phối (yêu cầu KH 07/09/2026).

Ở khâu "Điều phối" (tài xế chưa nhận) và "Điều phối lại" (tài xế từ chối), điều phối
viên có thể TRẢ VỀ NGƯỜI TẠO chỉnh sửa hoặc TỪ CHỐI hẳn — khi đó gỡ luôn xe/tài xế đã phân.
"""
from types import SimpleNamespace

from app.modules.employee.model import Employee
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.schema import DispatchIn, ReasonIn, VehicleBookingCreate
from app.modules.vehicle_booking.service import (
    approve_booking,
    create_booking,
    dispatch_booking,
    driver_reject,
    reject_booking,
    return_booking,
)


def _actor(db):
    emp = Employee(code='NV901', full_name='Điều Phối', email='dp@dego.vn',
                   department_id=7, company_id=3)
    db.add(emp)
    db.flush()
    return SimpleNamespace(id=201, employee_id=emp.id, email='dp@dego.vn')


def _dispatched(db):
    actor = _actor(db)
    v = m.Vehicle(license_plate='51A-111.11', model='Innova')
    d = m.Driver(name='Tài Xế', phone='0909')
    db.add_all([v, d])
    db.flush()
    data = VehicleBookingCreate(request_type=1, purpose='Đón khách', start_location='VP',
                                end_location='Q1', start_time='2026-12-10T08:00',
                                end_time='2026-12-10T12:00', passenger_count=2)
    b = create_booking(db, data, actor, submit=True)
    approve_booking(db, b, actor)
    dispatch_booking(db, b, DispatchIn(assigned_vehicle_id=v.id, assigned_driver_id=d.id), actor)
    assert (b.status, b.driver_status) == (m.BK_DISPATCHED, m.DRV_WAITING)
    return b, actor


def test_dispatcher_return_sends_back_and_clears_dispatch(db):
    b, actor = _dispatched(db)
    return_booking(db, b, ReasonIn(reason='Sai lộ trình'), actor)
    assert b.status == m.BK_RETURNED           # về người tạo sửa lại
    assert b.assigned_vehicle_id is None and b.assigned_driver_id is None
    assert b.driver_status == m.DRV_NONE        # gỡ điều phối


def test_dispatcher_reject_from_dispatch_locks_and_clears(db):
    b, actor = _dispatched(db)
    reject_booking(db, b, ReasonIn(reason='Không bố trí được xe'), actor)
    assert b.status == m.BK_REJECTED
    assert b.assigned_vehicle_id is None and b.driver_status == m.DRV_NONE


def test_return_and_reject_at_da_duyet(db):
    #  Phiếu ĐÃ DUYỆT (chưa điều phối) — điều phối viên vẫn trả về / từ chối được.
    actor = _actor(db)
    data = VehicleBookingCreate(request_type=1, purpose='Đi họp', start_location='VP',
                                end_location='Q3', start_time='2026-12-20T08:00',
                                end_time='2026-12-20T10:00', passenger_count=1)
    b = create_booking(db, data, actor, submit=True)
    approve_booking(db, b, actor)
    assert b.status == m.BK_APPROVED
    return_booking(db, b, ReasonIn(reason='Đổi điểm đến'), actor)
    assert b.status == m.BK_RETURNED

    b2 = create_booking(db, data, actor, submit=True)
    approve_booking(db, b2, actor)
    reject_booking(db, b2, ReasonIn(reason='Hết xe'), actor)
    assert b2.status == m.BK_REJECTED


def test_return_works_at_dieu_phoi_lai(db):
    #  "Điều phối lại" = đã điều phối + tài xế TỪ CHỐI → điều phối viên vẫn trả về được.
    b, actor = _dispatched(db)
    driver_reject(db, b, ReasonIn(reason='Xe hỏng'), actor)
    assert (b.status, b.driver_status) == (m.BK_DISPATCHED, m.DRV_REJECTED)
    return_booking(db, b, ReasonIn(reason='Đổi ngày đi'), actor)
    assert b.status == m.BK_RETURNED and b.driver_status == m.DRV_NONE
