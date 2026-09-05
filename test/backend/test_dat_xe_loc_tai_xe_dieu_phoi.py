"""Phase 6.4 Đặt xe — nguồn tài xế khi điều phối lọc theo vai trò.

Ô chọn tài xế lúc điều phối CHỈ hiện người thật sự là tài xế:
- tài xế thuê ngoài (không tài khoản) → luôn hiện;
- tài xế nội bộ ĐANG GIỮ vai trò `booking_driver` → hiện;
- hồ sơ tài xế nội bộ gắn tài khoản KHÔNG có vai trò Tài xế → **ẩn**.
Danh mục Tài xế (màn quản lý) vẫn hiện hết — đây chỉ lọc cho ô điều phối.
"""
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.service import drivers_for_dispatch


def _user(db, uid, email):
    u = User(email=email, is_active=True)
    u.id = uid
    db.add(u)
    db.flush()
    return u


def test_dispatch_drivers_filtered_by_role(db):
    role = Role(code='booking_driver', name='Tài xế')
    db.add(role)
    db.flush()

    driver_user = _user(db, 301, 'driver@dego.vn')
    db.add(UserRole(user_id=driver_user.id, role_id=role.id))
    other_user = _user(db, 302, 'staff@dego.vn')  # không có vai trò Tài xế
    db.flush()

    external = m.Driver(name='Thuê Ngoài', phone='01', is_external=True)
    internal_ok = m.Driver(name='Nội Bộ Có Vai Trò', phone='02', user_id=driver_user.id)
    internal_no_role = m.Driver(name='Nội Bộ Không Vai Trò', phone='03', user_id=other_user.id)
    db.add_all([external, internal_ok, internal_no_role])
    db.flush()

    names = {d['name'] for d in drivers_for_dispatch(db)}
    assert names == {'Thuê Ngoài', 'Nội Bộ Có Vai Trò'}
    assert 'Nội Bộ Không Vai Trò' not in names


def test_dispatch_drivers_empty_when_no_qualifying(db):
    lone = _user(db, 310, 'x@dego.vn')  # không vai trò
    db.add(m.Driver(name='Ẩn', phone='09', user_id=lone.id))
    db.flush()
    assert drivers_for_dispatch(db) == []
