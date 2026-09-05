"""Đồng bộ MẬT KHẨU (dego123) + EMAIL cho 7 tài khoản TEST phân quyền Đặt xe.

Vai trò / phạm vi / phòng ban của các tài khoản này ĐÃ được thiết lập sẵn — script
này CHỈ đặt lại mật khẩu = `dego123` và đảm bảo email `@dego.com` (để nút "Đổi tài
khoản nhanh" ở bản DEV login được), KHÔNG đụng tới vai trò / phạm vi / phòng ban.

Chạy (LOCAL/DEV):  docker compose exec -T api python -m scripts.seed_datxe_test_accounts
"""
import app.core.all_models  # noqa: F401 — nạp toàn bộ model để mapper đủ quan hệ
from app.core.auth import hash_password, perm_cache_clear
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.user.model import User

#  (mã nhân viên, email đăng nhập mong muốn) — vai trò/phòng ban đã set sẵn.
ACCOUNTS = [
    ("NSU203", "duonghaiyen.idagroup@dego.com"),   # NS1 — Nhân sự
    ("NSU202", "ndquyen.idagroup@dego.com"),        # TP1 — Trưởng bộ phận
    ("NSU171", "hnqanh.idagroup@dego.com"),         # NS2 — Nhân sự
    ("NSU170", "nmtoan.idagroup@dego.com"),         # TP2 — Trưởng bộ phận
    ("NSU055", "bhtthanh.idaglobal@dego.com"),      # ĐPV — Điều phối viên
    ("NSU060", "ltnhut.idagroup@dego.com"),         # TX1 — Lê Tấn Nhựt (emp#82)
    ("NSU058", "tqthai.idagroup@dego.com"),         # TX2 — Trần Quốc Thái (emp#80)
]
PASSWORD = "dego123"


def run():
    db = SessionLocal()
    try:
        for code, email in ACCOUNTS:
            emp = db.query(Employee).filter(Employee.code == code).first()
            if emp is None:
                print(f"  ! Không thấy nhân viên {code} — bỏ qua")
                continue
            gmail = email.replace("@dego.com", "@gmail.com")
            user = (
                db.query(User).filter(User.employee_id == emp.id).first()
                or db.query(User).filter(User.email == email).first()
                or db.query(User).filter(User.email == gmail).first()
            )
            if user is None:
                user = User(employee_id=emp.id, email=email, is_active=True)
                db.add(user)
                print(f"  + Tạo tài khoản đăng nhập cho {code} ({email})")
            user.email = email
            user.password_hash = hash_password(PASSWORD)
            user.is_active = True
            db.commit()
            perm_cache_clear(user.id)
            print(f"  ✓ {code} · {email} · mật khẩu = {PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
