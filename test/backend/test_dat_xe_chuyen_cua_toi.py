"""Phase 6.2 Đặt xe — màn "Chuyến của tôi" lọc chuyến được phân cho chính tài xế.

`filter_my_trips` chỉ trả chuyến mà người xem là TÀI XẾ được phân — khác phạm vi
`assigned` (còn gồm phiếu mình tạo). Không có hồ sơ tài xế → rỗng.
"""
from types import SimpleNamespace

from app.modules.user.model import User
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.service import filter_my_trips


def _user(db, uid):
    u = User(email=f'u{uid}@dego.vn', is_active=True)
    u.id = uid
    db.add(u)
    db.flush()
    return u


def _trip(db, driver_id):
    b = m.VehicleBooking(code=f'DX{driver_id:03d}', status=m.BK_DISPATCHED,
                         driver_status=m.DRV_WAITING, assigned_driver_id=driver_id)
    db.add(b)
    db.flush()
    return b


def test_filter_my_trips_returns_only_own_assigned(db):
    ua, ub = _user(db, 401), _user(db, 402)
    da = m.Driver(name='A', phone='1', user_id=ua.id)
    dbv = m.Driver(name='B', phone='2', user_id=ub.id)
    db.add_all([da, dbv])
    db.flush()
    _trip(db, da.id)
    _trip(db, dbv.id)

    q = db.query(m.VehicleBooking)
    mine = filter_my_trips(q, db, SimpleNamespace(id=ua.id)).all()
    assert [t.assigned_driver_id for t in mine] == [da.id]


def test_filter_my_trips_empty_without_driver_profile(db):
    da = m.Driver(name='A', phone='1', user_id=999)
    db.add(da)
    db.flush()
    _trip(db, da.id)
    #  Người xem không có hồ sơ tài xế → không thấy chuyến nào.
    mine = filter_my_trips(db.query(m.VehicleBooking), db, SimpleNamespace(id=500)).all()
    assert mine == []
