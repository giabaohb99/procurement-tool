"""bao-CR-793 — script chuyển người của một phòng từ vai trò xem cả cụm Giá NVL sang vai trò chỉ xem Bảng giá VTBB + Giá mua gần nhất.

Canh: đúng hai khóa, chỉ Xem / Xuất; người ngoài phòng giữ nguyên; vai trò đến từ gói chức vụ không bị đụng; chạy lại không đổi gì;
chưa có sáu khóa mới (chưa chạy migration `permsplit792`) thì dừng, không ghi.
"""
import pytest

from app.core.permissions import PACKAGING_ENTITIES
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole, UserScope
from scripts.split_packaging_lab_role import BASE_ROLE, LAB_ENTITIES, LAB_ROLE, split_lab_role


def _account(db, code: str, dept_id: int) -> User:
    emp = Employee(code=code, full_name=f"Người {code}", department_id=dept_id, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=code, employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def lab_world(db):
    lab = Department(code="LAB", name="Dego Lab", is_active=True)
    purchasing = Department(code="TM", name="Thu mua", is_active=True)
    base = Role(code=BASE_ROLE, name="Giá nguyên vật liệu")
    db.add_all([lab, purchasing, base])
    db.flush()
    for entity in PACKAGING_ENTITIES:
        db.add(Permission(role_id=base.id, entity=entity, scope="all", can_read=True, can_export=True))
    lab_a, lab_b, lab_by_position = _account(db, "LAB1", lab.id), _account(db, "LAB2", lab.id), _account(db, "LAB3", lab.id)
    outsider = _account(db, "TM1", purchasing.id)
    for user in (lab_a, lab_b, outsider):
        db.add(UserRole(user_id=user.id, role_id=base.id))
    db.add(UserRole(user_id=lab_by_position.id, role_id=base.id, granted_by_position_id=5))
    db.add(UserScope(user_id=lab_a.id, role_id=base.id, dim="company", value="1"))
    db.flush()
    return {"lab": lab.id, "base": base.id, "lab_users": [lab_a.id, lab_b.id], "by_position": lab_by_position.id,
            "outsider": outsider.id}


def _roles_of(db, user_id: int) -> set[str]:
    return {r[0] for r in db.query(Role.code).join(UserRole, UserRole.role_id == Role.id).filter(UserRole.user_id == user_id).all()}


def test_nguoi_phong_lab_chuyen_sang_vai_tro_hai_man_nguoi_ngoai_giu_nguyen(db, lab_world):
    result = split_lab_role(db, lab_world["lab"])

    assert result["role_created"] and sorted(result["granted"]) == sorted(LAB_ENTITIES) and len(result["moved"]) == 2
    for user_id in lab_world["lab_users"]:
        assert _roles_of(db, user_id) == {LAB_ROLE}
    assert _roles_of(db, lab_world["outsider"]) == {BASE_ROLE}
    lab_role = db.query(Role).filter(Role.code == LAB_ROLE).one()
    perms = db.query(Permission).filter(Permission.role_id == lab_role.id).all()
    assert {p.entity for p in perms} == set(LAB_ENTITIES)
    assert all(p.can_read and p.can_export and p.scope == "all" for p in perms)
    assert not any(p.can_create or p.can_write or p.can_delete or p.can_import for p in perms)


def test_pham_vi_rieng_theo_nguoi_di_theo_sang_vai_tro_moi(db, lab_world):
    split_lab_role(db, lab_world["lab"])
    lab_role = db.query(Role).filter(Role.code == LAB_ROLE).one()
    scopes = db.query(UserScope).filter(UserScope.user_id == lab_world["lab_users"][0]).all()
    assert [(s.role_id, s.dim, s.value) for s in scopes] == [(lab_role.id, "company", "1")]


def test_vai_tro_den_tu_goi_chuc_vu_khong_bi_dung(db, lab_world):
    result = split_lab_role(db, lab_world["lab"])
    assert len(result["skipped_position"]) == 1
    assert _roles_of(db, lab_world["by_position"]) == {BASE_ROLE}


def test_chay_lai_khong_doi_gi(db, lab_world):
    split_lab_role(db, lab_world["lab"])
    before = sorted((r.user_id, r.role_id) for r in db.query(UserRole).all())
    again = split_lab_role(db, lab_world["lab"])
    assert not again["role_created"] and again["granted"] == [] and again["moved"] == []
    assert sorted((r.user_id, r.role_id) for r in db.query(UserRole).all()) == before
    assert db.query(Permission).join(Role, Role.id == Permission.role_id).filter(Role.code == LAB_ROLE).count() == len(LAB_ENTITIES)


def test_chua_co_khoa_moi_thi_dung_khong_ghi(db, lab_world):
    db.query(Permission).filter(Permission.role_id == lab_world["base"]).delete()
    db.add(Permission(role_id=lab_world["base"], entity="packaging_cost", scope="all", can_read=True, can_export=True))
    db.flush()
    with pytest.raises(SystemExit):
        split_lab_role(db, lab_world["lab"])
    assert db.query(Role).filter(Role.code == LAB_ROLE).first() is None
    assert _roles_of(db, lab_world["lab_users"][0]) == {BASE_ROLE}
