"""HAI BỘ TÀI KHOẢN TEST cho "Phòng ban tự mua hàng" (bao-CR-414, 17/09/2026).

Menu DEV «Đổi tài khoản nhanh» (`frontend-v2/src/app/layouts/demo-accounts.ts`) có
thêm hai nhóm **«CR-414 · Nhà máy»** và **«CR-414 · Thu mua»**. Tệp này tạo đúng
các tài khoản đó, dựng theo ba bộ phạm vi đã chốt:

  · Bộ NHÀ MÁY (phòng «Dego Organic» tự mua hàng):
      NM_YC  — nhân sự lập phiếu (`employee`, phạm vi own);
      NM_TP  — trưởng phòng duyệt bước 1 (`dept_head`, phạm vi dept);
      NM_MUA — quản lý thu mua CỦA PHÒNG (`pur_dept_manager`, phạm vi `dept_proc`):
               chỉ thấy phiếu đã duyệt của phòng mình + phiếu được nhờ cho phòng mình;
      NM_NV  — nhân viên thu mua của phòng (`pur_staff`, phạm vi assigned).
  · Bộ THU MUA CHUNG (phòng «Sản xuất -Thu mua»):
      TM_FULL — quản lý thu mua toàn quyền (`pur_manager`, phạm vi all) — không đổi gì;
      TM_QL   — quản lý thu mua (`pur_manager`, phạm vi all, đủ quyền duyệt/sửa/hủy) + ô
                «Loại trừ phòng ban» = Dego Organic: KHÔNG thấy phiếu nhà máy, TRỪ phiếu
                nhà máy nhờ phòng mình. Ô loại trừ áp cả cho phạm vi `all` (điều kiện loại
                trừ nằm ngoài nhánh vai trò trong `core/scoping.scope_condition`);
      TM_AD   — admin thu mua (`pur_admin`, phạm vi proc) + cùng ô loại trừ như TM_QL;
      TM_NV   — nhân viên thu mua chung (`pur_staff`).
  · Cặp thường để đối chiếu «phiếu phòng khác vẫn y như cũ»:
      MKT_YC / MKT_TP ở phòng «Hành chính» (local không có phòng Marketing).

Mật khẩu = mã nhân viên, đúng quy ước của `demo-accounts.ts`.

⚠️ CHỈ chạy ở LOCAL / DEV (`seed.py` gọi khi `SEED_DEMO_ACCOUNTS` bật). `seed_prod.py`
không gọi tệp này.

⚠️ Tra phòng ban CHỈ THEO TÊN: trên CSDL local mọi phòng đều `company_id = 0` (dữ liệu
đổ từ app cũ), lọc thêm công ty là không tìm thấy phòng nào. Phòng chưa có thì bỏ qua
tài khoản đó và nói ra ở log, không tự đẻ phòng.

Chạy tay (idempotent, chạy lại không đẻ thêm bản ghi):
    docker compose exec api python -m app.seed_tai_khoan_cr414
"""
from app.core.auth import hash_password, perm_cache_clear
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole, UserScope

FACTORY_DEPT = "Dego Organic"
PURCHASING_DEPT = "Sản xuất -Thu mua"
OTHER_DEPT = "Hành chính"

#  (mã, họ tên, chức danh, mã vai trò, tên phòng ban)
ACCOUNTS = [
    ("NM_YC", "Nhân sự nhà máy (CR-414)", "Nhân viên", "employee", FACTORY_DEPT),
    ("NM_TP", "Trưởng phòng nhà máy (CR-414)", "Trưởng phòng", "dept_head", FACTORY_DEPT),
    ("NM_MUA", "Quản lý thu mua nhà máy (CR-414)", "Quản lý thu mua phòng",
     "pur_dept_manager", FACTORY_DEPT),
    ("NM_NV", "Nhân viên thu mua nhà máy (CR-414)", "Nhân viên thu mua", "pur_staff", FACTORY_DEPT),
    ("TM_FULL", "Quản lý thu mua chung (CR-414)", "Quản lý thu mua", "pur_manager", PURCHASING_DEPT),
    ("TM_QL", "Quản lý thu mua trừ nhà máy (CR-414)", "Quản lý thu mua", "pur_manager", PURCHASING_DEPT),
    ("TM_AD", "Admin thu mua trừ nhà máy (CR-414)", "Admin thu mua", "pur_admin", PURCHASING_DEPT),
    ("TM_NV", "Nhân viên thu mua chung (CR-414)", "Nhân viên thu mua", "pur_staff", PURCHASING_DEPT),
    ("MKT_YC", "Nhân sự phòng thường (CR-414)", "Nhân viên", "employee", OTHER_DEPT),
    ("MKT_TP", "Trưởng phòng thường (CR-414)", "Trưởng phòng", "dept_head", OTHER_DEPT),
]

#  Ô «Loại trừ phòng ban» gắn thêm cho tài khoản: mã → danh sách tên phòng bị loại trừ.
EXCLUDED_DEPARTMENTS = {
    "TM_QL": [FACTORY_DEPT],
    "TM_AD": [FACTORY_DEPT],
}

COMPANY_ME_ID = 1


def _find_department_id(db, name: str) -> int | None:
    row = db.query(Department.id).filter(Department.name == name).first()
    return row[0] if row else None


def _find_role(db, code: str) -> Role | None:
    return db.query(Role).filter(Role.code == code).first()


def seed_cr414_accounts(db, company_id: int = COMPANY_ME_ID) -> int:
    """Tạo/đồng bộ mười tài khoản test CR-414. Trả về số HỒ SƠ NHÂN SỰ vừa tạo mới."""
    count = 0
    for code, full_name, job_title, role_code, department_name in ACCOUNTS:
        role = _find_role(db, role_code)
        if role is None:
            print(f"  Bỏ qua {code}: chưa có vai trò «{role_code}».")
            continue
        dept_id = _find_department_id(db, department_name)
        if dept_id is None:
            print(f"  Bỏ qua {code}: chưa có phòng «{department_name}».")
            continue

        emp = db.query(Employee).filter(Employee.code == code).first()
        if not emp:
            emp = Employee(
                code=code, full_name=full_name, company_id=company_id,
                department_id=dept_id, position=job_title,
                status="official", is_active=True, created_by=1, updated_by=1,
            )
            db.add(emp)
            db.flush()
            count += 1
        else:
            #  Chạy lại thì kéo hồ sơ về đúng phòng đã hẹn — phạm vi test dựa vào phòng.
            emp.department_id = dept_id
            emp.company_id = company_id
            emp.is_active = True

        email = f"{code.lower()}@dego.test"
        user = (db.query(User).filter(User.employee_id == emp.id).first()
                or db.query(User).filter(User.email == email).first())
        if not user:
            user = User(email=email, employee_id=emp.id, is_active=True,
                        password_hash=hash_password(code), created_by=1, updated_by=1)
            db.add(user)
            db.flush()
        else:
            user.password_hash = hash_password(code)
            user.is_active = True
            user.employee_id = emp.id
            db.flush()

        db.query(UserRole).filter(UserRole.user_id == user.id).delete(synchronize_session=False)
        db.add(UserRole(user_id=user.id, role_id=role.id, created_by=1, updated_by=1))

        db.query(UserScope).filter(UserScope.user_id == user.id).delete(synchronize_session=False)
        db.add(UserScope(user_id=user.id, role_id=role.id, entity="", dim="company",
                         value=str(company_id), is_exclude=False, created_by=1, updated_by=1))
        for excluded_name in EXCLUDED_DEPARTMENTS.get(code, []):
            excluded_id = _find_department_id(db, excluded_name)
            if excluded_id is None:
                print(f"  {code}: chưa có phòng «{excluded_name}» để loại trừ, bỏ phần đó.")
                continue
            db.add(UserScope(user_id=user.id, role_id=role.id, entity="", dim="department",
                             value=str(excluded_id), is_exclude=True, created_by=1, updated_by=1))

        perm_cache_clear(user.id)

    db.commit()
    return count


if __name__ == "__main__":
    import app.core.all_models  # noqa: F401  — nạp đủ model kẻo quan hệ Department↔Company lỗi khi chạy lẻ
    from app.core.database import SessionLocal

    session = SessionLocal()
    try:
        created = seed_cr414_accounts(session)
        print(f"Xong. Tạo mới {created} hồ sơ nhân sự CR-414.")
    finally:
        session.close()
