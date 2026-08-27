"""VĂN THƯ Ở TỪNG PHÁP NHÂN CON — tài khoản demo cho luồng clone (20/08/2026).

Vì sao cần: ban hành một văn bản của Tập đoàn sinh ra **một bản nháp ở mỗi pháp
nhân con**, để nơi đó sửa lại cho đúng công ty mình rồi tự ban hành. Nhưng
11/12 pháp nhân con **chưa có một nhân sự nào** trong hệ, nên bản nháp nằm đó
không ai mở được — nửa sau của tính năng không diễn được.

Chỉ chạy ở LOCAL (`seed.py`). `seed_prod.py` không gọi tệp này: đây là tài khoản
demo, mật khẩu đoán được, tuyệt đối không để lên môi trường thật.

⚠️ KHÔNG đụng tới `TESTMEDEGO` / `TESTCONAGRI` và vai trò `vanthu_cty` của
chúng. Đó là bộ thử của người khác, và `vanthu_cty` cố ý chỉ có `document: read`.
Tệp này tạo vai trò RIÊNG.
"""
from app.core.auth import hash_password
from app.modules.company.model import Company
from app.modules.employee.model import Employee
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole, UserScope

ROLE_CODE = "vanthu_phapnhan"
ROLE_NAME = "Văn thư pháp nhân con (Demo)"

#  Pháp nhân ban hành của bộ dữ liệu demo — nơi văn bản gốc đứng tên, không phải
#  nơi nhận bản clone nên không tạo văn thư ở đây.
COMPANY_ME_ID = 1

#  Mật khẩu = mã nhân viên, đúng quy ước của các tài khoản demo sẵn có.
#  Đây là CSDL trên máy lập trình, không phải hệ thật.

PERMISSIONS = {
    #  Đủ để làm trọn việc của mình trên bản clone: mở ra, sửa, gửi duyệt, ban
    #  hành. `scope: company` — chỉ thấy văn bản của chính pháp nhân mình, và đó
    #  là điều đáng cho người xem demo thấy.
    "document": (["read", "create", "write", "approve", "print", "export"], "company"),
    #  Đọc danh mục: thiếu mấy dòng này thì form Tạo văn bản rỗng sạch mọi ô bắt
    #  buộc (loại, pháp nhân, phòng, người chịu trách nhiệm) và không tạo nổi
    #  văn bản nào — đã bị đúng lỗi đó với vai trò `vanthu_cty`.
    "doc_type": (["read"], "all"),
    "company": (["read"], "all"),
    "department": (["read"], "all"),
    "employee": (["read"], "all"),
    #  Tên entity phải khớp `core/permissions.py::ENTITIES` — là `document_book`,
    #  KHÔNG phải `doc_book`. Gõ sai thì `require("document_book", "read")` ở
    #  `book_controller` không thấy dòng nào, văn thư ăn 403 lúc mở màn Tạo văn
    #  bản và ô «Vào sổ» chỉ còn mỗi mục "Không vào sổ" — hỏng đúng việc chính
    #  của họ mà không có câu báo nào.
    "document_book": (["read"], "all"),
    "approval_flow": (["read"], "all"),
}


def _create_role(db) -> Role:
    role = db.query(Role).filter(Role.code == ROLE_CODE).first()
    if not role:
        role = Role(code=ROLE_CODE, name=ROLE_NAME)
        db.add(role)
        db.flush()

    #  Ghi đè quyền mỗi lần seed: sửa `QUYEN` ở trên rồi chạy lại là áp được
    #  ngay, không phải nhớ xóa tay. Vai trò này chỉ do tệp này quản.
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


def _admin_department_id(db) -> int | None:
    """Phòng của người nộp quyết định ai duyệt — để trống thì luồng dò theo phiếu."""
    from app.modules.department.model import Department

    row = db.query(Department.id).filter(Department.name == "Phòng Hành chính").first()
    return row[0] if row else None


def seed_subsidiary_document_data(db) -> int:
    """Mỗi pháp nhân con một văn thư. Chạy lại nhiều lần không đẻ thêm bản ghi."""
    role = _create_role(db)
    dept_id = _admin_department_id(db)
    count = 0

    companies = (
        db.query(Company)
        .filter(Company.is_active.is_(True), Company.id != COMPANY_ME_ID)
        .order_by(Company.id)
        .all()
    )

    for company in companies:
        #  Mã lấy từ `issue_code` (chỉ chữ và số) chứ không lấy `code` — `code`
        #  chứa dấu và khoảng trắng ("HỘ KD DR.XANH"), gõ vào ô đăng nhập thì sai.
        code = (company.issue_code or "").strip() or f"CTY{company.id}"
        emp_code = f"VT{code}"

        emp = db.query(Employee).filter(Employee.code == emp_code).first()
        if not emp:
            emp = Employee(
                code=emp_code,
                full_name=f"Văn thư {code}",
                company_id=company.id,
                department_id=dept_id,
                position="Văn thư",
                status="official",     # B-03: MÃ, xem app/core/status_codes.EMPLOYEE_STATUS
                is_active=True,
                created_by=1, updated_by=1,
            )
            db.add(emp)
            db.flush()
            count += 1

        email = f"{emp_code.lower()}@dego.test"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, employee_id=emp.id,
                        password_hash=hash_password(emp_code), is_active=True,
                        created_by=1, updated_by=1)
            db.add(user)
            db.flush()
        else:
            user.password_hash = hash_password(emp_code)
            user.is_active = True
            db.flush()

        #  Gán lại vai trò + phạm vi mỗi lần seed: dữ liệu demo phải về đúng
        #  trạng thái đã hẹn, kể cả khi ai đó sửa tay trên giao diện lúc thử.
        db.query(UserRole).filter(UserRole.user_id == user.id).delete(synchronize_session=False)
        db.add(UserRole(user_id=user.id, role_id=role.id, created_by=1, updated_by=1))

        db.query(UserScope).filter(UserScope.user_id == user.id,
                                   UserScope.role_id == role.id).delete(synchronize_session=False)
        #  Phạm vi dữ liệu = ĐÚNG pháp nhân của mình. Đây là thứ làm demo có
        #  nghĩa: mở danh sách văn bản chỉ thấy của công ty mình.
        db.add(UserScope(user_id=user.id, role_id=role.id, entity="",
                         dim="company", value=str(company.id), is_exclude=False,
                         created_by=1, updated_by=1))

    db.commit()
    return count
