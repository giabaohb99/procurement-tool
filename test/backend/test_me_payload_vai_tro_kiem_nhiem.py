"""`/api/auth/me` phải trả TÊN vai trò (từ tab_user_role) và các phòng KIÊM NHIỆM.

Trước đây payload lấy `role_name` từ cột `tab_employee.role_name` đã bỏ dùng (CR-022)
nên hồ sơ luôn hiện "Chưa cập nhật"; đây là bài giữ cho lỗi đó không quay lại.

duoc-CR-755 (giai đoạn 05): kiêm nhiệm đọc bảng `tab_employee_concurrent` (cùng HOẶC khác công ty, chỉ dòng
đang hiệu lực), `kiem_nhiem` là câu *Phòng X — Công ty B (Chức vụ)* và `concurrents` có cấu trúc cho popup."""
from datetime import timedelta

from app.core.vn_time import vn_today
from app.modules.auth.controller import _me_payload
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.department_model import EmployeeDepartment
from app.modules.employee.model import Employee
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole


def _build(db):
    cty_1 = Company(code="C1", name="Công ty Một", is_active=True)
    cty_2 = Company(code="C2", name="Công ty Hai", is_active=True)
    db.add_all([cty_1, cty_2])
    db.flush()
    main = Department(code="PC", name="Phòng Chính", company_id=cty_1.id)
    extra1 = Department(code="PP1", name="Phòng Phụ A", company_id=cty_1.id)
    extra2 = Department(code="PP2", name="Phòng Phụ B", company_id=cty_2.id)
    db.add_all([main, extra1, extra2])
    db.flush()

    emp = Employee(code="NV01", full_name="Nguyễn Văn A", company_id=cty_1.id, department_id=main.id)
    db.add(emp)
    db.flush()

    user = User(email="a@dego.vn", employee_id=emp.id)
    db.add(user)
    db.flush()

    truong = Role(code="tp", name="Trưởng phòng")
    kiemtoan = Role(code="kt", name="Kiểm toán nội bộ")
    db.add_all([truong, kiemtoan])
    db.flush()
    db.add_all([
        UserRole(user_id=user.id, role_id=truong.id),
        UserRole(user_id=user.id, role_id=kiemtoan.id),
    ])
    today = vn_today()
    db.add_all([
        EmployeeDepartment(employee_id=emp.id, department_id=main.id, is_primary=True),
        #  Cùng công ty chính, có chức vụ kiêm nhiệm.
        EmployeeConcurrent(employee_id=emp.id, company_id=cty_1.id, department_id=extra1.id,
                           position_label="Phó phòng", from_date=today - timedelta(days=5)),
        #  KHÁC công ty, tắt công tắc phạm vi: vẫn hiện ở Trang cá nhân (chỉ là ghi nhận).
        EmployeeConcurrent(employee_id=emp.id, company_id=cty_2.id, department_id=extra2.id,
                           from_date=today - timedelta(days=5), counts_scope=False),
        #  Đã hết hạn và chưa bắt đầu: KHÔNG hiện.
        EmployeeConcurrent(employee_id=emp.id, company_id=cty_2.id, department_id=main.id,
                           from_date=today - timedelta(days=40), to_date=today - timedelta(days=1)),
        EmployeeConcurrent(employee_id=emp.id, company_id=cty_2.id, department_id=main.id,
                           from_date=today + timedelta(days=3)),
    ])
    db.flush()
    return user


def test_me_payload_returns_role_names_from_user_role(db):
    user = _build(db)
    payload = _me_payload(db, user)
    # Tên vai trò lấy từ tab_user_role, sắp theo tên.
    assert payload["role_names"] == ["Kiểm toán nội bộ", "Trưởng phòng"]
    # role_name (giữ tương thích cũ) = nối các tên.
    assert payload["role_name"] == "Kiểm toán nội bộ, Trưởng phòng"


def test_me_payload_kiem_nhiem_lists_effective_rows_with_company_and_position(db):
    user = _build(db)
    payload = _me_payload(db, user)
    # Chỉ dòng ĐANG HIỆU LỰC (cùng và khác công ty), KHÔNG gồm phòng chính, dòng hết hạn, dòng sắp tới; sắp theo tên.
    assert payload["kiem_nhiem"] == ["Phòng Phụ A — Công ty Một (Phó phòng)", "Phòng Phụ B — Công ty Hai"]
    # Cấu trúc cho popup phạm vi: đủ khóa, không lộ khóa `text` nội bộ; công tắc đi theo từng dòng.
    assert [(c["department_name"], c["company_name"], c["position_label"], c["counts_scope"])
            for c in payload["concurrents"]] == [
        ("Phòng Phụ A", "Công ty Một", "Phó phòng", True),
        ("Phòng Phụ B", "Công ty Hai", "", False),
    ]
    assert all(set(c) == {"department_id", "company_id", "department_name", "company_name",
                          "position_label", "counts_scope"} for c in payload["concurrents"])


def test_me_payload_no_role_no_kiem_nhiem_returns_empty(db):
    # Nhân sự có tài khoản nhưng chưa gán vai trò, chỉ có phòng chính.
    dept = Department(code="D1", name="Phòng Một", company_id=1)
    db.add(dept)
    db.flush()
    emp = Employee(code="NV02", full_name="B", company_id=1, department_id=dept.id)
    db.add(emp)
    db.flush()
    user = User(email="b@dego.vn", employee_id=emp.id)
    db.add(user)
    db.add(EmployeeDepartment(employee_id=emp.id, department_id=dept.id, is_primary=True))
    db.flush()

    payload = _me_payload(db, user)
    assert payload["role_names"] == []
    assert payload["role_name"] == ""
    assert payload["kiem_nhiem"] == []
    assert payload["concurrents"] == []


def test_me_payload_without_employee_has_no_concurrents(db):
    # Tài khoản chưa gắn nhân sự: không văng lỗi, hai khóa rỗng (giao diện vẫn dựng được trang cá nhân).
    user = User(email="khong-nhan-su@dego.vn", employee_id=0)
    db.add(user)
    db.flush()
    payload = _me_payload(db, user)
    assert payload["kiem_nhiem"] == [] and payload["concurrents"] == []
