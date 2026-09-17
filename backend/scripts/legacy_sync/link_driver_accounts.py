"""Nối tài xế với tài khoản đăng nhập của chính họ, và cấp vai trò Tài xế.

VÌ SAO CẦN BƯỚC NÀY. Đợt nạp app cũ dựng hai thứ tách rời nhau: `sync_users`
tạo hồ sơ nhân sự + tài khoản cho 134 người, còn `sync_fleet` đóng dấu
`legacy_id` lên danh mục xe / tài xế. Không bước nào nối hai bên, nên sau khi
nạp xong **cả 13 dòng `tab_driver` đều có `user_id = 0`** — trong khi 11 tài xế
thật đã có sẵn đủ hồ sơ lẫn tài khoản. Nghĩa là dữ liệu không thiếu, chỉ thiếu
sợi dây.

Thiếu sợi dây đó thì hỏng đúng một việc: tài xế đăng nhập vào KHÔNG tự thấy
chuyến của mình. Cột `user_id` là chỗ duy nhất trả lời câu "người đang đăng
nhập này có phải tài xế không, và là tài xế nào".

CÁCH KHỚP — khớp theo TÊN, và cố ý không khớp mờ:

    tab_driver.name  ==  tab_employee.full_name   (khớp CHÍNH XÁC)
    tab_employee.id  ->  tab_user.employee_id

Không dùng số điện thoại làm chốt: 10/11 tài xế có số bên app cũ mà hồ sơ nhân
sự bỏ trống, nên khớp theo số thì rụng gần hết. Không dùng khớp gần đúng (bỏ
dấu, rút gọn khoảng trắng): nối nhầm một tài xế nghĩa là người này thấy chuyến
của người kia, sai kiểu đó im lặng và khó phát hiện. Tên trùng, tên không ra
hồ sơ nào, hoặc một hồ sơ có hai tài khoản — cả ba đều BỎ QUA và in ra để người
soát tự xử, chứ không đoán.

Tài xế `is_external = 1` bỏ qua hẳn: hai dòng đó ("Tài xế thuê ngoài", "Tự lái")
là chỗ giữ chỗ của app cũ, không phải người, nên không có tài khoản nào để nối.

BƯỚC HAI — CẤP VAI TRÒ `booking_driver`. Nối được `user_id` mới xong một nửa:
đợt nạp cấp cho 134 người đúng một vai trò `employee`, nên không tài khoản tài
xế nào giữ vai trò Tài xế. Thiếu vai trò đó thì hỏng hai chỗ, cả hai đều im:

  * `require("vehicle_booking", ...)` chặn, nên tài xế bấm Nhận / Bắt đầu /
    Hoàn thành chuyến đều bị từ chối;
  * `drivers_for_dispatch()` cố ý chỉ đưa vào ô điều phối những hồ sơ nội bộ
    ĐANG giữ `booking_driver`, nên điều phối viên mở ô chọn ra chỉ thấy mỗi hai
    dòng thuê ngoài — 11 tài xế thật biến mất khỏi danh sách phân chuyến.

Vai trò này CỘNG THÊM chứ không thay `employee`: hồ sơ nhân sự, nghỉ phép, xem
tin nội bộ vẫn phải chạy như người thường.

CHẠY ĐƯỢC NHIỀU LẦN. Mặc định chỉ xem trước, `--apply` mới ghi.

    docker compose exec -e PYTHONPATH=/app api \
        python -m scripts.legacy_sync.link_driver_accounts
    docker compose exec -e PYTHONPATH=/app api \
        python -m scripts.legacy_sync.link_driver_accounts --apply
"""

import argparse
import sys

from sqlalchemy import select

import app.core.all_models  # noqa: F401  nạp đủ model để SQLAlchemy dựng xong quan hệ
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole
from app.modules.vehicle_booking.model import Driver

DRIVER_ROLE_CODE = "booking_driver"


def find_account(db, name: str) -> tuple[User | None, str]:
    """Tra tài khoản theo tên tài xế. Trả về (tài khoản, lý do bỏ qua)."""
    employees = db.execute(
        select(Employee).where(Employee.full_name == name)
    ).scalars().all()
    if not employees:
        return None, "khong co ho so nhan su nao mang ten nay"
    if len(employees) > 1:
        codes = ", ".join(e.code for e in employees)
        return None, f"{len(employees)} ho so trung ten ({codes}) — phai chon tay"

    employee = employees[0]
    users = db.execute(
        select(User).where(User.employee_id == employee.id)
    ).scalars().all()
    if not users:
        return None, f"ho so {employee.code} chua co tai khoan dang nhap"
    if len(users) > 1:
        ids = ", ".join(str(u.id) for u in users)
        return None, f"ho so {employee.code} co {len(users)} tai khoan ({ids}) — phai chon tay"
    return users[0], ""


def link(db) -> tuple[int, int]:
    """Nối tài khoản cho mọi tài xế nội bộ. Trả về (so noi moi, so bo qua)."""
    linked = 0
    skipped = 0
    for driver in db.execute(select(Driver).order_by(Driver.id)).scalars():
        tag = f"id {driver.id:<3} {driver.name[:24]:<24}"

        if driver.is_external:
            print(f"  BO QUA {tag} thue ngoai / tu lai, khong phai mot nguoi")
            continue

        user, reason = find_account(db, driver.name)
        if user is None:
            print(f"  CANH BAO {tag} {reason}")
            skipped += 1
            continue

        if driver.user_id == user.id:
            print(f"  DA CO  {tag} -> tai khoan {user.id}")
            continue
        if driver.user_id:
            #  Đang trỏ tài khoản KHÁC. Có thể người soát đã nối tay và đúng hơn
            #  script, nên không đè — chỉ báo để đi xem.
            print(f"  CANH BAO {tag} dang tro tai khoan {driver.user_id}, "
                  f"khong phai {user.id} — khong de len")
            skipped += 1
            continue

        print(f"  NOI    {tag} -> tai khoan {user.id} ({user.email})")
        driver.user_id = user.id
        #  Ô email của tài xế là thông tin liên hệ, app cũ để trống hết. Chép từ
        #  tài khoản vừa nối cho khỏi phải gõ tay — chỉ điền khi đang trống, để
        #  không đè số liên hệ riêng mà ai đó đã nhập.
        if not driver.email and user.email:
            driver.email = user.email
        linked += 1

    return linked, skipped


def grant_driver_role(db) -> int:
    """Cấp vai trò Tài xế cho mọi tài khoản đã nối. Trả về số vai trò cấp thêm."""
    print("\n=== CAP VAI TRO TAI XE ===")
    role = db.execute(
        select(Role).where(Role.code == DRIVER_ROLE_CODE)
    ).scalars().first()
    if role is None:
        print(f"  LOI    khong co vai tro {DRIVER_ROLE_CODE!r} trong tab_role — "
              f"chay seed truoc roi chay lai")
        return 0

    granted = 0
    for driver in db.execute(select(Driver).order_by(Driver.id)).scalars():
        if driver.is_external or not driver.user_id:
            continue
        tag = f"id {driver.id:<3} {driver.name[:24]:<24}"
        existing = db.execute(
            select(UserRole).where(UserRole.user_id == driver.user_id,
                                   UserRole.role_id == role.id)
        ).scalars().first()
        if existing is not None:
            print(f"  DA CO  {tag} tai khoan {driver.user_id}")
            continue
        print(f"  CAP    {tag} tai khoan {driver.user_id} <- {DRIVER_ROLE_CODE}")
        db.add(UserRole(user_id=driver.user_id, role_id=role.id))
        granted += 1
    return granted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="ghi that; bo qua thi chi xem truoc")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print("=== NOI TAI KHOAN CHO TAI XE ===")
        linked, skipped = link(db)
        #  Chạy sau `link` và trên CÙNG một phiên: lúc xem trước, `user_id` vừa
        #  gán còn nằm trong phiên chưa ghi, nên bước này vẫn thấy đủ tài xế sắp
        #  nối — xem trước ra đúng thứ mà `--apply` sẽ làm.
        db.flush()
        granted = grant_driver_role(db)
        if args.apply:
            db.commit()
        else:
            db.rollback()

        remaining = [d.id for d in db.execute(select(Driver)).scalars()
                     if not d.is_external and not d.user_id]
        print(f"\n  noi moi        : {linked}")
        print(f"  cap vai tro    : {granted}")
        print(f"  bo qua         : {skipped}")
        if remaining and args.apply:
            print(f"  CANH BAO tai xe noi bo con chua co tai khoan: {remaining}")
        print("\n  " + ("DA GHI VAO DB." if args.apply
                        else "MOI CHI XEM TRUOC — them --apply de ghi that."))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
