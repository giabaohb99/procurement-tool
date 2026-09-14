"""bao-CR-395 (CR-312 P3b) — màn PHIÊN ĐĂNG NHẬP: ba màn, một API.

Đóng nốt phần còn lại của **BM-002**: P3a (bao-CR-360) đã có bảng phiên và
đăng xuất có hiệu lực thật, nhưng chưa ai NHÌN thấy phiên và chưa ai ĐÁ được
phiên của người khác. Tệp này chốt:

1. Khóa `login_session` có trong `ENTITIES`, có nhãn, có phạm vi, và KHÔNG rơi
   vào tay Quản lý thu mua qua vòng `_PUR_MANAGER_PERMS`.
2. Phạm vi: `own` chỉ thấy phiên của mình, `all` thấy hết; `get_scoped` chặn
   đá phiên ngoài phạm vi (404, không phải 403).
3. Đá MỘT phiên → `revoked_at` + lý do `ADMIN_KICK` + dòng nhật ký `session_revoked`
   ghi lên NGƯỜI BỊ ĐÁ; đá lại lần hai → 400.
4. Bắt đăng nhập lại → `token_version` tăng (hiệu lực tức thì) + mọi phiên thu hồi.
5. Lịch sử 90 ngày HỢP dòng phiên với dòng `login_failed` (nối bằng chuỗi
   `tài khoản '<email>'` — dòng thất bại có `entity_id = 0`).
6. Khóa tài khoản (`user/service.set_active`) tự thu hồi phiên với lý do
   `ACCOUNT_LOCKED`.
7. Ba endpoint «Thiết bị của tôi» KHÔNG cần grant nào; không đá được phiên của
   người khác qua đường đó (404); «đăng xuất mọi thiết bị khác» chừa phiên đang bấm.
"""
import json

import pytest
from fastapi import HTTPException

from app.core.audit import record
from app.core.auth import perm_cache_clear
from app.core.logging_codes import SOURCE_API
from app.core.permissions import ENTITIES, ENTITY_LABELS
from app.core.request_context import open_context
from app.core.scoping import SCOPE_FIELDS
from app.modules.audit.model import AuditLog
from app.modules.auth.controller import my_sessions, revoke_my_other_sessions, revoke_my_session
from app.modules.login_session.constants import RevokeReason
from app.modules.login_session.controller import (list_sessions, login_history, logout_all,
                                                  revoke_one)
from app.modules.login_session.model import LoginSession
from app.modules.login_session.service import start_session
from app.modules.user.model import User
from app.modules.user.service import set_active
from app.seed import STD_ROLES, _SYS_ENTITIES

CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
PAGE = {"page": 1, "page_size": 50, "offset": 0, "limit": 50}


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


def _open(db, user_id, ip="10.0.0.5"):
    return start_session(db, db.get(User, user_id), ip=ip, user_agent=CHROME)


def _data(resp):
    return json.loads(resp.body)["data"]


def _auth_rows(db, action):
    return db.query(AuditLog).filter(AuditLog.entity == "auth", AuditLog.action == action).all()


# ── 1. Khóa quyền ───────────────────────────────────────────────────────────────
def test_khoa_login_session_khai_du_ba_noi():
    assert "login_session" in ENTITIES
    assert ENTITY_LABELS["login_session"] == "Phiên đăng nhập"
    assert SCOPE_FIELDS["login_session"] == {"owner": "user_id"}


def test_quan_ly_thu_mua_khong_tu_co_khoa_phien():
    """`_PUR_MANAGER_PERMS` quét cả `ENTITIES` — quên `_SYS_ENTITIES` là Quản lý
    thu mua đá được phiên của toàn công ty."""
    assert "login_session" in _SYS_ENTITIES
    for role in ("pur_manager", "pur_admin"):
        assert "login_session" not in STD_ROLES[role]["perms"]
    assert STD_ROLES["hr_profile"]["perms"]["login_session"] == (["read"], "all")


# ── 2. Phạm vi ──────────────────────────────────────────────────────────────────
def test_own_chi_thay_phien_cua_minh_all_thay_het(db, seed, cap_quyen):
    _open(db, seed.u_req_id)
    _open(db, seed.u_nstm_id)
    req = db.get(User, seed.u_req_id)
    nstm = db.get(User, seed.u_nstm_id)

    cap_quyen(req.id, "login_session", scope="own", read=True)
    mine = _data(list_sessions(user_id=0, active_only=True, user=req, db=db, pg=PAGE))
    assert mine["total"] == 1 and mine["items"][0]["user_id"] == req.id

    cap_quyen(nstm.id, "login_session", scope="all", read=True)
    every = _data(list_sessions(user_id=0, active_only=True, user=nstm, db=db, pg=PAGE))
    assert every["total"] == 2
    assert {it["user_id"] for it in every["items"]} == {req.id, nstm.id}
    assert all(it["user_name"] for it in every["items"])   # tên người, không phải số


def test_own_khong_da_duoc_phien_nguoi_khac(db, seed, cap_quyen):
    other = _open(db, seed.u_nstm_id)
    req = db.get(User, seed.u_req_id)
    cap_quyen(req.id, "login_session", scope="own", read=True, delete=True)
    with pytest.raises(HTTPException) as exc:
        revoke_one(other.id, user=req, db=db)
    assert exc.value.status_code == 404
    db.refresh(other)
    assert other.revoked_at is None


# ── 3. Đá một phiên ─────────────────────────────────────────────────────────────
def test_admin_da_mot_phien_ghi_ly_do_va_nhat_ky(db, seed, cap_quyen):
    victim = _open(db, seed.u_req_id, ip="203.0.113.9")
    admin = db.get(User, seed.u_nstm_id)
    cap_quyen(admin.id, "login_session", scope="all", read=True, delete=True)

    revoke_one(victim.id, user=admin, db=db)
    db.refresh(victim)
    assert victim.revoked_at is not None
    assert victim.revoke_reason == RevokeReason.ADMIN_KICK
    assert victim.revoked_by == admin.id

    rows = _auth_rows(db, "session_revoked")
    assert len(rows) == 1
    assert rows[0].entity_id == seed.u_req_id and rows[0].created_by == admin.id
    assert "203.0.113.9" in rows[0].message

    with pytest.raises(HTTPException) as exc:
        revoke_one(victim.id, user=admin, db=db)
    assert exc.value.status_code == 400


# ── 4. Bắt đăng nhập lại ────────────────────────────────────────────────────────
def test_bat_dang_nhap_lai_tang_token_version_va_cat_het(db, seed, cap_quyen):
    _open(db, seed.u_req_id)
    _open(db, seed.u_req_id, ip="10.0.0.6")
    target = db.get(User, seed.u_req_id)
    before = target.token_version
    admin = db.get(User, seed.u_nstm_id)
    cap_quyen(admin.id, "login_session", scope="all", read=True, delete=True)

    out = _data(logout_all(target.id, user=admin, db=db))
    assert out["revoked"] == 2
    db.refresh(target)
    assert target.token_version == before + 1
    alive = db.query(LoginSession).filter(LoginSession.user_id == target.id,
                                          LoginSession.revoked_at.is_(None)).count()
    assert alive == 0
    reasons = {r.revoke_reason for r in
               db.query(LoginSession).filter(LoginSession.user_id == target.id)}
    assert reasons == {RevokeReason.FORCE_RELOGIN}
    assert len(_auth_rows(db, "logout_all")) == 1


def test_own_khong_bat_nguoi_khac_dang_nhap_lai(db, seed, cap_quyen):
    _open(db, seed.u_nstm_id)
    req = db.get(User, seed.u_req_id)
    cap_quyen(req.id, "login_session", scope="own", read=True, delete=True)
    with pytest.raises(HTTPException) as exc:
        logout_all(seed.u_nstm_id, user=req, db=db)
    assert exc.value.status_code == 404


# ── 5. Lịch sử đăng nhập ────────────────────────────────────────────────────────
def test_lich_su_hop_phien_voi_dang_nhap_that_bai(db, seed, cap_quyen):
    sess = _open(db, seed.u_req_id, ip="203.0.113.9")
    record(db, 0, "auth", 0, "login_failed",
           "Đăng nhập thất bại: tài khoản 'TESTREQ' — Sai mật khẩu (IP 198.51.100.7)")
    #  Thất bại của NGƯỜI KHÁC không được lẫn vào.
    record(db, 0, "auth", 0, "login_failed",
           "Đăng nhập thất bại: tài khoản 'DEMONV' — Sai mật khẩu (IP 198.51.100.8)")
    hr = db.get(User, seed.u_nstm_id)
    cap_quyen(hr.id, "login_session", scope="all", read=True)

    out = _data(login_history(user_id=seed.u_req_id, days=90, user=hr, db=db))
    assert out["login_count"] == 1 and out["failed_count"] == 1
    kinds = [(it["ok"], it["ip"]) for it in out["items"]]
    assert (True, "203.0.113.9") in kinds
    assert any(not ok for ok, _ in kinds)
    assert all("DEMONV" not in it["message"] for it in out["items"])
    login_row = next(it for it in out["items"] if it["ok"])
    assert login_row["session_id"] == sess.id and login_row["ending"] == "Còn hiệu lực"


# ── 6. Khóa tài khoản ───────────────────────────────────────────────────────────
def test_khoa_tai_khoan_thu_hoi_moi_phien(db, seed):
    sess = _open(db, seed.u_req_id)
    target = db.get(User, seed.u_req_id)
    before = target.token_version
    set_active(db, target.id, False, seed.u_nstm_id)
    db.refresh(sess)
    db.refresh(target)
    assert sess.revoked_at is not None
    assert sess.revoke_reason == RevokeReason.ACCOUNT_LOCKED
    assert sess.revoked_by == seed.u_nstm_id
    assert target.token_version == before + 1


# ── 7. Thiết bị của tôi — không cần grant ───────────────────────────────────────
def test_thiet_bi_cua_toi_khong_can_grant_va_danh_dau_phien_hien_tai(db, seed):
    a = _open(db, seed.u_req_id)
    b = _open(db, seed.u_req_id, ip="10.0.0.6")
    _open(db, seed.u_nstm_id)
    req = db.get(User, seed.u_req_id)

    with open_context(SOURCE_API, user_id=req.id) as ctx:
        ctx.session_id = a.id
        out = _data(my_sessions(active_only=True, user=req, db=db))
    assert {it["id"] for it in out["items"]} == {a.id, b.id}
    assert out["current_session_id"] == a.id
    assert [it["id"] for it in out["items"] if it["is_current"]] == [a.id]


def test_tu_da_thiet_bi_cua_minh_nhung_khong_da_duoc_cua_nguoi_khac(db, seed):
    mine = _open(db, seed.u_req_id)
    theirs = _open(db, seed.u_nstm_id)
    req = db.get(User, seed.u_req_id)

    with pytest.raises(HTTPException) as exc:
        revoke_my_session(theirs.id, user=req, db=db)
    assert exc.value.status_code == 404

    revoke_my_session(mine.id, user=req, db=db)
    db.refresh(mine)
    db.refresh(theirs)
    assert mine.revoke_reason == RevokeReason.SELF_LOGOUT and theirs.revoked_at is None


def test_dang_xuat_moi_thiet_bi_khac_chua_phien_dang_bam(db, seed):
    current = _open(db, seed.u_req_id)
    other = _open(db, seed.u_req_id, ip="10.0.0.6")
    req = db.get(User, seed.u_req_id)
    before = req.token_version

    with open_context(SOURCE_API, user_id=req.id) as ctx:
        ctx.session_id = current.id
        out = _data(revoke_my_other_sessions(user=req, db=db))
    assert out["revoked"] == 1
    db.refresh(current)
    db.refresh(other)
    db.refresh(req)
    assert current.revoked_at is None and other.revoked_at is not None
    assert req.token_version == before   # không đá chính mình
