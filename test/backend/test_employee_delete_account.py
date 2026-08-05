"""CR-023 — xoá hồ sơ nhân sự thì tài khoản đăng nhập của người đó phải bị khoá.

Trước đây xoá nhân sự là xoá cứng và không đụng gì tới `tab_user` → còn lại "tài khoản mồ côi"
vẫn đăng nhập được (và nếu trùng email với tài khoản thật thì còn che mất tài khoản thật).
"""
import pytest
from fastapi import HTTPException

from app.modules.auth import service as auth_service
from app.modules.employee import service as emp_service
from app.modules.employee.model import Employee
from app.modules.user import service as user_service
from app.modules.user.model import User
from app.modules.user.schema import UserProvision


def _user_of(db, employee_id: int) -> User | None:
    return db.query(User).filter(User.employee_id == employee_id).first()


class TestXoaNhanSuKhoaTaiKhoan:
    def test_xoa_nhan_su_thi_tai_khoan_bi_khoa_va_go_lien_ket(self, db, seed):
        user_id = _user_of(db, seed.emp_req_id).id

        locked = emp_service.delete_employee(db, seed.emp_req_id, 1)

        assert locked == 1
        assert db.get(Employee, seed.emp_req_id) is None
        u = db.get(User, user_id)
        assert u is not None            # giữ lại để truy vết ai đã làm gì
        assert u.is_active is False
        assert u.employee_id == 0

    def test_tai_khoan_mo_coi_khong_dang_nhap_duoc(self, db, seed):
        emp_service.delete_employee(db, seed.emp_req_id, 1)
        with pytest.raises(HTTPException) as ex:
            auth_service.authenticate(db, "TESTREQ", "x")
        assert ex.value.status_code == 401


class TestTrungEmailDangNhap:
    def test_tai_khoan_da_khoa_khong_che_tai_khoan_that(self, db, seed):
        """2 tài khoản trùng email, cái CŨ đã khoá → đăng nhập vẫn phải ra tài khoản đang hoạt động."""
        real = _user_of(db, seed.emp_tp_id)
        real.email = "trung@dego.vn"
        db.add(User(email="trung@dego.vn", employee_id=0, password_hash="x", is_active=False))
        db.flush()

        # verify_password thật sẽ fail với hash giả → chỉ kiểm tra tài khoản nào được chọn
        picked = {}
        real_verify = auth_service.verify_password
        auth_service.verify_password = lambda p, h: True
        try:
            picked = auth_service.authenticate(db, "trung@dego.vn", "x")
        finally:
            auth_service.verify_password = real_verify
        assert picked.id == real.id

    def test_khong_tao_duoc_tai_khoan_thu_hai_cung_email(self, db, seed):
        _user_of(db, seed.emp_tp_id).email = "trung@dego.vn"
        emp = Employee(code="NSU999", full_name="Người Mới", email="trung@dego.vn", is_active=True)
        db.add(emp)
        db.flush()

        with pytest.raises(HTTPException) as ex:
            user_service.provision_user(
                db, UserProvision(employee_id=emp.id, password="123456", role_ids=[]), 1)
        assert ex.value.status_code == 400
