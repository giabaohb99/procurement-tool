"""Bảng thống kê đội xe (theo XE / theo TÀI XẾ) và lịch Timeline của Đặt xe.

- Khối `fleet` chỉ hiện với người có quyền `approve` (điều phối viên / giám đốc);
  người chỉ tạo phiếu (own) hay chỉ `write` không thấy — chống lộ thống kê đội xe.
- `by_vehicle`/`by_driver` cộng đúng: số phiếu · hoàn tất · km; bỏ phiếu chưa gán xe.
- `timeline_events` trả phiếu trong KHOẢNG NGÀY, đúng phạm vi người xem, kèm `event_date`.
"""
from types import SimpleNamespace

from app.modules.employee.model import Employee
from app.modules.vehicle_booking.dashboard_service import build_overview
from app.modules.vehicle_booking.model import (
    BK_COMPLETED,
    BK_DISPATCHED,
    Driver,
    Vehicle,
    VehicleBooking,
)
from app.modules.vehicle_booking.service import timeline_events

CTY, DEPT = 1, 10
_seq = {"n": 0}


def _person(db, cap_quyen, *, uid, scope, **actions):
    emp = Employee(code=f"NVT{uid}", full_name=f"NVT{uid}", email=f"nvt{uid}@dego.vn",
                   department_id=DEPT, company_id=CTY)
    db.add(emp)
    db.flush()
    cap_quyen(uid, "vehicle_booking", scope=scope, **actions)
    return SimpleNamespace(id=uid, employee_id=emp.id, email=f"nvt{uid}@dego.vn")


def _booking(db, *, status=BK_DISPATCHED, vehicle_id=None, driver_id=None,
             distance_km=0, start_time=""):
    _seq["n"] += 1
    obj = VehicleBooking(
        code=f"XT{_seq['n']:04d}", status=status, created_by=9001, requester_id=9001,
        department_id=DEPT, company_id=CTY, assigned_vehicle_id=vehicle_id,
        assigned_driver_id=driver_id, distance_km=distance_km, start_time=start_time,
        purpose="[test]")
    db.add(obj)
    db.flush()
    return obj


def _fleet_seed(db):
    """Xe 1: 3 phiếu (2 hoàn tất, km 10+5) · Xe 2: 1 phiếu chưa hoàn tất. Một phiếu
    CHƯA gán xe (không được đếm)."""
    v1 = Vehicle(license_plate="51A-001", model="Vios")
    v2 = Vehicle(license_plate="51A-002", model="Innova")
    d1 = Driver(name="Bác Tài A")
    db.add_all([v1, v2, d1])
    db.flush()
    _booking(db, status=BK_COMPLETED, vehicle_id=v1.id, driver_id=d1.id, distance_km=10)
    _booking(db, status=BK_COMPLETED, vehicle_id=v1.id, driver_id=d1.id, distance_km=5)
    _booking(db, status=BK_DISPATCHED, vehicle_id=v1.id, driver_id=d1.id)
    _booking(db, status=BK_DISPATCHED, vehicle_id=v2.id)
    _booking(db, status=BK_DISPATCHED)  # chưa gán xe → không đếm ở by_vehicle
    return v1, v2, d1


def test_khoi_fleet_hien_cho_nguoi_co_quyen_approve(db, cap_quyen):
    _fleet_seed(db)
    user = _person(db, cap_quyen, uid=5001, scope="all", read=True, approve=True)
    data = build_overview(db, user)

    assert "fleet" in data
    by_v = {r["id"]: r for r in data["fleet"]["by_vehicle"]}
    # Xe 1: 3 phiếu, 2 hoàn tất, 15 km. Xếp đầu vì nhiều phiếu nhất.
    top = data["fleet"]["by_vehicle"][0]
    assert top["total"] == 3 and top["completed"] == 2 and top["distance_km"] == 15
    # Phiếu chưa gán xe (assigned_vehicle_id rỗng) KHÔNG tạo dòng thống kê.
    assert all(r["id"] for r in data["fleet"]["by_vehicle"])
    assert len(by_v) == 2

    by_d = data["fleet"]["by_driver"]
    assert by_d[0]["total"] == 3 and by_d[0]["completed"] == 2


def test_khoi_fleet_vang_mat_khi_khong_co_approve(db, cap_quyen):
    _fleet_seed(db)
    #  Điều phối viên "giả" chỉ có write (không approve) → KHÔNG thấy bảng đội xe.
    writer = _person(db, cap_quyen, uid=5002, scope="all", read=True, write=True)
    assert "fleet" not in build_overview(db, writer)
    #  Người chỉ tạo phiếu (own) cũng không thấy.
    owner = _person(db, cap_quyen, uid=5003, scope="own", read=True, create=True)
    assert "fleet" not in build_overview(db, owner)


def test_timeline_loc_theo_khoang_ngay_va_pham_vi(db, cap_quyen):
    _person_v = _person(db, cap_quyen, uid=5004, scope="all", read=True, approve=True)
    _booking(db, start_time="2026-09-10T08:00")   # trong khoảng
    _booking(db, start_time="2026-09-30T23:30")   # biên trên, còn trong khoảng
    _booking(db, start_time="2026-10-01T06:00")   # ngoài khoảng (tháng sau)
    _booking(db, start_time="2026-08-31T06:00")   # ngoài khoảng (tháng trước)

    events = timeline_events(db, _person_v, "2026-09-01", "2026-09-30")
    dates = sorted(e["event_date"] for e in events)
    assert dates == ["2026-09-10", "2026-09-30"]
    #  Mỗi sự kiện có đủ nhãn để vẽ thẻ (đi qua serialize_bookings).
    assert all("status_label" in e and "request_type_label" in e for e in events)


def test_timeline_bo_pham_vi_nguoi_xem(db, cap_quyen):
    #  Người xem phạm vi `own` chỉ thấy phiếu MÌNH tạo trên lịch.
    viewer = _person(db, cap_quyen, uid=5005, scope="own", read=True, create=True)
    mine = VehicleBooking(code="XTM01", status=BK_DISPATCHED, created_by=5005,
                          requester_id=5005, department_id=DEPT, company_id=CTY,
                          start_time="2026-09-12T09:00", purpose="[mine]")
    other = VehicleBooking(code="XTO01", status=BK_DISPATCHED, created_by=9999,
                           requester_id=9999, department_id=DEPT, company_id=CTY,
                           start_time="2026-09-12T09:00", purpose="[other]")
    db.add_all([mine, other])
    db.flush()

    events = timeline_events(db, viewer, "2026-09-01", "2026-09-30")
    codes = {e["code"] for e in events}
    assert "XTM01" in codes and "XTO01" not in codes
