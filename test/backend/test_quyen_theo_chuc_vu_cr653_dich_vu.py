"""duoc-CR-653 — Quyền mặc định theo chức vụ: DỊCH VỤ lõi (`position_role_service`).

Cấp khi tạo tài khoản · đổi chức vụ chỉ đổi dòng HỆ THỐNG cấp · dòng gán tay không bao giờ bị gỡ · vai trò
trùng tay+gói · bỏ chức vụ · tài khoản khóa / hồ sơ nghỉ việc bị bỏ qua · cache quyền · nhật ký.
"""
import pytest

from app.core import auth
from cr653_tro_giup import mk_admin
from app.modules.audit.model import AuditLog
from app.modules.employee import position_role_service as svc
from app.modules.employee import service as emp_service
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition, JobPositionRole
from app.modules.employee.schema import EmployeeUpdate
from app.modules.role.model import Role
from app.modules.user import service as user_service
from app.modules.user.model import User, UserRole
from app.modules.user.schema import UserProvision

ACTOR = 0


@pytest.fixture(autouse=True)
def _nguoi_thao_tac(db, seed):
    """Người thao tác là một quản trị riêng; `ACTOR` gán lại mỗi bài (id đếm lại từ 1 theo từng DB)."""
    global ACTOR
    ACTOR = mk_admin(db)


def mk_role(db, code):
    r = Role(code=code, name=f"Vai trò {code}")
    db.add(r)
    db.flush()
    return r


def mk_pos(db, name, roles=()):
    p = JobPosition(code=f"cv-{name}", name=name, is_active=True)
    db.add(p)
    db.flush()
    for r in roles:
        db.add(JobPositionRole(job_position_id=p.id, role_id=r.id))
    db.commit()
    return p


def user_of(db, seed, emp_attr="emp_req_id"):
    return db.query(User).filter(User.employee_id == getattr(seed, emp_attr)).one()


def rows_of(db, uid):
    """{role_id: granted_by_position_id}"""
    db.expire_all()
    return {r.role_id: r.granted_by_position_id for r in db.query(UserRole).filter(UserRole.user_id == uid)}


def set_position(db, eid, pid):
    emp_service.update_employee(db, eid, EmployeeUpdate(position_id=pid), ACTOR)


def test_tao_tai_khoan_cap_goi_chuc_vu(db, seed):
    ra, rb = mk_role(db, "ZA"), mk_role(db, "ZB")
    pos = mk_pos(db, "Kế toán", [ra, rb])
    emp = Employee(code="NV900", full_name="Mới", position_id=pos.id, position=pos.name, is_active=True)
    db.add(emp)
    db.commit()
    u = user_service.provision_user(db, UserProvision(employee_id=emp.id, email="moi@x.vn", password="Abcdef12!x"), ACTOR)
    got = rows_of(db, u.id)
    assert got[ra.id] == got[rb.id] == pos.id          # hai vai trò gói, đều đánh dấu nguồn
    actions = {a.action for a in db.query(AuditLog).filter(AuditLog.entity == "user", AuditLog.entity_id == u.id)}
    assert "auto_grant_position" in actions


def test_tao_tai_khoan_chuc_vu_chua_co_goi_khong_cap_gi_them(db, seed):
    pos = mk_pos(db, "Rỗng")
    emp = Employee(code="NV901", full_name="Mới", position_id=pos.id, is_active=True)
    db.add(emp)
    db.commit()
    u = user_service.provision_user(db, UserProvision(employee_id=emp.id, email="a@x.vn", password="Abcdef12!x"), ACTOR)
    assert all(v == 0 for v in rows_of(db, u.id).values())


def test_doi_chuc_vu_chi_doi_dong_he_thong_cap(db, seed):
    ra, rb, rhand = mk_role(db, "ZA"), mk_role(db, "ZB"), mk_role(db, "ZH")
    px, py = mk_pos(db, "X", [ra]), mk_pos(db, "Y", [rb])
    u = user_of(db, seed)
    db.add(UserRole(user_id=u.id, role_id=rhand.id))     # gán tay
    db.commit()
    set_position(db, seed.emp_req_id, px.id)
    assert rows_of(db, u.id) == {rhand.id: 0, ra.id: px.id}
    set_position(db, seed.emp_req_id, py.id)
    assert rows_of(db, u.id) == {rhand.id: 0, rb.id: py.id}    # A bị gỡ, B vào, tay còn nguyên


def test_vai_tro_chung_hai_goi_chi_doi_nhan_nguon_khong_xoa_chen(db, seed):
    ra = mk_role(db, "ZA")
    px, py = mk_pos(db, "X", [ra]), mk_pos(db, "Y", [ra])
    u = user_of(db, seed)
    set_position(db, seed.emp_req_id, px.id)
    first_id = db.query(UserRole).filter(UserRole.user_id == u.id, UserRole.role_id == ra.id).one().id
    set_position(db, seed.emp_req_id, py.id)
    row = db.query(UserRole).filter(UserRole.user_id == u.id, UserRole.role_id == ra.id).one()
    assert row.id == first_id and row.granted_by_position_id == py.id


def test_vai_tro_gan_tay_va_co_trong_goi_khong_nhan_doi_khong_bi_gỡ(db, seed):
    ra = mk_role(db, "ZA")
    px = mk_pos(db, "X", [ra])
    u = user_of(db, seed)
    db.add(UserRole(user_id=u.id, role_id=ra.id))        # tay trước
    db.commit()
    set_position(db, seed.emp_req_id, px.id)
    assert db.query(UserRole).filter(UserRole.user_id == u.id, UserRole.role_id == ra.id).count() == 1
    assert rows_of(db, u.id)[ra.id] == 0                  # vẫn là dòng tay
    set_position(db, seed.emp_req_id, 0)
    assert ra.id in rows_of(db, u.id)                     # bỏ chức vụ vẫn giữ


def test_bo_chuc_vu_go_dong_tu_cap(db, seed):
    ra = mk_role(db, "ZA")
    px = mk_pos(db, "X", [ra])
    u = user_of(db, seed)
    set_position(db, seed.emp_req_id, px.id)
    assert ra.id in rows_of(db, u.id)
    set_position(db, seed.emp_req_id, 0)
    assert ra.id not in rows_of(db, u.id)
    actions = {a.action for a in db.query(AuditLog).filter(AuditLog.entity == "user", AuditLog.entity_id == u.id)}
    assert {"auto_grant_position", "auto_revoke_position"} <= actions


def test_tai_khoan_khoa_va_ho_so_nghi_viec_bi_bo_qua(db, seed):
    ra = mk_role(db, "ZA")
    px = mk_pos(db, "X", [ra])
    locked = user_of(db, seed, "emp_req_id")
    locked.is_active = False
    gone_emp = db.get(Employee, seed.emp_tp_id)
    gone_emp.status = "resigned"
    gone = user_of(db, seed, "emp_tp_id")
    db.commit()
    set_position(db, seed.emp_req_id, px.id)
    emp_service.update_employee(db, seed.emp_tp_id, EmployeeUpdate(position_id=px.id), ACTOR)
    assert ra.id not in rows_of(db, locked.id)
    assert ra.id not in rows_of(db, gone.id)


def test_mo_khoa_tai_khoan_doi_chieu_lai_goi(db, seed):
    ra = mk_role(db, "ZA")
    px = mk_pos(db, "X", [ra])
    u = user_of(db, seed)
    u.is_active = False
    db.commit()
    set_position(db, seed.emp_req_id, px.id)
    assert ra.id not in rows_of(db, u.id)
    user_service.set_active(db, u.id, True, ACTOR)
    assert rows_of(db, u.id)[ra.id] == px.id


def test_xoa_cache_quyen_sau_commit(db, seed, monkeypatch):
    ra = mk_role(db, "ZA")
    px = mk_pos(db, "X", [ra])
    u = user_of(db, seed)
    auth._PERM_CACHE[u.id] = ({"stale": True}, 10 ** 12)
    set_position(db, seed.emp_req_id, px.id)
    assert u.id not in auth._PERM_CACHE
    # dựng lại hồ sơ quyền phải thấy vai trò mới
    prof = auth.get_perm_profile(db, u)
    assert any(g["role_id"] == ra.id for g in prof["grants"])


def test_goi_roi_khong_doi_chuc_vu_thi_khong_dung_toi_ai(db, seed):
    ra = mk_role(db, "ZA")
    px = mk_pos(db, "X")
    u = user_of(db, seed)
    set_position(db, seed.emp_req_id, px.id)
    db.add(JobPositionRole(job_position_id=px.id, role_id=ra.id))   # sửa gói trực tiếp, KHÔNG áp
    db.commit()
    emp_service.update_employee(db, seed.emp_req_id, EmployeeUpdate(full_name="Đổi tên"), ACTOR)
    assert ra.id not in rows_of(db, u.id)


def test_assign_roles_giu_nhan_tu_cap_va_chi_xoa_dong_bi_bo(db, seed):
    ra, rb = mk_role(db, "ZA"), mk_role(db, "ZB")
    px = mk_pos(db, "X", [ra])
    u = user_of(db, seed)
    set_position(db, seed.emp_req_id, px.id)
    from app.modules.user.schema import RoleAssign
    user_service.assign_roles(db, u.id, RoleAssign(role_ids=[ra.id, rb.id]), ACTOR)
    assert rows_of(db, u.id) == {ra.id: px.id, rb.id: 0}
    user_service.assign_roles(db, u.id, RoleAssign(role_ids=[rb.id]), ACTOR)
    assert rows_of(db, u.id) == {rb.id: 0}
    assert user_service.auto_grants_of(db, u.id) == []
