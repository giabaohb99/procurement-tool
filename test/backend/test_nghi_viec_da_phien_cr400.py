"""bao-CR-400 — nghỉ việc thì khóa tài khoản + đá phiên; lịch sử đăng nhập tự thân.

Trước CR này, HR chuyển hồ sơ sang "Nghỉ việc" là xong việc của HR — tài khoản
đăng nhập đứng yên, vé cũ còn hạn cứ vào tiếp (BM-015). Nay:

* `status -> resigned` hoặc `is_active -> False` trong `update_employee` khóa mọi
  tài khoản gắn kèm và bắt đăng nhập lại ngay (`token_version` tăng), phiên ghi
  lý do `EMPLOYEE_RESIGNED = 6`. Chỉ bắt lúc CHUYỂN; mở lại hồ sơ KHÔNG mở tài khoản.
* `detach_users` (xóa hồ sơ) cũng đá phiên với cùng lý do.
* `/api/auth/sessions` trả thêm `alive_count`; `/api/auth/sessions/history` là
  lịch sử của chính mình, cùng bộ dựng với cửa quản trị.
"""
import json
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from app.core.audit import record
from app.core.auth import perm_cache_clear
from app.core.logging_codes import SOURCE_API
from app.core.request_context import open_context
from app.modules.audit.model import AuditLog
from app.modules.auth.controller import my_login_history, my_sessions
from app.modules.employee import service as emp_service
from app.modules.employee.model import Employee
from app.modules.employee.schema import EmployeeUpdate
from app.modules.login_session.constants import REVOKE_REASON_LABELS, RevokeReason
from app.modules.login_session.controller import login_history
from app.modules.login_session.model import LoginSession
from app.modules.login_session.service import start_session
from app.modules.user.model import User

CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
ACTOR = 1


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


def _open(db, user_id, ip="10.0.0.5"):
    return start_session(db, db.get(User, user_id), ip=ip, user_agent=CHROME)


def _data(resp):
    return json.loads(resp.body)["data"]


def _sessions_of(db, user_id):
    return db.query(LoginSession).filter(LoginSession.user_id == user_id).all()


def _audit(db, entity, action, entity_id=None):
    q = db.query(AuditLog).filter(AuditLog.entity == entity, AuditLog.action == action)
    if entity_id is not None:
        q = q.filter(AuditLog.entity_id == entity_id)
    return q.all()


# ── 1. Bộ mã ────────────────────────────────────────────────────────────────────

def test_revoke_reason_has_employee_resigned_label():
    assert RevokeReason.EMPLOYEE_RESIGNED == 6
    assert REVOKE_REASON_LABELS[RevokeReason.EMPLOYEE_RESIGNED] == "Nghỉ việc"


# ── 2. Chuyển trạng thái nghỉ việc ─────────────────────────────────────────────

def test_status_resigned_locks_user_and_revokes_sessions(db, seed):
    a = _open(db, seed.u_req_id)
    b = _open(db, seed.u_req_id, ip="10.0.0.6")
    user = db.get(User, seed.u_req_id)
    before = user.token_version

    emp_service.update_employee(db, seed.emp_req_id, EmployeeUpdate(status="resigned"), ACTOR)

    db.refresh(user)
    assert user.is_active is False
    assert user.token_version == before + 1
    for s in (a, b):
        db.refresh(s)
        assert s.revoked_at is not None
        assert s.revoke_reason == RevokeReason.EMPLOYEE_RESIGNED
        assert s.revoked_by == ACTOR


def test_is_active_off_locks_user_too(db, seed):
    s = _open(db, seed.u_req_id)
    user = db.get(User, seed.u_req_id)

    emp_service.update_employee(db, seed.emp_req_id, EmployeeUpdate(is_active=False), ACTOR)

    db.refresh(user)
    db.refresh(s)
    assert user.is_active is False
    assert s.revoke_reason == RevokeReason.EMPLOYEE_RESIGNED


def test_resign_writes_audit_rows_on_both_entities(db, seed):
    user = db.get(User, seed.u_req_id)
    emp_service.update_employee(db, seed.emp_req_id, EmployeeUpdate(status="resigned"), ACTOR)

    emp_rows = _audit(db, "employee", "update", seed.emp_req_id)
    assert emp_rows and "Nghỉ việc" in (emp_rows[-1].message or "")
    user_rows = _audit(db, "user", "deactivate", user.id)
    assert len(user_rows) == 1
    assert "nghỉ việc" in (user_rows[0].message or "")


def test_saving_an_already_resigned_profile_does_not_lock_again(db, seed):
    """Sửa ghi chú trên hồ sơ đã nghỉ thì không bắn thêm dòng khóa nào."""
    user = db.get(User, seed.u_req_id)
    emp_service.update_employee(db, seed.emp_req_id, EmployeeUpdate(status="resigned"), ACTOR)
    db.refresh(user)
    ver = user.token_version

    emp_service.update_employee(db, seed.emp_req_id,
                                EmployeeUpdate(status="resigned", phone="0900000000"), ACTOR)

    db.refresh(user)
    assert user.token_version == ver
    assert len(_audit(db, "user", "deactivate", user.id)) == 1


def test_reopening_profile_does_not_reactivate_user(db, seed):
    """Không có chiều ngược: mở lại hồ sơ là việc của HR ở màn Tài khoản."""
    user = db.get(User, seed.u_req_id)
    emp_service.update_employee(db, seed.emp_req_id, EmployeeUpdate(status="resigned"), ACTOR)

    emp_service.update_employee(db, seed.emp_req_id,
                                EmployeeUpdate(status="official", is_active=True), ACTOR)

    db.refresh(user)
    assert user.is_active is False
    assert db.get(Employee, seed.emp_req_id).status == "official"


def test_unchanged_profile_save_leaves_user_alone(db, seed):
    s = _open(db, seed.u_req_id)
    user = db.get(User, seed.u_req_id)
    ver = user.token_version

    emp_service.update_employee(db, seed.emp_req_id, EmployeeUpdate(phone="0900000000"), ACTOR)

    db.refresh(user)
    db.refresh(s)
    assert user.is_active is True and user.token_version == ver
    assert s.revoked_at is None


def test_email_conflict_rolls_back_the_lock_too(db, seed):
    """Email đụng tài khoản khác → 400, và việc khóa/đá phiên hoàn tác cùng hồ sơ."""
    other = db.get(User, seed.u_nstm_id)
    other.email = "dung.email@dego.vn"
    db.commit()
    s = _open(db, seed.u_req_id)
    user = db.get(User, seed.u_req_id)
    ver = user.token_version

    with pytest.raises(HTTPException) as exc:
        emp_service.update_employee(
            db, seed.emp_req_id,
            EmployeeUpdate(email="dung.email@dego.vn", status="resigned"), ACTOR)
    assert exc.value.status_code == 400

    db.refresh(user)
    db.refresh(s)
    assert user.is_active is True and user.token_version == ver
    assert s.revoked_at is None
    assert db.get(Employee, seed.emp_req_id).status != "resigned"


# ── 3. Xóa hồ sơ ────────────────────────────────────────────────────────────────

def test_delete_employee_revokes_sessions_with_resigned_reason(db, seed):
    s = _open(db, seed.u_req_id)
    user = db.get(User, seed.u_req_id)
    before = user.token_version

    emp_service.delete_employee(db, seed.emp_req_id, ACTOR)

    db.refresh(user)
    db.refresh(s)
    assert user.is_active is False and user.employee_id == 0
    assert user.token_version == before + 1
    assert s.revoke_reason == RevokeReason.EMPLOYEE_RESIGNED


# ── 4. Cửa tự thân ──────────────────────────────────────────────────────────────

def test_my_sessions_reports_alive_count_regardless_of_filter(db, seed):
    a = _open(db, seed.u_req_id)
    b = _open(db, seed.u_req_id, ip="10.0.0.6")
    expired = _open(db, seed.u_req_id, ip="10.0.0.7")
    expired.expires_at = datetime.now() - timedelta(minutes=1)
    b.revoked_at = datetime.now()
    b.revoke_reason = RevokeReason.SELF_LOGOUT
    db.commit()
    _open(db, seed.u_nstm_id)     # phiên người khác không được đếm
    req = db.get(User, seed.u_req_id)

    with open_context(SOURCE_API, user_id=req.id) as ctx:
        ctx.session_id = a.id
        all_rows = _data(my_sessions(active_only=False, user=req, db=db))
        alive_rows = _data(my_sessions(active_only=True, user=req, db=db))
    assert all_rows["alive_count"] == 1
    assert alive_rows["alive_count"] == 1
    assert len(all_rows["items"]) == 3


def test_my_login_history_is_locked_to_self(db, seed):
    _open(db, seed.u_req_id, ip="203.0.113.9")
    _open(db, seed.u_nstm_id, ip="198.51.100.1")
    req = db.get(User, seed.u_req_id)
    record(db, 0, "auth", 0, "login_failed",
           f"Đăng nhập thất bại cho tài khoản '{req.email}' — sai mật khẩu")

    out = _data(my_login_history(days=90, user=req, db=db))

    assert out["days"] == 90
    assert out["login_count"] == 1 and out["failed_count"] == 1
    ips = {it["ip"] for it in out["items"]}
    assert "203.0.113.9" in ips and "198.51.100.1" not in ips


def test_self_and_admin_history_share_one_builder(db, seed, cap_quyen):
    _open(db, seed.u_req_id, ip="203.0.113.9")
    req = db.get(User, seed.u_req_id)
    hr = db.get(User, seed.u_nstm_id)
    cap_quyen(hr.id, "login_session", scope="all", read=True)

    mine = _data(my_login_history(days=30, user=req, db=db))
    theirs = _data(login_history(user_id=req.id, days=30, user=hr, db=db))

    assert mine == theirs
