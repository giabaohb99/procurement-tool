"""Tool lập BỘ TÀI KHOẢN thu mua qua Trợ lý AI (bao-CR-435) — `propose_account_setup`
+ `confirm_account_setup`.

Nguyên tắc phải giữ, giống tầng sửa phiếu (CR-218): token chỉ là TỜ ĐỀ XUẤT có hạn dùng.
Bộ test ép đủ các cửa: thiếu `user.write` / tự gán cho mình / gán vai trò cấp quyền mình không
có (L2) / hồ sơ không có, nhiều hồ sơ khớp, chưa có tài khoản / token của người khác / token hết
hạn / mất quyền giữa hai bước — và happy path phải ghi qua ĐÚNG hai service của màn Phân quyền
(`assign_roles` + `set_user_scope`), chạy lại thì mọi dòng «không đổi», không được ghi thêm dòng
«Chỉ trong công ty» nào (bao-CR-434).
"""
import json
import time

import pytest
from fastapi import HTTPException

from app.core.auth import perm_cache_clear
from app.modules.assistant import tools as T
from app.modules.assistant.tools.account_setup_tool import (
    CONFIRM_TTL_SECONDS,
    PROPOSAL_KIND,
    _fernet,
    confirm_account_setup,
)
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.role.model import Permission, Role
from app.modules.user import service as user_service
from app.modules.user.model import User, UserRole, UserScope
from app.modules.user.schema import ScopeUpdate


# ── Dựng cảnh ─────────────────────────────────────────────────────────────────────────────

def _make_role(db, code, name, entity="purchase_request", **actions):
    role = Role(code=code, name=name)
    db.add(role)
    db.flush()
    co = {f"can_{k}": True for k in actions}
    db.add(Permission(role_id=role.id, entity=entity, scope="all", **co))
    db.flush()
    return role


@pytest.fixture
def world(db, seed, cap_quyen):
    """Người thao tác = DEMOTP (có user.write + role.read + employee.read + purchase_request
    read/write); đích = TESTREQ; bộ vai trò mẫu chỉ cấp quyền nằm trong tay người thao tác,
    trừ `pur_manager` cố ý cấp `payable.read` mà người thao tác KHÔNG có (để ép L2)."""
    actor = db.query(User).filter(User.email == "DEMOTP").first()
    cap_quyen(actor.id, "user", scope="all", read=True, write=True)
    cap_quyen(actor.id, "role", scope="all", read=True)
    cap_quyen(actor.id, "employee", scope="all", read=True)
    cap_quyen(actor.id, "purchase_request", scope="all", read=True, write=True)

    roles = {
        "employee": _make_role(db, "employee", "Nhân sự", read=True),
        "pur_staff": _make_role(db, "pur_staff", "Nhân viên thu mua", read=True, write=True),
        "pur_manager": _make_role(db, "pur_manager", "Quản lý thu mua", entity="payable", read=True),
    }
    factory = Department(code="DORG", name="Dego Organic", company_id=seed.company_id, is_active=True)
    db.add(factory)
    db.commit()
    perm_cache_clear()
    return {"actor": actor, "target": db.get(User, seed.u_req_id), "roles": roles}


def _propose(db, actor, args):
    return T.run_tool(db, actor, "propose_account_setup", args)


def _status_of(lines, kind=None):
    return [line["status"] for line in lines if kind is None or line["kind"] == kind]


# ── propose: các cửa chặn ─────────────────────────────────────────────────────────────────

def test_missing_user_write_is_denied(db, seed, cap_quyen):
    """Có role.read + employee.read mà thiếu user.write thì không đề xuất được — cửa ghi thật
    của màn Phân quyền là user.write, tool không được rẻ hơn màn."""
    actor = db.query(User).filter(User.email == "DEMOTP").first()
    cap_quyen(actor.id, "role", scope="all", read=True)
    cap_quyen(actor.id, "employee", scope="all", read=True)
    _make_role(db, "pur_staff", "Nhân viên thu mua", read=True)
    db.commit()
    out = _propose(db, actor, {"employee": "TESTREQ", "role_codes": ["pur_staff"]})
    assert out.get("denied") is True
    assert "user.write" in out["reason"]


def test_role_outside_template_is_rejected(db, world):
    out = _propose(db, world["actor"], {"employee": "TESTREQ", "role_codes": ["admin"]})
    assert "error" in out and "admin" in out["error"]
    assert "proposal" not in out


def test_unknown_department_is_rejected(db, world):
    out = _propose(db, world["actor"], {"employee": "TESTREQ", "role_codes": ["pur_staff"],
                                        "exclude_departments": ["Phòng Không Có"]})
    assert "error" in out and "Phòng Không Có" in out["error"]


def test_employee_not_found_is_blocked_not_created(db, world):
    """Không có hồ sơ thì DỪNG — Bước 1 (tạo hồ sơ nhân sự) vẫn làm tay."""
    out = _propose(db, world["actor"], {"employee": "KHONGCO", "role_codes": ["pur_staff"]})
    assert out["status"] == "blocked" and out["reason"] == "not_found"
    assert db.query(Employee).filter(Employee.code == "KHONGCO").first() is None


def test_ambiguous_name_returns_candidates_without_token(db, world):
    """«NSTM» khớp cả NSTM Chính lẫn NSTM Dự Phòng — không được đoán, trả danh sách để hỏi lại."""
    out = _propose(db, world["actor"], {"employee": "NSTM", "role_codes": ["pur_staff"]})
    assert out["status"] == "ambiguous"
    assert {c["code"] for c in out["candidates"]} == {"DEMONV", "BACKUP01"}
    assert "proposal" not in out


def test_employee_without_login_account_is_blocked(db, world, seed):
    """Có hồ sơ mà chưa có tài khoản: tool KHÔNG tạo tài khoản, KHÔNG đặt mật khẩu."""
    db.add(Employee(code="NOACC", full_name="Chưa Có Tài Khoản", company_id=seed.company_id,
                    department_id=seed.dept_id, is_active=True))
    db.commit()
    before = db.query(User).count()
    out = _propose(db, world["actor"], {"employee": "NOACC", "role_codes": ["pur_staff"]})
    assert out["status"] == "blocked" and out["reason"] == "no_account"
    assert out["employee"]["has_account"] is False
    assert db.query(User).count() == before


def test_self_target_is_denied(db, world):
    """L1: người thao tác gõ đúng mã của chính mình thì bị chặn ngay ở bước đề xuất."""
    out = _propose(db, world["actor"], {"employee": "DEMOTP", "role_codes": ["pur_staff"]})
    assert out.get("denied") is True


def test_granting_permission_actor_lacks_is_denied(db, world):
    """L2: pur_manager cấp payable.read mà người thao tác không có → không đề xuất được."""
    out = _propose(db, world["actor"], {"employee": "TESTREQ", "role_codes": ["pur_manager"]})
    assert out.get("denied") is True
    assert "proposal" not in out


def test_target_outside_user_scope_is_denied(db, seed, cap_quyen):
    """user.write phạm vi `own` thì tài khoản của người khác nằm ngoài tầm với."""
    actor = db.query(User).filter(User.email == "DEMOTP").first()
    cap_quyen(actor.id, "user", scope="own", read=True, write=True)
    cap_quyen(actor.id, "role", scope="all", read=True)
    cap_quyen(actor.id, "employee", scope="all", read=True)
    _make_role(db, "pur_staff", "Nhân viên thu mua", read=True)
    db.commit()
    out = _propose(db, actor, {"employee": "TESTREQ", "role_codes": ["pur_staff"]})
    assert out.get("denied") is True
    assert "phạm vi" in out["reason"]


# ── happy path + chạy lại ─────────────────────────────────────────────────────────────────

def _setup_args():
    return {"employee": "TESTREQ", "role_codes": ["employee", "pur_staff"],
            "exclude_departments": ["dego organic"]}


def test_propose_then_confirm_writes_roles_and_scope_via_services(db, world):
    actor, target, roles = world["actor"], world["target"], world["roles"]
    out = _propose(db, actor, _setup_args())
    assert out["status"] == "ready"
    proposal = out["proposal"]
    assert proposal["kind"] == PROPOSAL_KIND
    assert proposal["target_label"] == "Người YC (TESTREQ)"
    assert proposal["employee"]["department"] == "Phòng Test"
    #  Hai vai trò + hai dòng loại trừ (mỗi vai trò một dòng) — tất cả «thêm», chưa ghi gì.
    assert _status_of(proposal["lines"], "role") == ["thêm", "thêm"]
    assert _status_of(proposal["lines"], "scope") == ["thêm", "thêm"]
    assert proposal["changed"] == 4
    assert proposal["url"] == f"/system/permissions/users/{target.id}"
    assert db.query(UserRole).filter(UserRole.user_id == target.id).count() == 0
    assert db.query(UserScope).filter(UserScope.user_id == target.id).count() == 0
    #  Tên phòng gõ thường vẫn ra tên chính thức trong danh mục.
    assert any("«Dego Organic»" in line["label"] for line in proposal["lines"])

    result = confirm_account_setup(db, actor, proposal["confirm_token"])
    assert result["updated"] == ["vai trò", "phạm vi Nhân sự", "phạm vi Nhân viên thu mua"]
    assert set(result["roles"]) == {"Nhân sự", "Nhân viên thu mua"}
    assert user_service._role_ids(db, target.id) == sorted([roles["employee"].id, roles["pur_staff"].id])
    for code in ("employee", "pur_staff"):
        scope = user_service.get_user_scope(db, target.id, roles[code].id)
        assert scope["exclude_departments"] == ["Dego Organic"]
        #  bao-CR-434: tool không được tự khai «Chỉ trong công ty».
        assert scope["companies"] == []


def test_rerun_after_confirm_reports_everything_unchanged(db, world):
    """Chạy lại y nguyên: mọi dòng «không đổi», changed = 0, xác nhận lần nữa không ghi gì."""
    actor, target = world["actor"], world["target"]
    first = _propose(db, actor, _setup_args())
    confirm_account_setup(db, actor, first["proposal"]["confirm_token"])
    role_rows = db.query(UserRole.id).filter(UserRole.user_id == target.id).all()
    scope_rows = db.query(UserScope.id).filter(UserScope.user_id == target.id).all()

    second = _propose(db, actor, _setup_args())
    assert second["status"] == "ready"
    assert set(_status_of(second["proposal"]["lines"])) == {"không đổi"}
    assert second["proposal"]["changed"] == 0 and second["total"] == 0

    result = confirm_account_setup(db, actor, second["proposal"]["confirm_token"])
    assert result["updated"] == []
    #  Không xóa-ghi lại: id dòng giữ nguyên, tức service không bị gọi thừa.
    assert db.query(UserRole.id).filter(UserRole.user_id == target.id).all() == role_rows
    assert db.query(UserScope.id).filter(UserScope.user_id == target.id).all() == scope_rows


def test_add_role_keeps_existing_roles_unless_replace(db, world):
    """Mặc định là CỘNG THÊM: vai trò đang có giữ nguyên («không đổi»); replace_roles=true thì
    vai trò ngoài danh sách bị đề xuất «bỏ»."""
    actor, target, roles = world["actor"], world["target"], world["roles"]
    db.add(UserRole(user_id=target.id, role_id=roles["employee"].id))
    db.commit()

    out = _propose(db, actor, {"employee": "TESTREQ", "role_codes": ["pur_staff"]})
    by_code = {l["role_code"]: l["status"] for l in out["proposal"]["lines"] if l["kind"] == "role"}
    assert by_code == {"employee": "không đổi", "pur_staff": "thêm"}

    out = _propose(db, actor, {"employee": "TESTREQ", "role_codes": ["pur_staff"], "replace_roles": True})
    by_code = {l["role_code"]: l["status"] for l in out["proposal"]["lines"] if l["kind"] == "role"}
    assert by_code == {"employee": "bỏ", "pur_staff": "thêm"}
    confirm_account_setup(db, actor, out["proposal"]["confirm_token"])
    assert user_service._role_ids(db, target.id) == [roles["pur_staff"].id]


def test_company_include_is_warned_and_only_removed_on_request(db, world, seed):
    """Vai trò thu mua đang có «Chỉ trong công ty»: mặc định chỉ CẢNH BÁO (không tự gỡ),
    remove_company_include=true thì đề xuất «bỏ» và xác nhận xong ô công ty trống."""
    actor, target, roles = world["actor"], world["target"], world["roles"]
    db.add(UserRole(user_id=target.id, role_id=roles["pur_staff"].id))
    db.commit()
    user_service.set_user_scope(db, target.id, roles["pur_staff"].id,
                                ScopeUpdate(companies=[seed.company_id]), actor.id)

    out = _propose(db, actor, {"employee": "TESTREQ", "role_codes": ["pur_staff"]})
    assert any("Chỉ trong công ty" in w for w in out["proposal"]["warnings"])
    assert out["proposal"]["changed"] == 0
    assert user_service.get_user_scope(db, target.id, roles["pur_staff"].id)["companies"] == [seed.company_id]

    out = _propose(db, actor, {"employee": "TESTREQ", "role_codes": ["pur_staff"],
                               "remove_company_include": True})
    assert _status_of(out["proposal"]["lines"], "scope") == ["bỏ"]
    assert out["proposal"]["warnings"] == []
    confirm_account_setup(db, actor, out["proposal"]["confirm_token"])
    assert user_service.get_user_scope(db, target.id, roles["pur_staff"].id)["companies"] == []


def test_locked_account_gets_warning_but_still_proposes(db, world):
    target = world["target"]
    target.is_active = False
    db.commit()
    out = _propose(db, world["actor"], {"employee": "TESTREQ", "role_codes": ["pur_staff"]})
    assert out["status"] == "ready"
    assert out["proposal"]["employee"]["account_active"] is False
    assert any("KHÓA" in w for w in out["proposal"]["warnings"])


# ── confirm: token và kiểm lại lúc bấm ────────────────────────────────────────────────────

def test_confirm_with_someone_elses_token_is_403(db, world):
    """Token buộc vào người hỏi — đem token của DEMOTP cho DEMONV bấm là 403, không ghi gì."""
    actor, target = world["actor"], world["target"]
    out = _propose(db, actor, {"employee": "TESTREQ", "role_codes": ["pur_staff"]})
    other = db.query(User).filter(User.email == "DEMONV").first()
    with pytest.raises(HTTPException) as e:
        confirm_account_setup(db, other, out["proposal"]["confirm_token"])
    assert e.value.status_code == 403
    assert db.query(UserRole).filter(UserRole.user_id == target.id).count() == 0


def test_confirm_with_update_proposal_token_is_403(db, world):
    """Token của tầng sửa phiếu (CR-218) không được lọt vào cửa này dù cùng khóa Fernet."""
    actor = world["actor"]
    payload = {"k": "update_proposal", "u": actor.id, "t": world["target"].id, "roles": []}
    token = _fernet().encrypt(json.dumps(payload).encode()).decode()
    with pytest.raises(HTTPException) as e:
        confirm_account_setup(db, actor, token)
    assert e.value.status_code == 403


def test_expired_token_is_400(db, world):
    actor = world["actor"]
    payload = {"k": PROPOSAL_KIND, "u": actor.id, "t": world["target"].id, "roles": [], "scopes": {}}
    expired = _fernet().encrypt_at_time(
        json.dumps(payload).encode(), int(time.time()) - CONFIRM_TTL_SECONDS - 5).decode()
    with pytest.raises(HTTPException) as e:
        confirm_account_setup(db, actor, expired)
    assert e.value.status_code == 400


def test_garbage_token_is_400(db, world):
    with pytest.raises(HTTPException) as e:
        confirm_account_setup(db, world["actor"], "khong-phai-token")
    assert e.value.status_code == 400


def test_confirm_rechecks_permission_at_click_time(db, world):
    """Đề xuất xong bị rút user.write → bấm Xác nhận ăn 403, không ghi."""
    actor, target = world["actor"], world["target"]
    out = _propose(db, actor, {"employee": "TESTREQ", "role_codes": ["pur_staff"]})
    role_ids = [r.id for r in db.query(Role).filter(Role.code.like("VT_TEST_%")).all()]
    for perm in db.query(Permission).filter(Permission.role_id.in_(role_ids), Permission.entity == "user"):
        perm.can_write = False
    db.commit()
    perm_cache_clear()
    with pytest.raises(HTTPException) as e:
        confirm_account_setup(db, actor, out["proposal"]["confirm_token"])
    assert e.value.status_code == 403
    assert db.query(UserRole).filter(UserRole.user_id == target.id).count() == 0


def test_confirm_rechecks_escalation_when_role_gains_permission_later(db, world):
    """Giữa hai bước có ai tick thêm quyền vào vai trò được gán → L2 chặn lại lúc bấm."""
    actor, target, roles = world["actor"], world["target"], world["roles"]
    out = _propose(db, actor, {"employee": "TESTREQ", "role_codes": ["pur_staff"]})
    db.add(Permission(role_id=roles["pur_staff"].id, entity="payable", scope="all", can_read=True))
    db.commit()
    with pytest.raises(HTTPException) as e:
        confirm_account_setup(db, actor, out["proposal"]["confirm_token"])
    assert e.value.status_code == 403
    assert db.query(UserRole).filter(UserRole.user_id == target.id).count() == 0


def test_confirm_with_deleted_role_is_400(db, world):
    actor, roles = world["actor"], world["roles"]
    out = _propose(db, actor, {"employee": "TESTREQ", "role_codes": ["pur_staff"]})
    db.query(Permission).filter(Permission.role_id == roles["pur_staff"].id).delete()
    db.delete(roles["pur_staff"])
    db.commit()
    with pytest.raises(HTTPException) as e:
        confirm_account_setup(db, actor, out["proposal"]["confirm_token"])
    assert e.value.status_code == 400


def test_tool_is_registered_in_active_specs(db):
    assert "propose_account_setup" in {s.name for s in T._active_specs()}
