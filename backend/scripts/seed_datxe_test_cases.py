"""Dựng DỮ LIỆU MẪU kiểm phân quyền Đặt xe (2 phiếu A & B) bằng CHÍNH 7 tài khoản test.

Luồng dựng (khớp doc/dat-xe-duyet-dau/test-phan-quyen.md §2):
  A: NS1 tạo+gửi duyệt → TP1 duyệt → ĐPV điều phối cho TX1
  B: NS2 tạo+gửi duyệt → TP2 duyệt → ĐPV điều phối cho TX2

Idempotent: nhận diện theo `purpose` có tiền tố [TEST-PQ]; chạy lại không tạo trùng.
Chạy (LOCAL/DEV):  docker compose exec -T api python -m scripts.seed_datxe_test_cases
"""
import app.core.all_models  # noqa: F401 — nạp toàn bộ model
from app.core.auth import perm_cache_clear
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.user.model import User
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking import service
from app.modules.vehicle_booking.schema import DispatchIn, VehicleBookingCreate

#  MÃ NHÂN VIÊN, không phải email (bao-CR-380, 11/09/2026). Bản cũ tra người bằng
#  email `@dego.com` do seed tài khoản dập vào — mà danh sách email ngày ấy lệch
#  một mã, nên hai phiếu mẫu dựng ra mang tên nhầm người và không ai thấy sai ở
#  đâu cả. Mã nhân viên là khóa thật của hồ sơ, không ai dập đè lên được.
NS1 = "NSU204"  # Dương Hải Yến — Nhân sự
TP1 = "NSU203"  # Nguyễn Đỗ Quyên — Trưởng bộ phận
NS2 = "NSU172"  # Hồ Ngọc Quế Anh — Nhân sự
TP2 = "NSU171"  # Nguyễn Minh Toàn — Trưởng bộ phận
DPV = "NSU056"  # Bùi Huỳnh Trường Thành — Điều phối viên
TX1 = "NSU060"  # Lê Tấn Nhựt — Tài xế
TX2 = "NSU058"  # Trần Quốc Thái — Tài xế


def _user(db, code):
    emp = db.query(Employee).filter(Employee.code == code).first()
    if emp is None:
        raise SystemExit(f"Thiếu hồ sơ nhân sự {code} — kiểm lại dữ liệu nhân sự.")
    #  Ưu tiên tài khoản đang hoạt động — cùng luật với `auth.authenticate`.
    u = (
        db.query(User).filter(User.employee_id == emp.id, User.is_active.is_(True)).first()
        or db.query(User).filter(User.employee_id == emp.id).first()
    )
    if u is None:
        raise SystemExit(f"Thiếu tài khoản {code} — chạy scripts.seed_datxe_test_accounts trước.")
    return u


def _emp_name(db, user):
    emp = db.get(Employee, user.employee_id) if user.employee_id else None
    return (emp.full_name if emp and emp.full_name else user.email)


def _driver_for(db, user):
    """Hồ sơ tài xế (tab_driver) nối tài khoản này — tạo nếu chưa có."""
    d = db.query(m.Driver).filter(m.Driver.user_id == user.id).first()
    if d:
        return d
    d = m.Driver(name=_emp_name(db, user), phone="", user_id=user.id,
                 license_number="B2-TEST", license_class="B2", status="available")
    db.add(d)
    db.commit()
    db.refresh(d)
    print(f"  + Tạo hồ sơ tài xế cho {d.name}")
    return d


def _vehicle(db, plate, model_name):
    v = db.query(m.Vehicle).filter(m.Vehicle.license_plate == plate).first()
    if v:
        return v
    v = m.Vehicle(license_plate=plate, model=model_name, type="Xe con", capacity=4, status="available")
    db.add(v)
    db.commit()
    db.refresh(v)
    print(f"  + Tạo xe {plate}")
    return v


def _make_case(db, purpose, requester, approver, driver, vehicle, *, delivery=False):
    existing = (db.query(m.VehicleBooking)
                .filter(m.VehicleBooking.purpose == purpose,
                        m.VehicleBooking.is_deleted == False).first())  # noqa: E712
    if existing:
        print(f"  = Đã có: {purpose} ({existing.code})")
        return existing

    payload = VehicleBookingCreate(
        request_type=2 if delivery else 1,
        purpose=purpose,
        start_location="Văn phòng Degoholding",
        end_location="Điểm đến kiểm thử",
        start_time="2026-09-20T08:00",
        end_time="2026-09-20T11:00",
        passenger_count=2,
        goods_name="Thùng hàng mẫu" if delivery else "",
        sender_name="Kho A" if delivery else "",
        sender_phone="0900000001" if delivery else "",
        receiver_name="Khách B" if delivery else "",
        receiver_phone="0900000002" if delivery else "",
    )
    b = service.create_booking(db, payload, requester, submit=True)     # NS gửi duyệt
    service.approve_booking(db, b, approver)                            # TP duyệt
    dpv = _user(db, DPV)
    service.dispatch_booking(db, b, DispatchIn(assigned_vehicle_id=vehicle.id,
                                               assigned_driver_id=driver.id), dpv)  # ĐPV điều phối
    print(f"  ✓ {purpose} → {b.code} · điều phối XE {vehicle.license_plate} cho {driver.name}")
    return b


def run():
    db = SessionLocal()
    try:
        for code in (NS1, TP1, NS2, TP2, DPV, TX1, TX2):
            perm_cache_clear(_user(db, code).id)

        drv1 = _driver_for(db, _user(db, TX1))
        drv2 = _driver_for(db, _user(db, TX2))
        veh1 = _vehicle(db, "TEST-A.01", "Toyota Vios (test)")
        veh2 = _vehicle(db, "TEST-B.02", "Ford Transit (test)")

        _make_case(db, "[TEST-PQ] NS1 đi họp khách", _user(db, NS1), _user(db, TP1), drv1, veh1)
        _make_case(db, "[TEST-PQ] NS2 giao hàng", _user(db, NS2), _user(db, TP2), drv2, veh2, delivery=True)

        print("Xong. Đăng nhập từng tài khoản (nút Đổi tài khoản nhanh) để kiểm theo test-phan-quyen.md.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
