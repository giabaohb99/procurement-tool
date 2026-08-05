"""Seed cho môi trường THẬT (prod + dev-UAT). Chạy: python -m app.seed_prod

Chạy TỰ ĐỘNG mỗi lần api khởi động (backend/start.prod.sh) nên phải TUYỆT ĐỐI an toàn:
chỉ THÊM phần còn thiếu, KHÔNG ghi đè bất cứ dữ liệu nào người dùng đã sửa trên giao diện.

Khác `app/seed.py` (bản đầy đủ, dùng cho LOCAL):
  - KHÔNG nạp dữ liệu mẫu: công ty/NCC/sản phẩm mẫu, danh mục từ app/seed_data/*.json.
  - KHÔNG tạo tài khoản demo (DEMO*, TESTREQ...).
  - KHÔNG ghi đè hình thức thanh toán của NCC.
  - KHÔNG đồng bộ lại ma trận quyền của các vai trò chuẩn.

Việc nó làm — đúng phần tối thiểu để hệ thống chạy được:
  1. Vai trò 'admin' có đủ quyền cho MỌI entity (chìa khóa dự phòng khi ra phân hệ mới).
     Chỉ thêm entity còn thiếu.
  2. Tạo vai trò chuẩn nào CHƯA có (STD_ROLES). Vai trò đã có thì GIỮ NGUYÊN quyền đang chạy.
  3. Tài khoản quản trị đầu tiên — chỉ khi DB chưa có tài khoản admin nào (cài mới).
  4. Tài khoản quản trị Help Center + 4 khung cấu hình trang chủ HDSD (insert-only).

KHÔNG tự gán vai trò 'Nhân sự' cho tài khoản chưa có vai trò (CR-022): quyền của tài khoản chỉ
được cấp ở màn "Phân quyền tài khoản", không có đường tự cấp ngầm nào.

Muốn áp LẠI phân quyền chuẩn theo file seed (vd sau khi đổi STD_ROLES): đặt SEED_FORCE_SYNC=true
trong .env, restart api MỘT lần, rồi trả về false trước lần deploy sau.
"""
from app.core.auth import hash_password
from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.company.model import Company
from app.modules.employee.model import Employee
from app.modules.role.model import Role, Permission  # noqa: F401
from app.modules.user.model import User, UserRole

from app.seed import (ensure_admin_role, force_resync_roles,
                      seed_help_admin, seed_help_home_sections, seed_standard_roles)


def bootstrap_admin_account(db):
    """Tài khoản quản trị đầu tiên — CHỈ tạo khi DB chưa có tài khoản nào mang vai trò 'admin'.
    DB đang chạy (đã có admin) thì hàm này không đụng gì cả."""
    admin_role = db.query(Role).filter(Role.code == "admin").first()
    if not admin_role:
        return
    if db.query(UserRole).filter(UserRole.role_id == admin_role.id).first():
        return   # đã có quản trị viên -> bỏ qua

    company = db.query(Company).order_by(Company.id).first()
    if not company:
        company = Company(code="DEGO", name="CÔNG TY TNHH DEGO HOLDING",
                          tax_code="1801722464", is_active=True)
        db.add(company)
        db.commit()
        db.refresh(company)

    emp = db.query(Employee).filter(Employee.code == settings.ADMIN_CODE).first()
    if not emp:
        emp = Employee(code=settings.ADMIN_CODE, full_name="Quản trị viên",
                       company_id=company.id, position="Admin", is_active=True)
        db.add(emp)
        db.commit()
        db.refresh(emp)

    user = db.query(User).filter(User.employee_id == emp.id).first()
    if not user:
        user = User(email=settings.ADMIN_CODE, employee_id=emp.id,
                    password_hash=hash_password(settings.ADMIN_PASSWORD), is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    db.add(UserRole(user_id=user.id, role_id=admin_role.id))
    db.commit()
    print(f"Tạo tài khoản quản trị đầu tiên: {settings.ADMIN_CODE} (mật khẩu trong .env)")


def run():
    db = SessionLocal()
    try:
        ensure_admin_role(db)          # 1
        seed_standard_roles(db)        # 2 — chỉ tạo vai trò còn thiếu
        force_resync_roles(db)         # no-op trừ khi SEED_FORCE_SYNC=true
        bootstrap_admin_account(db)    # 3

        _company = db.query(Company).order_by(Company.id).first()   # 4
        seed_help_admin(db, _company.id if _company else None)
        seed_help_home_sections(db)

        print("Seed prod done (không nạp dữ liệu mẫu, không ghi đè dữ liệu đã có).")
    finally:
        db.close()


if __name__ == "__main__":
    run()
