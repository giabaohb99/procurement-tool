"""Tạo tài khoản VĂN THƯ cho nhân sự có sẵn — chạy TAY.

    docker compose exec api python -m app.seed_van_thu

Mặc định: chị **Đào Trúc Nhi (NSU206)** — có sẵn trong `tab_employee` (id 228, email
`dtnhi.degoholding@gmail.com`) nhưng CHƯA có tài khoản đăng nhập. Script này chỉ:
  1. Tạo tài khoản đăng nhập (nếu chưa có), mật khẩu = MÃ nhân viên (quy ước nội bộ).
  2. Gán vai trò `seal_clerk` (Văn thư Duyệt dấu).
  3. Xóa cache quyền.

⚠️ **KHÔNG gán công ty ở đây.** Cơ chế mới: văn thư thấy phiếu nào là do **bảng phân
công `tab_seal_clerk`** quyết (màn "Phân công văn thư"), KHÔNG theo `company_id` hồ
sơ. Chưa được phân công thì chưa thấy phiếu nào — đúng thiết kế. Admin vào màn Phân
công văn thư để gán công ty (hoặc đặt làm văn thư tổng).

Cố ý KHÔNG gắn vào `start.sh`/`seed.py`: đây là thao tác một lần cho một nhân sự cụ
thể, không phải dữ liệu mẫu tái tạo mỗi lần khởi động.
"""
import app.core.all_models  # noqa: F401 — nạp đủ model để mapper cấu hình được
from app.core.auth import hash_password, perm_cache_clear
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole

#  (mã nhân viên, vai trò, gán TẤT CẢ công ty?, làm văn thư TỔNG?).
#  Đào Trúc Nhi: văn thư cho MỌI công ty + văn thư tổng (nhận cả phiếu đa công ty).
CLERKS = [
    ("NSU206", "seal_clerk", True, True),
]

#  Gán vai trò THUẦN (không kèm công ty) — vd cho vào danh sách tài khoản Đặt xe.
#  (mã nhân viên, mã vai trò).
ROLE_GRANTS = [
    ("NSU206", "booking_requester"),   # Đào Trúc Nhi — Đặt xe (chỉ tạo yêu cầu)
]


def _ensure_role(db, role_code: str):
    """Lấy vai trò; CHƯA có thì tạo từ định nghĩa chuẩn `STD_ROLES` (một nguồn sự thật)."""
    from app.modules.role.model import Permission
    from app.seed import STD_ROLES

    role = db.query(Role).filter(Role.code == role_code).first()
    if role:
        return role
    info = STD_ROLES.get(role_code)
    if not info:
        return None
    role = Role(code=role_code, name=info["name"])
    db.add(role)
    db.flush()
    for entity, (actions, scope) in info["perms"].items():
        db.add(Permission(
            role_id=role.id, entity=entity, scope=scope,
            **{f"can_{a}": (a in actions) for a in
               ("read", "create", "write", "delete", "approve", "cancel", "print", "export")}))
    db.flush()
    return role


def _grant_clerk(db, emp_code: str, role_code: str,
                 all_companies: bool = False, as_head: bool = False) -> str:
    from app.modules.company.model import Company
    from app.modules.seal_clerk import service as clerk_service

    emp = db.query(Employee).filter(Employee.code == emp_code).first()
    if not emp:
        return f"BỎ QUA {emp_code}: không thấy nhân sự"
    role = _ensure_role(db, role_code)
    if not role:
        return f"BỎ QUA {emp_code}: không có định nghĩa vai trò {role_code}"

    #  Đăng nhập bằng MÃ nhân viên + mật khẩu = mã (quy ước nội bộ). Email lấy từ
    #  hồ sơ nếu có, để trùng với thông tin nhân sự.
    email = (emp.email or "").strip() or f"{emp_code.lower()}@dego.vn"
    user = db.query(User).filter(User.employee_id == emp.id).first()
    created = False
    if not user:
        user = User(email=email, employee_id=emp.id,
                    password_hash=hash_password(emp_code), is_active=True,
                    created_by=1, updated_by=1)
        db.add(user)
        db.flush()
        created = True
    else:
        user.is_active = True

    #  Gán vai trò văn thư nếu chưa có (KHÔNG xóa các vai trò khác của họ).
    has = (db.query(UserRole)
           .filter(UserRole.user_id == user.id, UserRole.role_id == role.id).first())
    if not has:
        db.add(UserRole(user_id=user.id, role_id=role.id, created_by=1, updated_by=1))
    db.flush()
    perm_cache_clear(user.id)
    verb = "tạo tài khoản +" if created else "đã có tài khoản,"
    msg = f"{emp_code} ({emp.full_name}): {verb} gán vai trò {role_code}"

    if all_companies:
        #  Phân công phụ trách MỌI công ty đang hoạt động (+ văn thư tổng nếu bật).
        #  `sync` đặt lại đúng danh sách — chạy lại vẫn đúng, và tự nhận công ty mới.
        cids = [c.id for c in db.query(Company).filter(Company.is_active.is_(True)).all()]
        clerk_service.sync(db, emp.id, cids, as_head, user_id=1, anchor_id=0)
        msg += f"; phụ trách {len(cids)} công ty" + (" + văn thư tổng" if as_head else "")
    return msg


def run() -> int:
    db = SessionLocal()
    try:
        for emp_code, role_code, all_companies, as_head in CLERKS:
            print(_grant_clerk(db, emp_code, role_code, all_companies, as_head))
        for emp_code, role_code in ROLE_GRANTS:
            print(_grant_clerk(db, emp_code, role_code))
        db.commit()
        print("Xong.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(run())
