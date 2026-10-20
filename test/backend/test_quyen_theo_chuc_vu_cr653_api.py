"""duoc-CR-653 — API gói quyền chức vụ: ai được sửa, chống nâng quyền, vai trò admin, «Áp lại», nhật ký."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.modules.audit.model import AuditLog
from app.modules.employee import service as emp_service
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition, JobPositionRole
from app.modules.employee.schema import EmployeeUpdate
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole


@pytest.fixture
def client_as(db):
    def build(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield build
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def mk_role(db, code, entity="document", **act):
    r = Role(code=code, name=f"Vai trò {code}")
    db.add(r)
    db.flush()
    if entity:
        co = {f"can_{k}": True for k in (act or {"read": True})}
        db.add(Permission(role_id=r.id, entity=entity, scope="own", **co))
    db.commit()
    return r


def mk_pos(db, name="Kế toán"):
    p = JobPosition(code=f"cv-{name}".lower(), name=name, is_active=True)
    db.add(p)
    db.commit()
    return p


def actor(db, seed, cap_quyen, **act):
    u = db.query(User).filter(User.employee_id == seed.emp_tp_id).one()
    cap_quyen(u.id, "role", scope="all", **act)
    return u


def test_doc_goi_can_role_read(db, seed, cap_quyen, client_as):
    pos = mk_pos(db)
    nobody = db.query(User).filter(User.employee_id == seed.emp_tp_id).one()
    assert client_as(nobody).get(f"/api/job-positions/{pos.id}/roles").status_code == 403
    rd = actor(db, seed, cap_quyen, read=True)
    r = client_as(rd).get(f"/api/job-positions/{pos.id}/roles")
    assert r.status_code == 200 and r.json()["data"]["roles"] == []


def test_job_position_write_khong_du_de_sua_goi(db, seed, cap_quyen, client_as):
    pos, ra = mk_pos(db), mk_role(db, "ZA")
    u = db.query(User).filter(User.employee_id == seed.emp_tp_id).one()
    cap_quyen(u.id, "job_position", scope="all", read=True, write=True, create=True)
    cap_quyen(u.id, "role", scope="all", read=True)           # chỉ đọc vai trò
    r = client_as(u).put(f"/api/job-positions/{pos.id}/roles", json={"role_ids": [ra.id]})
    assert r.status_code == 403
    assert client_as(u).post(f"/api/job-positions/{pos.id}/roles/apply").status_code == 403


def test_sua_goi_ghi_nhat_ky_va_khong_dung_tai_khoan(db, seed, cap_quyen, client_as):
    pos, ra = mk_pos(db), mk_role(db, "ZA")
    u = actor(db, seed, cap_quyen, read=True, write=True)
    cap_quyen(u.id, "document", scope="all", read=True)        # đủ quyền để không vướng chống nâng quyền
    holder = db.query(User).filter(User.employee_id == seed.emp_req_id).one()
    emp_service.update_employee(db, seed.emp_req_id, EmployeeUpdate(position_id=pos.id), 1)
    r = client_as(u).put(f"/api/job-positions/{pos.id}/roles", json={"role_ids": [ra.id, ra.id]})
    assert r.status_code == 200, r.text
    assert [x["role_id"] for x in r.json()["data"]["roles"]] == [ra.id]
    assert db.query(UserRole).filter(UserRole.user_id == holder.id, UserRole.role_id == ra.id).count() == 0
    assert db.query(AuditLog).filter(AuditLog.action == "set_position_roles").count() == 1


def test_chong_nang_quyen_khong_dua_vao_goi_vai_tro_manh_hon_minh(db, seed, cap_quyen, client_as):
    pos = mk_pos(db)
    strong = mk_role(db, "ZSTRONG", entity="payable", read=True, write=True, delete=True)
    u = actor(db, seed, cap_quyen, read=True, write=True)
    r = client_as(u).put(f"/api/job-positions/{pos.id}/roles", json={"role_ids": [strong.id]})
    assert r.status_code == 403
    assert db.query(JobPositionRole).count() == 0


def test_khong_dua_vai_tro_admin_vao_goi_va_vai_tro_ma_bi_tu_choi(db, seed, cap_quyen, client_as):
    pos = mk_pos(db)
    admin = Role(code="admin", name="Quản trị hệ thống")
    db.add(admin)
    db.commit()
    u = actor(db, seed, cap_quyen, read=True, write=True)
    assert client_as(u).put(f"/api/job-positions/{pos.id}/roles", json={"role_ids": [admin.id]}).status_code == 400
    assert client_as(u).put(f"/api/job-positions/{pos.id}/roles", json={"role_ids": [99999]}).status_code in (400, 404)
    assert client_as(u).put(f"/api/job-positions/99999/roles", json={"role_ids": []}).status_code == 404
    assert client_as(u).put(f"/api/job-positions/{pos.id}/roles", json={"role_ids": list(range(201))}).status_code == 422


def test_ap_lai_dem_dung_va_chi_dong_bo_phan_tu_cap(db, seed, cap_quyen, client_as):
    ra, rb, rhand = mk_role(db, "ZA"), mk_role(db, "ZB"), mk_role(db, "ZH")
    pos = mk_pos(db)
    for eid in (seed.emp_req_id, seed.emp_nstm_id):
        emp_service.update_employee(db, eid, EmployeeUpdate(position_id=pos.id), 1)
    req = db.query(User).filter(User.employee_id == seed.emp_req_id).one()
    db.add(UserRole(user_id=req.id, role_id=rhand.id))
    db.add(JobPositionRole(job_position_id=pos.id, role_id=ra.id))
    db.commit()
    u = actor(db, seed, cap_quyen, read=True, write=True)
    cap_quyen(u.id, "document", scope="all", read=True)
    got = client_as(u).get(f"/api/job-positions/{pos.id}/roles").json()["data"]
    assert got["eligible_holders"] == 2
    r = client_as(u).post(f"/api/job-positions/{pos.id}/roles/apply")
    assert r.status_code == 200, r.text
    s = r.json()["data"]
    assert (s["holders"], s["changed_users"], s["granted"], s["revoked"]) == (2, 2, 2, 0)
    db.add(JobPositionRole(job_position_id=pos.id, role_id=rb.id))
    db.query(JobPositionRole).filter(JobPositionRole.role_id == ra.id).delete()
    db.commit()
    s = client_as(u).post(f"/api/job-positions/{pos.id}/roles/apply").json()["data"]
    assert (s["granted"], s["revoked"]) == (2, 2)
    db.expire_all()
    roles = {r.role_id for r in db.query(UserRole).filter(UserRole.user_id == req.id)}
    assert rhand.id in roles and rb.id in roles and ra.id not in roles
    assert db.query(AuditLog).filter(AuditLog.action == "apply_position_roles").count() == 2


def test_ap_lai_bo_qua_nguoi_nghi_viec_va_chinh_nguoi_bam(db, seed, cap_quyen, client_as):
    ra = mk_role(db, "ZA")
    pos = mk_pos(db)
    db.add(JobPositionRole(job_position_id=pos.id, role_id=ra.id))
    db.commit()
    u = actor(db, seed, cap_quyen, read=True, write=True)
    cap_quyen(u.id, "document", scope="all", read=True)
    for eid in (seed.emp_tp_id, seed.emp_req_id):           # người bấm (emp_tp) + một người sẽ nghỉ việc
        emp_service.update_employee(db, eid, EmployeeUpdate(position_id=pos.id), 1)
    db.query(UserRole).filter(UserRole.role_id == ra.id).delete()   # xóa cái vừa tự cấp để thử «Áp lại»
    db.get(Employee, seed.emp_req_id).status = "resigned"
    db.commit()
    s = client_as(u).post(f"/api/job-positions/{pos.id}/roles/apply").json()["data"]
    # Review L4: người bấm KHÔNG tính vào «holders», báo riêng ở skipped_self.
    assert s["holders"] == 0 and s["skipped_self"] == 1 and s["changed_users"] == 0
