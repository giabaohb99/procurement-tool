"""bao-CR-523 — Quản trị hệ thống tự sửa quyền được (có cảnh báo) + vai trò Quản trị luôn FULL.

Khách chốt 30/09/2026:
  1. Người giữ vai trò `admin` được MIỄN L1 (tự sửa vai trò / phạm vi của mình, sửa ma trận
     của vai trò mình đang giữ). Người khác vẫn L1 + L2 như cũ.
  2. Tự bỏ vai trò Quản trị của chính mình phải kèm `confirm_self_admin_removal` — thiếu
     cờ là 409 (giao diện hỏi lại). Không thao tác nào được để hệ còn 0 quản trị đang
     hoạt động — 400, kể cả có cờ.
  3. Vai trò `admin` luôn FULL: cửa ghi ma trận từ chối bản làm hụt (400), seed ép lại
     mỗi lần deploy (ngoại lệ có chủ đích của D-018).
  4. Tool `propose_account_setup`: admin miễn L1, nhưng tool TỪ CHỐI HẲN việc bỏ vai trò
     Quản trị của chính người hỏi.

Bài kiểm cố tìm chỗ lủng: người KHÔNG phải admin đội lốt (vai trò `ADMINISTRATOR` đời cũ),
quản trị đã khóa vẫn được đếm, ma trận bớt đúng một ô / đúng phạm vi, seed chạy hai lần.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import privilege_escalation as pe
from app.core.permissions import ACTIONS, ENTITIES
from app.modules.assistant import tools as T
from app.modules.assistant.tools.account_setup_tool import (
    SELF_ADMIN_REMOVAL_REFUSED,
    confirm_account_setup,
)
from app.modules.employee.model import Employee
from app.modules.role import controller as role_controller
from app.modules.role.model import Permission, Role
from app.modules.role.schema import PermissionItem, PermissionUpdate
from app.modules.user import controller as user_controller
from app.modules.user import service as user_service
from app.modules.user.model import User, UserRole
from app.modules.user.schema import ActiveUpdate, RoleAssign, ScopeUpdate
from app.seed import ensure_admin_role


# ── Dựng cảnh ─────────────────────────────────────────────────────────────────────────────

def _make_user(db, code: str, active: bool = True) -> User:
    emp = Employee(code=code, full_name=f"Người {code}", is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=code, employee_id=emp.id, password_hash="x", is_active=active)
    db.add(user)
    db.flush()
    return user


def _give(db, user: User, role_id: int) -> None:
    db.add(UserRole(user_id=user.id, role_id=role_id))
    db.commit()


def _full_matrix(entities=ENTITIES, scope: str = "all") -> list[PermissionItem]:
    return [PermissionItem(entity=e, scope=scope, **{f"can_{a}": True for a in ACTIONS})
            for e in entities]


@pytest.fixture
def world(db, cap_quyen):
    """admin A + admin B (đều hoạt động), người thường N có user.write + role.write phạm vi
    tất cả, và vai trò thường `employee` (A đang giữ) để thử sửa ma trận vai trò mình giữ."""
    admin_role = ensure_admin_role(db)
    employee_role = Role(code="employee", name="Nhân sự")
    db.add(employee_role)
    db.flush()
    db.add(Permission(role_id=employee_role.id, entity="purchase_request",
                      can_read=True, scope="own"))
    a = _make_user(db, "ADMIN_A")
    b = _make_user(db, "ADMIN_B")
    n = _make_user(db, "NGUOI_N")
    db.commit()
    _give(db, a, admin_role.id)
    _give(db, a, employee_role.id)
    _give(db, b, admin_role.id)
    cap_quyen(n.id, "user", scope="all", read=True, write=True)
    cap_quyen(n.id, "role", scope="all", read=True, write=True)
    db.commit()
    return SimpleNamespace(admin_role=admin_role, employee_role=employee_role, a=a, b=b, n=n)


def _assign(db, actor, target_id, role_ids, confirm=False):
    return user_controller.assign_roles(
        target_id, RoleAssign(role_ids=role_ids, confirm_self_admin_removal=confirm),
        db=db, user=actor)


# ── 1. Admin được tự sửa, người thường thì không ──────────────────────────────────────────

def test_admin_may_edit_own_roles_and_scope(db, world):
    _assign(db, world.a, world.a.id, [world.admin_role.id])
    assert user_service._role_ids(db, world.a.id) == [world.admin_role.id]
    user_controller.set_scope(world.a.id, world.admin_role.id,
                              ScopeUpdate(exclude_departments=["Phòng X"]), db=db, user=world.a)


def test_admin_may_edit_matrix_of_a_role_they_hold(db, world):
    """A giữ vai trò `employee` — trước CR-523 là 403 «Bạn đang giữ vai trò này»."""
    matrix = PermissionUpdate(permissions=[PermissionItem(entity="purchase_request",
                                                          can_read=True, can_write=True)])
    role_controller.set_permissions(world.employee_role.id, matrix, db=db, user=world.a)


def test_non_admin_is_still_blocked_on_self(db, world):
    with pytest.raises(HTTPException) as err:
        _assign(db, world.n, world.n.id, [])
    assert err.value.status_code == 403
    with pytest.raises(HTTPException) as err:
        user_controller.set_scope(world.n.id, world.employee_role.id, ScopeUpdate(),
                                  db=db, user=world.n)
    assert err.value.status_code == 403


def test_non_admin_still_cannot_edit_matrix_of_role_they_hold(db, world):
    _give(db, world.n, world.employee_role.id)
    with pytest.raises(HTTPException) as err:
        role_controller.set_permissions(world.employee_role.id, PermissionUpdate(permissions=[]),
                                        db=db, user=world.n)
    assert err.value.status_code == 403


def test_legacy_administrator_role_is_not_exempt(db, world):
    """Chỉ đúng mã `admin` được miễn. Vai trò đời cũ `ADMINISTRATOR` — hay một vai trò ai đó
    đặt tên «Quản trị» — không được mở cửa L1."""
    legacy = Role(code="ADMINISTRATOR", name="Quản trị hệ thống")
    db.add(legacy)
    db.flush()
    _give(db, world.n, legacy.id)
    assert pe.is_system_admin(db, world.n.id) is False
    with pytest.raises(HTTPException) as err:
        pe.block_edit_own_permissions(world.n.id, world.n, db)
    assert err.value.status_code == 403


def test_without_db_argument_l1_stays_hard_even_for_admin(db, world):
    """Cửa nào quên truyền `db` thì chặn THỪA chứ không mở lỗ."""
    with pytest.raises(HTTPException):
        pe.block_edit_own_permissions(world.a.id, world.a)


# ── 2. Tự bỏ vai trò Quản trị: 409 → gửi lại kèm cờ ──────────────────────────────────────

def test_self_admin_removal_without_flag_is_409_with_confirm_text(db, world):
    with pytest.raises(HTTPException) as err:
        _assign(db, world.a, world.a.id, [world.employee_role.id])
    assert err.value.status_code == 409
    assert err.value.detail == pe.SELF_ADMIN_REMOVAL_MESSAGE
    assert "Tiếp tục?" in err.value.detail
    #  Chưa ghi gì.
    assert world.admin_role.id in user_service._role_ids(db, world.a.id)


def test_self_admin_removal_with_flag_goes_through(db, world):
    _assign(db, world.a, world.a.id, [world.employee_role.id], confirm=True)
    assert user_service._role_ids(db, world.a.id) == [world.employee_role.id]
    assert pe.is_system_admin(db, world.a.id) is False


def test_keeping_admin_role_never_asks(db, world):
    """Cờ chỉ cần khi thật sự BỎ admin — tick thêm/bớt vai trò khác thì không hỏi."""
    _assign(db, world.a, world.a.id, [world.admin_role.id])


def test_removing_someone_elses_admin_needs_no_flag(db, world):
    _assign(db, world.a, world.b.id, [])
    assert pe.is_system_admin(db, world.b.id) is False


# ── 2b. Hệ phải còn ít nhất một quản trị đang hoạt động ──────────────────────────────────

def test_last_active_admin_cannot_drop_own_admin_even_with_flag(db, world):
    """B đã khóa thì không tính — A là quản trị hoạt động cuối cùng."""
    world.b.is_active = False
    db.commit()
    with pytest.raises(HTTPException) as err:
        _assign(db, world.a, world.a.id, [], confirm=True)
    assert err.value.status_code == 400
    assert err.value.detail == pe.LAST_ADMIN_MESSAGE


def test_last_admin_guard_fires_before_the_confirm_question(db, world):
    """Đừng hỏi «Tiếp tục?» cho một việc đằng nào cũng bị từ chối."""
    world.b.is_active = False
    db.commit()
    with pytest.raises(HTTPException) as err:
        _assign(db, world.a, world.a.id, [])
    assert err.value.status_code == 400


def test_nobody_may_strip_the_last_active_admin(db, world):
    _assign(db, world.a, world.b.id, [])          # còn A
    with pytest.raises(HTTPException) as err:
        _assign(db, world.n, world.a.id, [])      # N (không phải admin) tước nốt A
    assert err.value.status_code == 400


def test_locking_the_last_active_admin_is_400(db, world):
    user_controller.set_active(world.b.id, ActiveUpdate(is_active=False), db=db, user=world.n)
    with pytest.raises(HTTPException) as err:
        user_controller.set_active(world.a.id, ActiveUpdate(is_active=False), db=db, user=world.n)
    assert err.value.status_code == 400
    assert db.get(User, world.a.id).is_active is True


def test_unlocking_is_never_blocked(db, world):
    world.b.is_active = False
    db.commit()
    user_controller.set_active(world.b.id, ActiveUpdate(is_active=True), db=db, user=world.a)


def test_count_active_admins_ignores_locked_and_non_admin(db, world):
    assert pe.count_active_admins(db) == 2
    world.b.is_active = False
    db.commit()
    assert pe.count_active_admins(db) == 1
    assert pe.count_active_admins(db, exclude_user_id=world.a.id) == 0


# ── 3. Vai trò admin luôn FULL ────────────────────────────────────────────────────────────

def test_admin_role_accepts_full_matrix(db, world):
    role_controller.set_permissions(world.admin_role.id, PermissionUpdate(permissions=_full_matrix()),
                                    db=db, user=world.a)


@pytest.mark.parametrize("how", ["one_cell_off", "narrow_scope", "missing_entity", "empty"])
def test_admin_role_cannot_be_reduced(db, world, how):
    items = _full_matrix()
    if how == "one_cell_off":
        items[0].can_export = False
    elif how == "narrow_scope":
        items[-1].scope = "company"
    elif how == "missing_entity":
        items = items[1:]
    else:
        items = []
    with pytest.raises(HTTPException) as err:
        role_controller.set_permissions(world.admin_role.id, PermissionUpdate(permissions=items),
                                        db=db, user=world.a)
    assert err.value.status_code == 400
    assert err.value.detail == pe.ADMIN_ROLE_FULL_MESSAGE
    #  DB giữ nguyên FULL.
    rows = db.query(Permission).filter(Permission.role_id == world.admin_role.id).all()
    assert {p.entity for p in rows} >= set(ENTITIES)


def test_non_admin_cannot_write_admin_role_even_full(db, world):
    """Bản FULL thì qua chốt «không làm hụt», nhưng L2 chặn: N không có đủ quyền để cấp."""
    with pytest.raises(HTTPException) as err:
        role_controller.set_permissions(world.admin_role.id,
                                        PermissionUpdate(permissions=_full_matrix()),
                                        db=db, user=world.n)
    assert err.value.status_code == 403


def test_other_roles_can_still_be_reduced(db, world):
    role_controller.set_permissions(world.employee_role.id, PermissionUpdate(permissions=[]),
                                    db=db, user=world.a)
    assert db.query(Permission).filter(Permission.role_id == world.employee_role.id).count() == 0


# ── 3b. Seed ép vai trò admin FULL, chạy lại không đổi gì ────────────────────────────────

def _admin_rows(db, role_id):
    return db.query(Permission).filter(Permission.role_id == role_id).all()


def test_seed_repairs_admin_role_idempotently(db):
    admin = Role(code="admin", name="Quản trị hệ thống")
    legacy = Role(code="ADMINISTRATOR", name="Quản trị đời cũ")
    db.add_all([admin, legacy])
    db.flush()
    #  Giống prod 30/09: thiếu hẳn vài entity, vài dòng bị bỏ tick / thu hẹp phạm vi.
    db.add(Permission(role_id=admin.id, entity=ENTITIES[0], can_read=True, scope="own"))
    db.add(Permission(role_id=admin.id, entity=ENTITIES[1], scope="all",
                      **{f"can_{a}": True for a in ACTIONS if a != "delete"}))
    db.add(Permission(role_id=admin.id, entity="entity_da_bo", can_read=True, scope="own"))
    db.add(Permission(role_id=legacy.id, entity=ENTITIES[0], can_read=True, scope="own"))
    db.commit()

    ensure_admin_role(db)
    first = {(p.entity, p.scope, tuple(getattr(p, f"can_{a}") for a in ACTIONS))
             for p in _admin_rows(db, admin.id)}
    ensure_admin_role(db)
    second = {(p.entity, p.scope, tuple(getattr(p, f"can_{a}") for a in ACTIONS))
              for p in _admin_rows(db, admin.id)}

    assert first == second
    rows = [p for p in _admin_rows(db, admin.id) if p.entity in ENTITIES]
    assert len(rows) == len(ENTITIES)
    assert all(p.scope == "all" and all(getattr(p, f"can_{a}") for a in ACTIONS) for p in rows)
    #  Dòng entity đã bỏ khỏi ENTITIES: không ép, không xóa.
    stale = [p for p in _admin_rows(db, admin.id) if p.entity == "entity_da_bo"]
    assert len(stale) == 1 and stale[0].scope == "own"
    #  Ngoại lệ D-018 CHỈ cho `admin`: dòng có sẵn của ADMINISTRATOR giữ nguyên.
    legacy_row = db.query(Permission).filter(Permission.role_id == legacy.id,
                                             Permission.entity == ENTITIES[0]).one()
    assert legacy_row.scope == "own" and legacy_row.can_write is False


def test_seed_prod_runs_ensure_admin_role():
    """seed_prod gọi đúng hàm đã kiểm ở trên — đổi tên/bỏ bước là bài này đỏ."""
    import inspect

    from app import seed_prod

    assert "ensure_admin_role(db)" in inspect.getsource(seed_prod.run)


# ── 4. Tool AI lập bộ tài khoản ──────────────────────────────────────────────────────────

@pytest.fixture
def tool_world(db, world):
    pur_staff = Role(code="pur_staff", name="Nhân viên thu mua")
    db.add(pur_staff)
    db.flush()
    db.add(Permission(role_id=pur_staff.id, entity="purchase_request", can_read=True, scope="all"))
    db.commit()
    world.pur_staff = pur_staff
    return world


def _propose(db, actor, args):
    return T.run_tool(db, actor, "propose_account_setup", args)


def test_tool_admin_may_add_role_to_self(db, tool_world):
    out = _propose(db, tool_world.a, {"employee": "ADMIN_A", "role_codes": ["pur_staff"]})
    assert out["status"] == "ready", out
    confirm_account_setup(db, tool_world.a, out["proposal"]["confirm_token"])
    assert tool_world.pur_staff.id in user_service._role_ids(db, tool_world.a.id)
    assert pe.is_system_admin(db, tool_world.a.id)


def test_tool_refuses_to_drop_callers_own_admin(db, tool_world):
    out = _propose(db, tool_world.a, {"employee": "ADMIN_A", "role_codes": ["pur_staff"],
                                      "replace_roles": True})
    assert out.get("denied") is True
    assert out["reason"] == SELF_ADMIN_REMOVAL_REFUSED
    assert pe.is_system_admin(db, tool_world.a.id)


def _let_n_use_tool(db, world) -> None:
    """N có user.write + role.read; thêm employee.read (tool đòi) và purchase_request.read
    (để qua L2 khi gán pur_staff)."""
    extra = Role(code="VT_TOOL_N", name="Đủ quyền dùng tool")
    db.add(extra)
    db.flush()
    db.add(Permission(role_id=extra.id, entity="employee", can_read=True, scope="all"))
    db.add(Permission(role_id=extra.id, entity="purchase_request", can_read=True, scope="all"))
    _give(db, world.n, extra.id)


def test_tool_non_admin_self_still_denied(db, tool_world):
    _let_n_use_tool(db, tool_world)
    out = _propose(db, tool_world.n, {"employee": "NGUOI_N", "role_codes": ["pur_staff"]})
    assert out.get("denied") is True
    assert out["reason"] == pe.SELF_CHANGE_MESSAGE


def test_tool_cannot_strip_last_active_admin_from_someone_else(db, tool_world):
    """B đã khóa → A là quản trị hoạt động cuối. N dùng `replace_roles` gán A chỉ còn
    pur_staff là tước nốt admin của cả hệ → từ chối ngay ở bước đề xuất."""
    _let_n_use_tool(db, tool_world)
    tool_world.b.is_active = False
    db.commit()
    out = _propose(db, tool_world.n, {"employee": "ADMIN_A", "role_codes": ["pur_staff"],
                                      "replace_roles": True})
    assert out.get("denied") is True
    assert out["reason"] == pe.LAST_ADMIN_MESSAGE
    assert pe.is_system_admin(db, tool_world.a.id)
