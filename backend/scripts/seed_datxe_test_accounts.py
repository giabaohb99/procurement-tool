"""Đặt lại MẬT KHẨU (dego123) cho 7 tài khoản TEST phân quyền Đặt xe.

Vai trò / phạm vi / phòng ban của các tài khoản này ĐÃ được thiết lập sẵn — script
này CHỈ đặt lại mật khẩu và bật `is_active`, KHÔNG đụng tới vai trò / phạm vi /
phòng ban.

⚠️ **KHÔNG GHI EMAIL NỮA** (bao-CR-380, 11/09/2026). Bản cũ nhận diện tài khoản
bằng `employee_id` rồi *dập* email `@dego.com` lên đó, để nút "Đổi tài khoản
nhanh" đăng nhập bằng email. Danh sách ngày ấy lệch một mã, nên mỗi email bị dập
lên người kế bên: tài khoản thật của **5 nhân sự** (NSU055, NSU170, NSU171,
NSU202, NSU203) mất email đăng nhập của chính mình, và menu demo bấm tên này ra
người khác. Tệ hơn: vì nhận diện bằng `employee_id` chứ không bằng email, chạy
lại script bao nhiêu lần cũng không tự sửa được — dòng hỏng sống sót mọi lần.

Nay menu demo đăng nhập bằng **mã nhân viên** (`authenticate` tra `Employee.code`
rồi lấy tài khoản đang hoạt động của người đó), nên không cần email cố định nữa.
Bỏ hẳn nhịp ghi email là bỏ luôn cả lớp lỗi đó: script không còn đường nào chạm
vào dữ liệu thật của nhân sự.

Dữ liệu đã lệch trên DB dev thì chạy `scripts.repair_datxe_account_emails` để nắn lại.

Chạy (LOCAL/DEV):  docker compose exec -T api python -m scripts.seed_datxe_test_accounts
"""
import app.core.all_models  # noqa: F401 — nạp toàn bộ model để mapper đủ quan hệ
from app.core.auth import hash_password, perm_cache_clear
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.user.model import User

#  Mã nhân viên — đây là thứ menu demo gõ vào ô đăng nhập.
ACCOUNTS = [
    "NSU204",  # Dương Hải Yến — Nhân sự
    "NSU203",  # Nguyễn Đỗ Quyên — Trưởng bộ phận (dept_head)
    "NSU172",  # Hồ Ngọc Quế Anh — Nhân sự
    "NSU171",  # Nguyễn Minh Toàn — Trưởng bộ phận (dept_head)
    "NSU056",  # Bùi Huỳnh Trường Thành — Điều phối viên (booking_dispatcher)
    "NSU060",  # Lê Tấn Nhựt — Tài xế (booking_driver)
    "NSU058",  # Trần Quốc Thái — Tài xế (booking_driver)
]
PASSWORD = "dego123"


def run():
    db = SessionLocal()
    try:
        for code in ACCOUNTS:
            emp = db.query(Employee).filter(Employee.code == code).first()
            if emp is None:
                print(f"  ! Không thấy nhân viên {code} — bỏ qua")
                continue
            #  Ưu tiên tài khoản ĐANG HOẠT ĐỘNG — cùng luật với `auth.authenticate`,
            #  để thứ đặt mật khẩu ở đây đúng là thứ đăng nhập vào sau đó.
            user = (
                db.query(User)
                .filter(User.employee_id == emp.id, User.is_active.is_(True))
                .first()
                or db.query(User).filter(User.employee_id == emp.id).first()
            )
            if user is None:
                #  Email lấy theo hồ sơ nhân sự chứ không bịa ra: tài khoản mới
                #  vẫn cần một email để không đụng ràng buộc, và email của chính
                #  người đó là giá trị duy nhất chắc chắn không cướp của ai.
                user = User(employee_id=emp.id, email=emp.email or "", is_active=True)
                db.add(user)
                print(f"  + Tạo tài khoản đăng nhập cho {code}")
            user.password_hash = hash_password(PASSWORD)
            user.is_active = True
            db.commit()
            perm_cache_clear(user.id)
            print(f"  ✓ {code} · {emp.full_name} · mật khẩu = {PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
