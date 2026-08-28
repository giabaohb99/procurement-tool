"""`/api/auth/me` phải trả TÊN vai trò (từ tab_user_role) và các phòng KIÊM NHIỆM.

Trước đây payload lấy `role_name` từ cột `tab_employee.role_name` đã bỏ dùng (CR-022)
nên hồ sơ luôn hiện "Chưa cập nhật"; đây là bài giữ cho lỗi đó không quay lại."""
from app.modules.auth.controller import _me_payload
from app.modules.department.model import Department
from app.modules.employee.department_model import EmployeeDepartment
from app.modules.employee.model import Employee
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole


def _build(db):
    main = Department(code="PC", name="Phòng Chính", company_id=1)
    extra1 = Department(code="PP1", name="Phòng Phụ A", company_id=1)
    extra2 = Department(code="PP2", name="Phòng Phụ B", company_id=1)
    db.add_all([main, extra1, extra2])
    db.flush()

    emp = Employee(code="NV01", full_name="Nguyễn Văn A", company_id=1, department_id=main.id)
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
    db.add_all([
        EmployeeDepartment(employee_id=emp.id, department_id=main.id, is_primary=True),
        EmployeeDepartment(employee_id=emp.id, department_id=extra1.id, is_primary=False),
        EmployeeDepartment(employee_id=emp.id, department_id=extra2.id, is_primary=False),
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


def test_me_payload_kiem_nhiem_lists_only_extra_departments(db):
    user = _build(db)
    payload = _me_payload(db, user)
    # Chỉ phòng PHỤ (is_primary=False), KHÔNG gồm phòng chính; sắp theo tên.
    assert payload["kiem_nhiem"] == ["Phòng Phụ A", "Phòng Phụ B"]


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
