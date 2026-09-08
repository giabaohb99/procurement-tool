"""BẢY TÀI KHOẢN TEST của menu «Đổi tài khoản nhanh» (24/08/2026).

Menu DEV ở `frontend-v2/src/app/layouts/demo-accounts.ts` bày một nhóm
**«Tài khoản Test (Data)»** gồm bảy mã: TESTREQ · DEMONV · DEMOTP · DEMOQL ·
DEMOAD · DEMOTP2 · DEMOTP3. Trên CSDL local **không có mã nào trong bảy mã đó** —
`seed.py::seed_demo_accounts` chỉ *đồng bộ mật khẩu* cho chúng nếu hồ sơ nhân sự
đã tồn tại (dấu vết của một lần nạp dữ liệu thật), còn máy dựng mới thì bấm vào
là ăn toast "Không đăng nhập được … kiểm lại dữ liệu seed". Bảy dòng chết trong
một menu chín dòng.

Tệp này tạo chúng, và tiện thể dựng luôn **hai ví dụ phân quyền Văn bản** mà
người dùng hỏi tới:

  · DEMONV — CHỈ XEM văn bản, không thao tác được gì (vai trò `vanban_xem`);
  · DEMOTP — soạn và SỬA được nhưng KHÔNG xóa, KHÔNG duyệt (`vanban_sua`).

Mọi vai trò đều khai ở `seed.py::STD_ROLES` để mọi môi trường có sẵn mẫu; tệp
này chỉ *gán* chúng cho tài khoản demo — vai chính ở `ACCOUNTS`, vai gán thêm ở
`EXTRA_ROLES`.

⚠️ CHỈ chạy ở LOCAL (`seed.py`). `seed_prod.py` không gọi tệp này: mật khẩu bằng
đúng mã nhân viên, tuyệt đối không để lên hệ thật.

⚠️ KHÔNG đụng tới bảy vai trò chuẩn mà nó gán (`employee`, `dept_head`,
`company_head`, `pur_admin`, `vanthu_phapnhan`, `vanban_xem`, `vanban_sua`) —
tệp này chỉ đọc chúng ra để gán. Vai trò nào chưa có thì bỏ qua tài khoản đó
thay vì tự đẻ vai trò rỗng: một vai trò không có dòng quyền nào trông y như một
vai trò bị mất quyền, và người đi tìm nguyên nhân sẽ mất buổi chiều.
"""
from app.core.auth import hash_password, perm_cache_clear
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole, UserScope

#  (mã, họ tên, chức danh, mã vai trò, tên phòng ban, ghi chú cho người đọc log)
#
#  Phòng ban khác nhau là CÓ Ý: ba trưởng phòng nằm ba phòng thì phạm vi dữ liệu
#  `dept` mới nhìn ra được — cùng một màn danh sách, mỗi người thấy một tập phiếu.
ACCOUNTS = [
    ("TESTREQ", "Nhân sự tạo phiếu (Test)", "Nhân viên",
     "employee", "Phòng Kinh doanh", "người tạo phiếu test"),
    ("DEMONV", "Nhân viên xem văn bản (Demo)", "Nhân viên",
     "employee", "Phòng Kinh doanh", "chỉ XEM văn bản"),
    ("DEMOTP", "Trưởng phòng Kinh doanh (Demo)", "Trưởng phòng",
     "dept_head", "Phòng Kinh doanh", "sửa văn bản, KHÔNG xóa"),
    ("DEMOTP2", "Trưởng phòng Kế toán (Demo)", "Trưởng phòng",
     "dept_head", "Phòng Kế toán", "trưởng phòng 2"),
    ("DEMOTP3", "Trưởng phòng Sản xuất (Demo)", "Trưởng phòng",
     "dept_head", "Phòng Sản xuất", "trưởng phòng 3"),
    ("DEMOQL", "Quản lý công ty (Demo)", "Quản lý",
     "company_head", "Ban Giám đốc", "duyệt văn bản"),
    ("DEMOAD", "Admin thu mua (Demo)", "Admin",
     "pur_admin", "Phòng Thu mua", "admin thu mua"),
]

#  Vai trò gán THÊM ngoài vai trò chính ở `ACCOUNTS`. Cộng dồn chứ không thay
#  thế — hệ phân quyền là hợp (OR) của mọi vai trò người đó giữ.
EXTRA_ROLES = {
    "DEMONV": ["vanban_xem"],
    "DEMOTP": ["vanban_sua"],
    "DEMOQL": [
        #  Quản lý công ty duyệt được văn bản của pháp nhân mình — dùng lại vai
        #  trò sẵn có thay vì đẻ thêm một vai trò gần giống.
        "vanthu_phapnhan",
        #  `company_head` cố ý CHỈ XEM trên cả 13 nhóm dữ liệu, nên một mình nó
        #  không mở được phần Giao hàng nhiều lần của ĐMH (màn hình đòi
        #  `purchase_order.write`). Gán thêm vai thu mua để tài khoản demo này
        #  bấm vào là nhập được tiến độ giao, thay vì nới quyền ghi cho
        #  `company_head` — nới ở đó thì MỌI trưởng pháp nhân sửa được chứng từ.
        "pur_manager",
    ],
}

COMPANY_ME_ID = 1


def _department_id(db, name: str, company_id: int) -> int | None:
    row = (db.query(Department.id)
           .filter(Department.name == name, Department.company_id == company_id)
           .first())
    return row[0] if row else None


def _role(db, code: str) -> Role | None:
    return db.query(Role).filter(Role.code == code).first()


def seed_test_accounts(db, company_id: int = COMPANY_ME_ID) -> int:
    """Tạo/đồng bộ bảy tài khoản test. Chạy lại nhiều lần không đẻ thêm bản ghi.

    Trả về số HỒ SƠ NHÂN SỰ vừa tạo mới (0 nghĩa là đã có sẵn cả bảy).
    """
    count = 0

    for code, full_name, job_title, role_code, department_name, _note in ACCOUNTS:
        role = _role(db, role_code)
        if role is None:
            print(f"  Bỏ qua {code}: chưa có vai trò «{role_code}».")
            continue

        emp = db.query(Employee).filter(Employee.code == code).first()
        if not emp:
            emp = Employee(
                code=code, full_name=full_name, company_id=company_id,
                department_id=_department_id(db, department_name, company_id),
                position=job_title,
                status="official",   # B-03: MÃ, xem app/core/status_codes.EMPLOYEE_STATUS
                is_active=True, created_by=1, updated_by=1,
            )
            db.add(emp)
            db.flush()
            count += 1

        #  Mật khẩu = mã nhân viên, đúng quy ước của `demo-accounts.ts` và của bộ
        #  E2E (`test/e2e` đăng nhập TESTREQ/DEMONV/DEMOTP bằng chính mã).
        #  Đăng nhập bằng MÃ nhân sự, nên `email` chỉ là một địa chỉ giữ chỗ.
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

        #  Gán lại vai trò mỗi lần seed: dữ liệu demo phải về đúng trạng thái đã
        #  hẹn, kể cả khi ai đó vừa sửa tay trên màn Phân quyền lúc thử.
        db.query(UserRole).filter(UserRole.user_id == user.id).delete(synchronize_session=False)
        db.add(UserRole(user_id=user.id, role_id=role.id, created_by=1, updated_by=1))

        extra_role_ids = set()
        for extra_code in EXTRA_ROLES.get(code, []):
            extra_role = _role(db, extra_code)
            if extra_role is None:
                print(f"  {code}: chưa có vai trò «{extra_code}», bỏ phần đó.")
                continue
            extra_role_ids.add(extra_role.id)
            db.add(UserRole(user_id=user.id, role_id=extra_role.id, created_by=1, updated_by=1))

        #  Phạm vi dữ liệu: đúng pháp nhân của mình. Không có dòng này thì vai trò
        #  phạm vi `company` không biết "công ty nào" và `apply_scope` chặn sạch
        #  (B-07/CR-131 — scope không dựng được điều kiện thì trả `false()`).
        db.query(UserScope).filter(UserScope.user_id == user.id).delete(synchronize_session=False)
        for r in {role.id} | extra_role_ids:
            db.add(UserScope(user_id=user.id, role_id=r, entity="", dim="company",
                             value=str(company_id), is_exclude=False,
                             created_by=1, updated_by=1))

        #  Bộ đệm quyền giữ 60 giây (`_PERM_CACHE`), không xóa thì vừa seed xong
        #  đăng nhập vào vẫn thấy quyền cũ.
        perm_cache_clear(user.id)

    db.commit()
    return count
