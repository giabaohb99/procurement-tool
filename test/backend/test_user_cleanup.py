"""Dọn tài khoản: lọc mồ côi / chưa gán vai trò, xóa tài khoản, vai trò mặc định khi tạo.

Bối cảnh: trên prod có 5 tài khoản mồ côi (không còn hồ sơ nhân sự) — do CR-023 khi xóa nhân sự
chỉ KHÓA tài khoản chứ không xóa. Cần lọc ra được và xóa hẳn, nhưng KHÔNG được xóa nhầm tài khoản
đang dùng hoặc tài khoản đã tạo chứng từ.
"""
import pytest
from fastapi import HTTPException

from app.modules.employee.model import Employee
from app.modules.role.model import Role
from app.modules.user import service as user_service
from app.modules.user.model import User, UserRole, UserScope
from app.modules.user.schema import RoleAssign, UserProvision

PG = {"offset": 0, "limit": 50}


@pytest.fixture
def role_nv(db):
    r = Role(code=user_service.DEFAULT_ROLE_CODE, name="Nhân sự")
    db.add(r)
    db.commit()
    return r


class TestLocTaiKhoan:
    def test_loc_mo_coi(self, db, seed):
        mo_coi = User(email="", employee_id=0, password_hash="x", is_active=False)
        chet = User(email="cu@dego.vn", employee_id=99999, password_hash="x", is_active=False)
        db.add_all([mo_coi, chet])
        db.commit()

        total, items = user_service.list_users(db, PG, orphan=True)
        ids = {u.id for u in items}

        assert total == 2
        assert ids == {mo_coi.id, chet.id}

    def test_loc_chua_gan_vai_tro(self, db, seed, role_nv):
        user_service.assign_roles(db, seed.u_req_id, RoleAssign(role_ids=[role_nv.id]), 1)

        total, items = user_service.list_users(db, PG, no_role=True)

        assert seed.u_req_id not in {u.id for u in items}
        assert total == 3          # 3 tài khoản còn lại trong seed đều chưa gán vai trò


class TestVaiTroMacDinh:
    def test_tao_tai_khoan_khong_chon_vai_tro_thi_thanh_nhan_su(self, db, seed, role_nv):
        emp = Employee(code="NSU100", full_name="Người Mới", is_active=True)
        db.add(emp)
        db.commit()

        u = user_service.provision_user(
            db, UserProvision(employee_id=emp.id, password="123456", role_ids=[]), 1)

        assert user_service._role_ids(db, u.id) == [role_nv.id]

    def test_chon_vai_tro_thi_giu_nguyen_lua_chon(self, db, seed, role_nv):
        other = Role(code="pur_staff", name="Nhân viên thu mua")
        db.add(other)
        emp = Employee(code="NSU101", full_name="Người Mới 2", is_active=True)
        db.add(emp)
        db.commit()

        u = user_service.provision_user(
            db, UserProvision(employee_id=emp.id, password="123456", role_ids=[other.id]), 1)

        assert user_service._role_ids(db, u.id) == [other.id]


class TestXoaTaiKhoan:
    def test_xoa_tai_khoan_mo_coi_keo_theo_vai_tro_va_pham_vi(self, db, seed, role_nv):
        u = User(email="", employee_id=0, password_hash="x", is_active=False)
        db.add(u)
        db.commit()
        db.add(UserRole(user_id=u.id, role_id=role_nv.id))
        db.add(UserScope(user_id=u.id, role_id=role_nv.id, dim="company", value="1"))
        db.commit()

        user_service.delete_user(db, u.id, 1)

        assert db.get(User, u.id) is None
        assert db.query(UserRole).filter(UserRole.user_id == u.id).count() == 0
        assert db.query(UserScope).filter(UserScope.user_id == u.id).count() == 0

    def test_khong_xoa_tai_khoan_dang_hoat_dong_cua_nhan_su(self, db, seed):
        with pytest.raises(HTTPException) as ex:
            user_service.delete_user(db, seed.u_req_id, 1)
        assert ex.value.status_code == 400
        assert db.get(User, seed.u_req_id) is not None

    def test_khong_xoa_tai_khoan_da_khoa_nhung_con_ho_so_nhan_su(self, db, seed):
        """Đã khóa mà hồ sơ nhân sự vẫn còn thì KHÔNG phải mồ côi — vẫn cấm xóa."""
        u = db.get(User, seed.u_req_id)
        u.is_active = False
        db.commit()
        emp = db.get(Employee, u.employee_id)

        with pytest.raises(HTTPException) as ex:
            user_service.delete_user(db, u.id, u.id + 1000)   # người xóa là admin khác

        assert ex.value.status_code == 400
        assert emp.full_name in ex.value.detail
        assert db.get(User, u.id) is not None

    def test_khong_xoa_chinh_minh(self, db, seed):
        u = User(email="", employee_id=0, password_hash="x", is_active=False)
        db.add(u)
        db.commit()
        with pytest.raises(HTTPException) as ex:
            user_service.delete_user(db, u.id, u.id)
        assert ex.value.status_code == 400

    def test_khong_xoa_tai_khoan_da_tao_chung_tu(self, db, seed):
        from app.modules.purchase_request.model import PurchaseRequest
        u = User(email="", employee_id=0, password_hash="x", is_active=False)
        db.add(u)
        db.commit()
        db.add(PurchaseRequest(code="PYC-TEST", created_by=u.id, updated_by=u.id))
        db.commit()

        with pytest.raises(HTTPException) as ex:
            user_service.delete_user(db, u.id, 1)
        assert ex.value.status_code == 400
        assert "khóa tài khoản" in ex.value.detail

    def test_khong_xoa_quan_tri_duy_nhat(self, db, seed):
        admin = Role(code="admin", name="Quản trị hệ thống")
        db.add(admin)
        u = User(email="", employee_id=0, password_hash="x", is_active=False)
        db.add_all([admin, u])
        db.commit()
        db.add(UserRole(user_id=u.id, role_id=admin.id))
        db.commit()

        with pytest.raises(HTTPException) as ex:
            user_service.delete_user(db, u.id, 1)
        assert ex.value.status_code == 400
        assert "quản trị" in ex.value.detail.lower()

    def test_nhat_ky_thao_tac_khong_chan_xoa(self, db, seed):
        """Nhật ký là lịch sử — giữ nguyên, không được vì nó mà cấm xóa tài khoản mồ côi."""
        from app.modules.audit.model import AuditLog
        u = User(email="", employee_id=0, password_hash="x", is_active=False)
        db.add(u)
        db.commit()
        db.add(AuditLog(entity="survey_request", entity_id=1, action="create",
                        created_by=u.id, updated_by=u.id))
        db.commit()

        user_service.delete_user(db, u.id, 1)

        assert db.get(User, u.id) is None
        assert db.query(AuditLog).filter(AuditLog.created_by == u.id).count() == 1
