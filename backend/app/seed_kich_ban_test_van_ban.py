"""BỘ DIỄN VIÊN cho kịch bản test phân hệ Văn bản (22/08/2026).

Vì sao cần: dữ liệu demo đang có **không diễn nổi** mấy ca quan trọng nhất của
phạm vi áp dụng (F01–F05). Đo lúc dựng tệp này:

- mỗi pháp nhân chỉ đúng **một** phòng có người;
- 4 trên 8 nhân sự của DEGO **không thuộc phòng nào**;
- không phòng nào có từ 2 người trở lên.

Mà ba ca cần kiểm lại đúng là: *loại trừ một phòng ban*, *loại trừ phòng nhưng
chừa một người trong phòng đó*, và *loại trừ vài cá nhân*. Không có phòng nào
đủ người thì bấm xong không phân biệt được "luật chạy đúng" với "vốn dĩ chẳng
ai thấy".

Tệp này tạo **9 nhân sự ở 3 phòng của DEGO**, đủ để mọi ca đều có ít nhất một
người PHẢI thấy và một người PHẢI KHÔNG thấy — kiểm được cả hai chiều, chứ một
chiều thì luật sai kiểu "không ai thấy gì" vẫn qua.

Chỉ chạy ở LOCAL. `seed_prod.py` KHÔNG gọi tệp này: mật khẩu đoán được.

Chạy: `docker compose exec api python -m app.seed_kich_ban_test_van_ban`
"""
from app.core.auth import hash_password
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole, UserScope

ROLE_CODE = "nhanvien_docvanban"
ROLE_NAME = "Nhân viên đọc văn bản (Kịch bản test)"

#: Pháp nhân dựng bộ diễn viên — DEGO, nơi có sẵn luồng duyệt nhiều bước.
COMPANY_CODE = "DEGO"

#: (mã, họ tên, tên phòng). Ba phòng, mỗi phòng ba người: đủ để loại trừ cả
#: phòng mà vẫn còn phòng khác đối chứng, và chừa một người trong phòng bị loại.
CAST = [
    ("TVB_NS1", "Nguyễn Văn Nhân Sự Một", "Phòng Nhân sự - Hành chính"),
    ("TVB_NS2", "Trần Thị Nhân Sự Hai", "Phòng Nhân sự - Hành chính"),
    ("TVB_NS3", "Lê Văn Nhân Sự Ba", "Phòng Nhân sự - Hành chính"),
    ("TVB_KT1", "Phạm Thị Kế Toán Một", "Phòng Kế toán"),
    ("TVB_KT2", "Hoàng Văn Kế Toán Hai", "Phòng Kế toán"),
    ("TVB_KT3", "Đỗ Thị Kế Toán Ba", "Phòng Kế toán"),
    ("TVB_KD1", "Vũ Văn Kinh Doanh Một", "Phòng Kinh doanh"),
    ("TVB_KD2", "Bùi Thị Kinh Doanh Hai", "Phòng Kinh doanh"),
    ("TVB_KD3", "Đặng Văn Kinh Doanh Ba", "Phòng Kinh doanh"),
]

#: Quyền của một NHÂN VIÊN THƯỜNG — cố ý hẹp.
#:
#: ⚠️ KHÔNG cấp `document: read`. Người thường không được vào màn danh sách văn
#: bản; họ chỉ thấy văn bản qua «Văn bản áp dụng cho tôi» và qua đường dẫn trực
#: tiếp. Cấp `document: read` là kịch bản mất luôn ý nghĩa — ai cũng thấy mọi
#: thứ và không phân biệt được phạm vi có chạy hay không.
PERMISSIONS = {
    "company": (["read"], "all"),
    "department": (["read"], "all"),
    "employee": (["read"], "all"),
}


def _role(db) -> Role:
    role = db.query(Role).filter(Role.code == ROLE_CODE).first()
    if not role:
        role = Role(code=ROLE_CODE, name=ROLE_NAME)
        db.add(role)
        db.flush()

    #  Ghi đè quyền mỗi lần chạy: sửa `QUYEN` rồi chạy lại là áp được ngay.
    db.query(Permission).filter(Permission.role_id == role.id).delete(synchronize_session=False)
    db.flush()
    for entity, (actions, scope) in PERMISSIONS.items():
        db.add(Permission(
            role_id=role.id, entity=entity, scope=scope,
            **{f"can_{a}": (a in actions) for a in
               ("read", "create", "write", "delete", "approve", "cancel", "print", "export")},
        ))
    db.flush()
    return role


def seed_document_test_scenario(db) -> int:
    company = db.query(Company).filter(Company.code == COMPANY_CODE).first()
    if company is None:
        raise SystemExit(f"Không thấy pháp nhân {COMPANY_CODE} — chạy `python -m app.seed` trước.")

    role = _role(db)
    count = 0

    for code, full_name, department_name in CAST:
        department = (
            db.query(Department)
            .filter(Department.company_id == company.id, Department.name == department_name)
            .first()
        )
        if department is None:
            raise SystemExit(f"Không thấy phòng «{department_name}» ở {COMPANY_CODE}.")

        emp = db.query(Employee).filter(Employee.code == code).first()
        if emp is None:
            emp = Employee(code=code, full_name=full_name, company_id=company.id,
                           department_id=department.id, position="Nhân viên",
                           status="Chính thức", is_active=True,
                           created_by=1, updated_by=1)
            db.add(emp)
            db.flush()
            count += 1
        else:
            #  Đưa về đúng trạng thái đã hẹn — người thử có thể đã sửa tay.
            emp.department_id = department.id
            emp.company_id = company.id
            emp.is_active = True

        email = f"{code.lower()}@dego.test"
        user = db.query(User).filter(User.email == email).first()
        if user is None:
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
        db.add(UserScope(user_id=user.id, role_id=role.id, entity="",
                         dim="company", value=str(company.id), is_exclude=False,
                         created_by=1, updated_by=1))

    db.commit()

    #  Hồ sơ quyền được nhớ trong tiến trình `api` 60 giây (`_PERM_CACHE`). Seed
    #  chạy ở TIẾN TRÌNH KHÁC nên không xóa được cache đó — nói ra để người chạy
    #  không tưởng là quyền chưa vào.
    return count


if __name__ == "__main__":
    from app.core.database import SessionLocal

    with SessionLocal() as db:
        new = seed_document_test_scenario(db)
    print(f"Xong. Thêm mới {new} nhân sự; toàn bộ {len(CAST)} tài khoản đã đặt lại mật khẩu.")
    print("Đăng nhập: mã nhân viên, mật khẩu = chính mã đó (vd TVB_NS1 / TVB_NS1).")
    print("⚠️ Chờ ~60 giây hoặc restart `api` nếu vừa đổi quyền — có cache 60s.")
