"""Đặt xe — KIỂM TỔNG THỂ toàn luồng (mô phỏng phiếu DX006).

Gộp hai phần trong một file để có bức tranh đầy đủ:

1. `test_full_flow_all_four_variants` — 2 loại × 2 chế độ (công tác/giao hàng ×
   có tài xế/tự lái) chạy hết máy trạng thái 6 bước tạo → duyệt → điều phối →
   nhận → bắt đầu → hoàn tất, khẳng định về đúng trạng thái cuối COMPLETED.

2. `test_permission_matrix_dx006` — ma trận PHÂN QUYỀN 7 tài khoản theo kịch bản
   `doc/dat-xe-duyet-dau/test-phan-quyen.md` (T1–T8): NS chỉ thấy phiếu của mình,
   TP thấy phiếu cùng phòng, ĐPV thấy tất cả, tài xế chỉ thấy chuyến được phân —
   và TX1 KHÔNG thấy chuyến của TX2. Đây là chốt chặn `apply_scope` thật, không
   phải ẩn nút, nên phải có test tự động chứ không kiểm bằng tay mãi.
"""
from types import SimpleNamespace

import pytest

from app.core.auth import get_perm_profile
from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.schema import (
    CompleteIn,
    DispatchIn,
    VehicleBookingCreate,
)
from app.modules.vehicle_booking.service import (
    approve_booking,
    create_booking,
    dispatch_booking,
    driver_accept,
    driver_complete,
    driver_start,
    filter_my_trips,
)

# ---------------------------------------------------------------------------
# Phần 1 — Luồng đầy đủ cho cả 4 biến thể
# ---------------------------------------------------------------------------


def _delivery_extra():
    return dict(goods_name="Thùng hàng mẫu", sender_name="Kho A", sender_phone="0900000001",
                receiver_name="Khách B", receiver_phone="0900000002")


def _payload(*, delivery: bool, self_drive: bool):
    data = dict(
        request_type=2 if delivery else 1,
        purpose=("Giao hàng" if delivery else "Đi công tác") + (" (tự lái)" if self_drive else ""),
        start_location="VP Degoholding", end_location="Điểm đến",
        start_time="2026-09-20T08:00", end_time="2026-09-20T11:00",
        passenger_count=2, is_self_drive=self_drive,
        license_number="B2-12345" if self_drive else "",
        license_class="B2" if self_drive else "",
    )
    if delivery:
        data.update(_delivery_extra())
    return VehicleBookingCreate(**data)


def _actor(db, *, uid=101):
    emp = Employee(code="NV900", full_name="Người Tạo", email="c@dego.vn",
                   department_id=7, company_id=3)
    db.add(emp)
    db.flush()
    return SimpleNamespace(id=uid, employee_id=emp.id, email="c@dego.vn")


@pytest.mark.parametrize("delivery", [False, True], ids=["cong-tac", "giao-hang"])
@pytest.mark.parametrize("self_drive", [False, True], ids=["co-tai-xe", "tu-lai"])
def test_full_flow_all_four_variants(db, delivery, self_drive):
    actor = _actor(db)
    veh = m.Vehicle(license_plate="51A-100.10", model="Innova")
    db.add(veh)
    #  Có tài xế → cần hồ sơ tài xế; tự lái → điều phối chỉ gán XE, người yêu cầu lái.
    driver = None if self_drive else m.Driver(name="Tài Xế", phone="0909")
    if driver is not None:
        db.add(driver)
    db.flush()

    b = create_booking(db, _payload(delivery=delivery, self_drive=self_drive), actor, submit=True)
    assert b.status == m.BK_PENDING
    assert b.is_self_drive is self_drive

    approve_booking(db, b, actor)
    assert b.status == m.BK_APPROVED

    dispatch = DispatchIn(assigned_vehicle_id=veh.id,
                          assigned_driver_id=0 if self_drive else driver.id)
    dispatch_booking(db, b, dispatch, actor)
    assert (b.status, b.driver_status) == (m.BK_DISPATCHED, m.DRV_WAITING)
    if self_drive:
        assert not b.assigned_driver_id  # tự lái không gán tài xế riêng

    driver_accept(db, b, actor)
    assert b.driver_status == m.DRV_ACCEPTED
    driver_start(db, b, actor)
    assert b.driver_status == m.DRV_ONGOING and b.actual_start_time
    driver_complete(db, b, CompleteIn(distance_km=42.5, cost=350000), actor)
    assert b.status == m.BK_COMPLETED
    assert b.driver_status == m.DRV_COMPLETED
    assert b.actual_end_time and b.distance_km == 42.5 and b.cost == 350000


# ---------------------------------------------------------------------------
# Phần 2 — Ma trận phân quyền 7 tài khoản (DX006 / test-phan-quyen.md T1–T8)
# ---------------------------------------------------------------------------

DEPT_1, DEPT_2, DEPT_DPV = 10, 20, 30
COMPANY = 1


def _person(db, cap_quyen, *, uid, code, dept, scope):
    """Dựng 1 tài khoản thật: Employee + grant vai trò vehicle_booking(read) phạm vi `scope`."""
    emp = Employee(code=code, full_name=code, email=f"{code}@dego.vn",
                   department_id=dept, company_id=COMPANY)
    db.add(emp)
    db.flush()
    user = SimpleNamespace(id=uid, employee_id=emp.id, email=f"{code}@dego.vn")
    cap_quyen(uid, "vehicle_booking", scope=scope, read=True)
    return user


def _visible_ids(db, user):
    profile = get_perm_profile(db, user)
    q = apply_scope(db.query(m.VehicleBooking), m.VehicleBooking, "vehicle_booking", user, profile)
    return {b.id for b in q.all()}


def _booking_payload(purpose, *, delivery=False):
    data = dict(request_type=2 if delivery else 1, purpose=purpose,
                start_location="VP", end_location="Điểm đến",
                start_time="2026-09-20T08:00", end_time="2026-09-20T11:00", passenger_count=1)
    if delivery:
        data.update(_delivery_extra())
    return VehicleBookingCreate(**data)


def test_permission_matrix_dx006(db, cap_quyen):
    #  Bảy tài khoản đúng vai trò/phạm vi như bảng §1 của test-phan-quyen.md.
    ns1 = _person(db, cap_quyen, uid=1101, code="NS1", dept=DEPT_1, scope="own")
    tp1 = _person(db, cap_quyen, uid=1102, code="TP1", dept=DEPT_1, scope="dept")
    ns2 = _person(db, cap_quyen, uid=1103, code="NS2", dept=DEPT_2, scope="own")
    tp2 = _person(db, cap_quyen, uid=1104, code="TP2", dept=DEPT_2, scope="dept")
    dpv = _person(db, cap_quyen, uid=1105, code="DPV", dept=DEPT_DPV, scope="all")
    tx1 = _person(db, cap_quyen, uid=1106, code="TX1", dept=DEPT_DPV, scope="assigned")
    tx2 = _person(db, cap_quyen, uid=1107, code="TX2", dept=DEPT_DPV, scope="assigned")

    #  Hồ sơ tài xế nối tài khoản TX1/TX2 (điều kiện `assigned` khớp qua Driver.user_id).
    drv1 = m.Driver(name="TX1", phone="1", user_id=tx1.id)
    drv2 = m.Driver(name="TX2", phone="2", user_id=tx2.id)
    v1 = m.Vehicle(license_plate="TEST-A.01", model="Vios")
    v2 = m.Vehicle(license_plate="TEST-B.02", model="Transit")
    db.add_all([drv1, drv2, v1, v2])
    db.flush()

    #  A: NS1 tạo+gửi → TP1 duyệt → ĐPV điều phối cho TX1.
    a = create_booking(db, _booking_payload("[DX006] NS1 đi họp"), ns1, submit=True)
    approve_booking(db, a, tp1)
    dispatch_booking(db, a, DispatchIn(assigned_vehicle_id=v1.id, assigned_driver_id=drv1.id), dpv)

    #  B: NS2 tạo+gửi → TP2 duyệt → ĐPV điều phối cho TX2.
    b = create_booking(db, _booking_payload("[DX006] NS2 giao hàng", delivery=True), ns2, submit=True)
    approve_booking(db, b, tp2)
    dispatch_booking(db, b, DispatchIn(assigned_vehicle_id=v2.id, assigned_driver_id=drv2.id), dpv)

    # T1/T2 — NS1 chỉ thấy phiếu của mình (A), KHÔNG thấy B của NS2.
    assert _visible_ids(db, ns1) == {a.id}
    # T3/T4 — TP1 thấy phiếu cùng phòng (A), KHÔNG thấy B (NS2 khác phòng).
    assert _visible_ids(db, tp1) == {a.id}
    # đối xứng: NS2 và TP2 chỉ thấy B.
    assert _visible_ids(db, ns2) == {b.id}
    assert _visible_ids(db, tp2) == {b.id}
    # T5 — ĐPV thấy TẤT CẢ.
    assert _visible_ids(db, dpv) == {a.id, b.id}
    # T6/T7 — TX1 chỉ thấy chuyến được phân cho mình (A), KHÔNG thấy B (của TX2).
    assert _visible_ids(db, tx1) == {a.id}
    # T8 — TX2 chỉ thấy B, không thấy A.
    assert _visible_ids(db, tx2) == {b.id}

    #  "Chuyến của tôi" cũng phải tách đúng theo tài xế (không lẫn chuyến của người khác).
    assert {t.id for t in filter_my_trips(db.query(m.VehicleBooking), db, tx1).all()} == {a.id}
    assert {t.id for t in filter_my_trips(db.query(m.VehicleBooking), db, tx2).all()} == {b.id}
