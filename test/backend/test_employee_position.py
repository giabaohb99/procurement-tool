"""CR-022 — hồ sơ nhân sự KHÔNG còn cấp quyền cho tài khoản đăng nhập.

Ô "Vai trò" ở màn Nhân sự đã đổi thành "Vị trí / Chức vụ" (`position`) — chỉ là chữ để hiển thị
và in phiếu. Quyền của tài khoản chỉ được gán ở màn "Phân quyền tài khoản" (tab_user_role).
"""
from app.modules.employee import service as emp_service
from app.modules.employee.schema import EmployeeCreate, EmployeeUpdate
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole


def _roles_of(db, employee_id: int) -> set[int]:
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        return set()
    return {ur.role_id for ur in db.query(UserRole).filter(UserRole.user_id == user.id).all()}


class TestNhanSuKhongCapQuyen:
    def test_tao_nhan_su_khong_bat_buoc_vai_tro(self, db, seed):
        """Trước đây thiếu role_name là lỗi 400 — nay tạo nhân sự chỉ cần họ tên."""
        obj = emp_service.create_employee(
            db, EmployeeCreate(full_name="Nhân Viên Mới", position="Nhân viên kho"), 1)
        assert obj.id and obj.position == "Nhân viên kho"
        assert _roles_of(db, obj.id) == set()   # chưa có tài khoản → không có vai trò nào

    def test_doi_role_name_khong_gan_vai_tro_cho_tai_khoan(self, db, seed):
        """Sửa hồ sơ nhân sự (kể cả cột role_name cũ) KHÔNG được đụng tới vai trò tài khoản."""
        role = Role(code="pur_manager", name="Quản lý thu mua")
        db.add(role)
        db.flush()

        before = _roles_of(db, seed.emp_req_id)
        emp_service.update_employee(
            db, seed.emp_req_id, EmployeeUpdate(role_name="Quản lý thu mua"), 1)
        assert _roles_of(db, seed.emp_req_id) == before == set()

    def test_doi_vi_tri_khong_dung_toi_vai_tro_da_gan(self, db, seed):
        """Người đã được gán vai trò tay ở màn Phân quyền → sửa chức vụ không làm mất vai trò đó."""
        role = Role(code="pur_staff", name="Nhân viên thu mua")
        db.add(role)
        db.flush()
        user = db.query(User).filter(User.employee_id == seed.emp_req_id).first()
        db.add(UserRole(user_id=user.id, role_id=role.id))
        db.flush()

        emp_service.update_employee(
            db, seed.emp_req_id, EmployeeUpdate(position="Trưởng bộ phận"), 1)
        obj = emp_service.get_employee(db, seed.emp_req_id)
        assert obj.position == "Trưởng bộ phận"
        assert _roles_of(db, seed.emp_req_id) == {role.id}
