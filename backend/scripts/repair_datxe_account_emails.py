"""Nắn lại EMAIL ĐĂNG NHẬP đã bị bản seed Đặt xe cũ dập lên nhầm người.

Bối cảnh (bao-CR-380, 11/09/2026). `seed_datxe_test_accounts` bản cũ giữ một danh
sách `(mã nhân viên, email @dego.com)` lệch một bậc, rồi ghi email đó đè lên tài
khoản của người mang mã kia. Hậu quả trên DB dev: **5 nhân sự thật** đang đăng
nhập bằng email của đồng nghiệp —

    NSU055 Trần Thị Hương Tuyền   ← bhtthanh.idaglobal@dego.com
    NSU170 Lê Thị Cẩm Hường       ← nmtoan.idagroup@dego.com
    NSU171 Nguyễn Minh Toàn       ← hnqanh.idagroup@dego.com
    NSU202 Võ Thanh Ngân          ← ndquyen.idagroup@dego.com
    NSU203 Nguyễn Đỗ Quyên        ← duonghaiyen.idagroup@dego.com

và menu "Đổi tài khoản nhanh" bấm một tên ra một người khác (khách bắt được trên
dev ngày 11/09/2026). Hai mã còn lại (NSU058, NSU060) đúng người nhưng vẫn mang
email `@dego.com` do seed ghi vào — nay không dùng tới nữa nên trả về luôn.

Nguồn sự thật là `tab_employee.email`. Script chỉ đụng vào tài khoản có email kết
thúc bằng `@dego.com` — tức đúng dấu vết seed để lại; email người dùng tự đổi
hoặc email hệ thống khác đều không khớp điều kiện đó nên nằm ngoài tầm với.

Chạy lại được nhiều lần. Chạy (DEV/LOCAL):
    docker compose exec -T api python -m scripts.repair_datxe_account_emails
"""
import app.core.all_models  # noqa: F401 — nạp toàn bộ model để mapper đủ quan hệ
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.user.model import User

#  10 mã: 7 tài khoản test + 3 người bị email dập lên oan (NSU055, NSU170, NSU202).
CODES = [
    "NSU055", "NSU056", "NSU058", "NSU060", "NSU170",
    "NSU171", "NSU172", "NSU202", "NSU203", "NSU204",
]
SEED_EMAIL_SUFFIX = "@dego.com"


def run():
    db = SessionLocal()
    fixed = 0
    try:
        for code in CODES:
            emp = db.query(Employee).filter(Employee.code == code).first()
            if emp is None:
                print(f"  - {code}: không có hồ sơ nhân sự — bỏ qua")
                continue

            users = db.query(User).filter(User.employee_id == emp.id).all()
            if not users:
                print(f"  - {code}: chưa có tài khoản đăng nhập — bỏ qua")
                continue

            for user in users:
                current = (user.email or "").strip()
                if not current.endswith(SEED_EMAIL_SUFFIX):
                    continue  # không phải dấu vết của seed — không đụng tới

                target = (emp.email or "").strip()
                if not target:
                    print(f"  ! {code}: hồ sơ nhân sự bỏ trống email — không biết trả về đâu")
                    continue
                if target == current:
                    continue

                #  `tab_user.email` là thứ `authenticate` tra đầu tiên: hai tài khoản
                #  cùng email thì người đăng nhập rơi vào cái nào là chuyện hên xui.
                taken = (
                    db.query(User)
                    .filter(User.email == target, User.id != user.id)
                    .first()
                )
                if taken:
                    print(
                        f"  ! {code}: email {target} đang thuộc tài khoản #{taken.id} "
                        f"(nhân sự {taken.employee_id}) — bỏ qua, phải gỡ tay"
                    )
                    continue

                print(f"  ✓ {code} {emp.full_name}: tài khoản #{user.id}  {current} → {target}")
                user.email = target
                fixed += 1

        db.commit()
        print(f"\nXong. Đã nắn {fixed} tài khoản.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
