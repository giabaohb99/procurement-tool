# -*- coding: utf-8 -*-
"""Dựng dữ liệu DEMO cho màn «Chuyến của tôi» (`/vehicle-booking/my-trips`).

CHỈ DÙNG Ở MÁY LOCAL. Đây là dữ liệu rác để xem/chỉnh giao diện, đừng chạy trên
dev/prod.

Chạy:
    docker compose exec -T api python -m scripts.demo_chuyen_cua_toi           # dựng
    docker compose exec -T api python -m scripts.demo_chuyen_cua_toi --xoa     # dọn
    docker compose exec -T api python -m scripts.demo_chuyen_cua_toi --email a@b.c
    docker compose exec -T api python -m scripts.demo_chuyen_cua_toi --user 275

KHÔNG truyền gì thì script tự lấy tài khoản của PHIÊN ĐĂNG NHẬP GẦN NHẤT. Máy
local hay có vài phiên chạy song song (mỗi người một tài khoản trên cùng một DB),
mà màn «Chuyến của tôi» lọc theo NGƯỜI ĐANG XEM — dựng nhầm tài khoản thì màn vẫn
rỗng trong khi DB đầy dữ liệu, và không có gì trên màn hình nói ra điều đó.

CHẠY LẠI ĐƯỢC: mỗi lần dựng đều xóa sạch phiếu demo cũ (nhận ra nhờ dấu
`[DEMO-CHUYEN-CUA-TOI]` trong `note`) rồi tạo lại, nên bấm thử hỏng thế nào cũng
reset được. `--xoa` dọn cả hồ sơ tài xế demo.

VÌ SAO PHẢI CÓ HỒ SƠ TÀI XẾ: `service.filter_my_trips` chỉ nhận hai loại chuyến —
được phân cho một hồ sơ tài xế NỐI VỚI tài khoản đang xem, hoặc chuyến TỰ LÁI do
chính họ yêu cầu. Trên DB local hiện KHÔNG hồ sơ tài xế nào có `user_id`, nên màn
này rỗng với mọi tài khoản. Script tạo một hồ sơ tài xế nối vào tài khoản đích.

Màn hình còn lọc cứng `status = Đã điều phối` và `created_at` trong 30 ngày gần
nhất, nên mọi phiếu dựng ra đều phải nằm trong hai điều kiện đó — sai một cái là
màn vẫn rỗng dù DB có dữ liệu.
"""
import argparse
import re
import sys
from datetime import datetime, timedelta

import app.core.all_models  # noqa: F401 — nạp đủ model, không thì mapper User gãy
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.login_session.model import LoginSession
from app.modules.user.model import User
from app.modules.vehicle_booking.model import (
    BK_DISPATCHED,
    DRV_ACCEPTED,
    DRV_ONGOING,
    DRV_WAITING,
    TYPE_CAR,
    TYPE_DELIVERY,
    Driver,
    Vehicle,
    VehicleBooking,
)

#  Dấu nhận biết phiếu do script này tạo. Nằm trong `note`, và `note` CÓ hiện —
#  khối «Ghi chú» ở trang chi tiết phiếu bày nguyên văn. Nên viết thành câu người
#  đọc hiểu chứ không phải một chuỗi mã: mở phiếu ra thấy `[DEMO-XXX]` thì người
#  dùng không biết đó là rác của script hay một quy ước nghiệp vụ nào đó.
MARKER = "Dữ liệu demo — dựng bằng scripts/demo_chuyen_cua_toi.py, xoá được bằng --xoa"
#  Chuỗi dùng để TRUY LẠI (bền hơn cả câu trên: đổi câu chữ vẫn tìm ra phiếu cũ).
MARKER_KEY = "scripts/demo_chuyen_cua_toi.py"

#  (lệch ngày so với hôm nay, giờ đi, số tiếng chạy, loại phiếu, trạng thái tài
#   xế, tự lái?, biển số xe — rỗng = chưa gán xe, mục đích, điểm đi, điểm đến)
TRIPS = [
    (0, "08:00", 4, TYPE_CAR, DRV_ONGOING, False, "65A-096.81",
     "Chở Ban giám đốc đi họp Sở Công Thương",
     "Văn phòng DEGO — 12 Nguyễn Huệ, Q.1", "Sở Công Thương TP.HCM — 163 Hai Bà Trưng, Q.3"),
    (0, "13:30", 3, TYPE_CAR, DRV_ACCEPTED, False, "51M-15735",
     "Đón đối tác Hàn Quốc tại sân bay Tân Sơn Nhất",
     "Văn phòng DEGO — 12 Nguyễn Huệ, Q.1", "Ga quốc tế Tân Sơn Nhất"),
    (1, "06:30", 9, TYPE_CAR, DRV_WAITING, False, "51L-423.31",
     "Đưa đoàn khách Nhật đi tham quan nhà máy Long An",
     "Khách sạn Rex — 141 Nguyễn Huệ, Q.1", "Nhà máy DEGO Long An — KCN Thuận Đạo, Bến Lức"),
    (1, "09:00", 5, TYPE_DELIVERY, DRV_WAITING, False, "51D-895.00",
     "Giao 12 thùng mẫu bao bì cho khách duyệt trước khi vào đơn",
     "Kho Bình Chánh — Lô C3, KCN Vĩnh Lộc", "Công ty CP Thực phẩm Sài Gòn — Q.7"),
    (2, "07:00", 6, TYPE_DELIVERY, DRV_ACCEPTED, False, "51D-853.97",
     "Chuyển hàng tồn từ kho Bình Chánh về kho Thủ Đức",
     "Kho Bình Chánh — Lô C3, KCN Vĩnh Lộc", "Kho Thủ Đức — 45 Đường số 8, P.Linh Trung"),
    (2, "14:00", 3, TYPE_CAR, DRV_ACCEPTED, False, "",
     "Đi ngân hàng nộp hồ sơ bảo lãnh thầu (chưa bố trí được xe)",
     "Văn phòng DEGO — 12 Nguyễn Huệ, Q.1", "Vietcombank CN Tân Định"),
    (3, "08:30", 4, TYPE_CAR, DRV_WAITING, True, "51D-465.49",
     "Tự lái đi khảo sát mặt bằng chi nhánh mới",
     "Văn phòng DEGO — 12 Nguyễn Huệ, Q.1", "234 Quốc lộ 13, TP.Thủ Đức"),
    (4, "05:30", 12, TYPE_CAR, DRV_ONGOING, True,  "51D-668.25",
     "Tự lái đi công tác miền Tây: làm việc với ba nhà cung cấp gạo tại Cần Thơ "
     "và An Giang, khảo sát kho trung chuyển, ghé lấy mẫu bao bì mới rồi quay về "
     "trong ngày nếu kịp chuyến phà",
     "Văn phòng DEGO — 12 Nguyễn Huệ, Q.1", "Cần Thơ — An Giang"),
    (5, "10:00", 5, TYPE_DELIVERY, DRV_WAITING, False, "51D-982.44",
     "Giao hàng mẫu cho hội chợ triển lãm",
     "Kho Thủ Đức — 45 Đường số 8, P.Linh Trung, TP.Thủ Đức, TP.Hồ Chí Minh",
     "Trung tâm Hội chợ và Triển lãm Sài Gòn (SECC) — 799 Nguyễn Văn Linh, Q.7"),
]

#  Trường riêng của phiếu GIAO HÀNG, gắn theo thứ tự các phiếu TYPE_DELIVERY.
DELIVERY_EXTRA = [
    ("Thùng carton mẫu 3 lớp", "12 thùng · 40x30x30cm",
     "Kho Bình Chánh", "0909112233", "Chị Hạnh — Phòng Mua hàng", "0938445566"),
    ("Hàng tồn kho tổng hợp", "8 pallet · ~3 tấn",
     "Thủ kho Bình Chánh", "0909112233", "Thủ kho Thủ Đức", "0912778899"),
    ("Sản phẩm trưng bày hội chợ", "3 kiện · hàng dễ vỡ",
     "Thủ kho Thủ Đức", "0912778899", "Ban tổ chức gian hàng B12", "0977334455"),
]


def _resolve_user(db, user_id: int | None, email: str | None) -> User | None:
    """Tài khoản đích: theo `--user`, theo `--email`, hoặc PHIÊN ĐĂNG NHẬP GẦN NHẤT.

    Không đặt cứng một id mặc định: id khác nhau giữa các máy, mà đặt sai thì lỗi
    biểu hiện ra là "màn hình rỗng" — giống hệt lúc chưa chạy script.
    """
    if user_id:
        return db.get(User, user_id)
    if email:
        return db.query(User).filter(User.email == email).first()
    last = db.query(LoginSession).order_by(LoginSession.id.desc()).first()
    return db.get(User, getattr(last, "user_id", 0) or 0) if last else None


def _display_name(user: User, emp: Employee | None) -> str:
    """Tên người dùng để hiển thị.

    `tab_user` KHÔNG có cột tên — tên nằm ở hồ sơ nhân sự (`tab_employee.full_name`),
    tài khoản chỉ giữ `email`. Lùi về email khi chưa gắn hồ sơ.
    """
    return (getattr(emp, "full_name", "") or "").strip() or user.email or f"user#{user.id}"


def _next_code_number(db) -> int:
    """Số thứ tự kế tiếp của mã `DX…`.

    Chép cách đọc của `service._next_booking_code` (so theo SỐ, không so theo
    chuỗi) nhưng tính MỘT LẦN rồi tự tăng, thay vì gọi lại cho từng phiếu — gọi
    lại thì phiếu chưa `flush` không được đếm và cả loạt trùng mã.
    """
    biggest = 0
    for (code,) in db.query(VehicleBooking.code).filter(VehicleBooking.code.like("DX%")).all():
        m = re.fullmatch(r"DX(\d+)", code or "")
        if m:
            biggest = max(biggest, int(m.group(1)))
    return biggest + 1


def _wipe(db, user_id: int) -> int:
    """Xóa THẬT phiếu demo CỦA RIÊNG tài khoản này (không xóa mềm — đây là rác).

    Lọc thêm `requester_id`: nhiều người cùng dùng một DB local (mỗi người một
    phiên đăng nhập), dựng cho người này mà xóa sạch theo dấu thì bộ của người kia
    biến mất giữa chừng.
    """
    rows = (db.query(VehicleBooking)
            .filter(VehicleBooking.note.like(f"%{MARKER_KEY}%"),
                    VehicleBooking.requester_id == user_id)
            .all())
    for r in rows:
        db.delete(r)
    return len(rows)


def _ensure_driver(db, user: User, emp: Employee | None) -> Driver:
    """Hồ sơ tài xế nối với tài khoản đích — tạo nếu chưa có."""
    drv = db.query(Driver).filter(Driver.user_id == user.id).first()
    if drv:
        return drv
    drv = Driver(
        user_id=user.id,
        name=_display_name(user, emp),
        email=getattr(user, "email", "") or "",
        phone=getattr(emp, "phone", "") or "",
        license_number="B2-079204001234",
        license_class="B2",
        status="available",
        is_external=False,
    )
    db.add(drv)
    db.flush()
    return drv


def main() -> int:
    ap = argparse.ArgumentParser(description="Dựng dữ liệu demo cho màn «Chuyến của tôi»")
    ap.add_argument("--user", type=int, default=0,
                    help="id tài khoản sẽ thấy các chuyến này")
    ap.add_argument("--email", default="",
                    help="tra tài khoản theo email (thay cho --user)")
    ap.add_argument("--xoa", action="store_true",
                    help="chỉ dọn dữ liệu demo (cả hồ sơ tài xế demo), không dựng lại")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        user = _resolve_user(db, args.user, args.email.strip())
        if user is None:
            print("Không tìm ra tài khoản đích. Truyền --user <id> hoặc --email <email>.")
            return 1
        emp = db.get(Employee, getattr(user, "employee_id", 0) or 0)

        removed = _wipe(db, user.id)
        print(f"Đã xóa {removed} phiếu demo cũ của tài khoản này.")

        if args.xoa:
            drv = db.query(Driver).filter(Driver.user_id == user.id).first()
            if drv is not None:
                db.delete(drv)
                print(f"Đã xóa hồ sơ tài xế demo #{drv.id}.")
            db.commit()
            return 0

        driver = _ensure_driver(db, user, emp)
        #  Tra xe theo BIỂN SỐ chứ không theo id: id khác nhau giữa các máy.
        plates = {v.license_plate: v.id for v in db.query(Vehicle).all()}

        now = datetime.now()
        seq = _next_code_number(db)
        delivery_i = 0
        for (offset, depart_at, hours, req_type, drv_status, self_drive,
             plate, trip_purpose, origin, destination) in TRIPS:
            day = (now + timedelta(days=offset)).date()
            starts_at = datetime.combine(day, datetime.strptime(depart_at, "%H:%M").time())
            ends_at = starts_at + timedelta(hours=hours)

            bk = VehicleBooking(
                code=f"DX{seq:03d}",
                request_type=req_type,
                purpose=trip_purpose,
                start_location=origin,
                end_location=destination,
                start_time=starts_at.strftime("%Y-%m-%dT%H:%M"),
                end_time=ends_at.strftime("%Y-%m-%dT%H:%M"),
                status=BK_DISPATCHED,
                driver_status=drv_status,
                is_self_drive=self_drive,
                #  Tự lái: người yêu cầu đóng vai tài xế, KHÔNG gán hồ sơ tài xế.
                assigned_driver_id=0 if self_drive else driver.id,
                assigned_vehicle_id=plates.get(plate, 0),
                dispatched_by=user.id,
                dispatched_at=(now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
                requester=_display_name(user, emp),
                requester_id=user.id,
                requester_email=getattr(user, "email", "") or "",
                requester_phone=getattr(emp, "phone", "") or "",
                requester_role=getattr(emp, "position", "") or "",
                department_id=getattr(emp, "department_id", 0) or 0,
                company_id=getattr(emp, "company_id", 0) or 0,
                note=MARKER,
                created_by=user.id,
                updated_by=user.id,
                #  Màn hình lọc «Ngày tạo» 30 ngày gần nhất — rải trong khoảng đó,
                #  không để `server_default` vì mọi phiếu sẽ trùng đúng một mốc.
                created_at=now - timedelta(days=offset + 1, hours=3),
                updated_at=now - timedelta(days=offset + 1, hours=3),
            )
            if req_type == TYPE_CAR:
                bk.passenger_count = 2 + (seq % 3)
                bk.contact_phone = getattr(emp, "phone", "") or "0909000111"
                bk.is_round_trip = offset % 2 == 0
                if self_drive:
                    bk.license_number = "B2-079204001234"
                    bk.license_class = "B2"
            else:
                (goods, size, sender, sender_phone, receiver, receiver_phone) = DELIVERY_EXTRA[delivery_i]
                delivery_i += 1
                bk.goods_name = goods
                bk.goods_size = size
                bk.sender_name = sender
                bk.sender_phone = sender_phone
                bk.receiver_name = receiver
                bk.receiver_phone = receiver_phone
                bk.special_instructions = "Gọi trước 30 phút khi tới nơi."

            db.add(bk)
            seq += 1

        db.commit()
        print(f"Đã tạo {len(TRIPS)} phiếu cho tài khoản «{_display_name(user, emp)}» "
              f"(id={user.id}), hồ sơ tài xế #{driver.id}.")
        print("Mở http://localhost:5174/vehicle-booking/my-trips để xem.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
