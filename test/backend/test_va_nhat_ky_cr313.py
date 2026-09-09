"""bao-CR-313 / BM-001 — gác quyền + phạm vi cho `/api/audit-logs`.

Trước bản này ai đăng nhập cũng đọc được nhật ký của mọi phân hệ (kể cả `entity=auth`
chứa IP + tài khoản gõ sai mật khẩu). Bộ này gọi thẳng `list_logs` (không qua HTTP) với
user thật từ fixture `seed`, cấp vai trò bằng `_grant` như `test_payable_export_ticket16`.

Các ca:
- không grant: 403 cho `auth`, cho `purchase_request`, và cho lối toàn hệ (không entity);
- `setting.read`: lối toàn hệ đọc được, thấy cả `auth`;
- `purchase_request` phạm vi công ty: danh sách chỉ thấy phiếu công ty mình, id phiếu
  công ty khác -> 404, id phiếu công ty mình -> thấy;
- hồ sơ chính mình (`user`/`employee` + id mình) đọc được không cần khóa; id người khác 403;
- `faq` đi bằng khóa `help_article` (alias), entity không có trong bảng quyền -> 403.
"""
import json

import pytest
from fastapi import HTTPException

from app.core.audit import record
from app.core.auth import perm_cache_clear
from app.modules.audit.controller import list_logs
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.user.model import User


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


def _grant(db, user_id: int, entity: str, scope: str = "all", **actions):
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import UserRole
    role = Role(code=f"R{user_id}{scope}{entity[:6]}", name="Vai trò test")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity=entity, scope=scope,
                      can_read=actions.get("read", True),
                      can_write=actions.get("write", False)))
    db.add(UserRole(user_id=user_id, role_id=role.id))
    db.flush()
    perm_cache_clear()
    return role.id


def _logs(db, user, entity=None, entity_id=None, limit=100):
    resp = list_logs(entity=entity, entity_id=entity_id, limit=limit, db=db, user=user)
    return json.loads(resp.body)["data"]


def _status(fn):
    with pytest.raises(HTTPException) as exc:
        fn()
    return exc.value.status_code


def _two_prs(db, seed):
    """Một phiếu công ty mình, một phiếu công ty khác; mỗi phiếu một dòng nhật ký."""
    mine = PurchaseRequest(code="PR-MINE", company_id=seed.company_id, created_by=0)
    other = PurchaseRequest(code="PR-OTHER", company_id=seed.company_id + 100, created_by=0)
    db.add_all([mine, other])
    db.flush()
    record(db, seed.u_nstm_id, "purchase_request", mine.id, "create", "Tạo PR-MINE")
    record(db, seed.u_nstm_id, "purchase_request", other.id, "create", "Tạo PR-OTHER")
    return mine, other


# ── không grant ─────────────────────────────────────────────────────────────────
def test_khong_grant_khong_doc_duoc_gi(db, seed):
    user = db.get(User, seed.u_req_id)
    record(db, 0, "auth", 0, "login_failed", "Đăng nhập thất bại: tài khoản 'x' (IP 1.2.3.4)")

    assert _status(lambda: _logs(db, user, entity="auth")) == 403
    assert _status(lambda: _logs(db, user, entity="purchase_request")) == 403
    assert _status(lambda: _logs(db, user)) == 403


# ── lối toàn hệ ─────────────────────────────────────────────────────────────────
def test_setting_read_doc_duoc_toan_he_ke_ca_auth(db, seed):
    user = db.get(User, seed.u_req_id)
    _grant(db, user.id, "setting")
    record(db, 0, "auth", 0, "login_failed", "Đăng nhập thất bại (IP 1.2.3.4)")
    record(db, seed.u_nstm_id, "supplier", 1, "create", "Tạo NCC")

    rows = _logs(db, user)
    assert {r["entity"] for r in rows} == {"auth", "supplier"}
    assert _logs(db, user, entity="auth")[0]["action_label"] == "Đăng nhập thất bại"


def test_setting_write_khong_read_van_vao_duoc_toan_he(db, seed):
    user = db.get(User, seed.u_req_id)
    _grant(db, user.id, "setting", read=False, write=True)
    record(db, seed.u_nstm_id, "supplier", 1, "create", "Tạo NCC")
    assert len(_logs(db, user)) == 1


# ── phạm vi theo dòng ───────────────────────────────────────────────────────────
def test_pham_vi_cong_ty_chi_thay_phieu_cong_ty_minh(db, seed):
    user = db.get(User, seed.u_req_id)
    _grant(db, user.id, "purchase_request", scope="company")
    mine, other = _two_prs(db, seed)

    rows = _logs(db, user, entity="purchase_request")
    assert [r["entity_id"] for r in rows] == [mine.id]

    assert [r["entity_id"] for r in _logs(db, user, "purchase_request", mine.id)] == [mine.id]
    assert _status(lambda: _logs(db, user, "purchase_request", other.id)) == 404


def test_pham_vi_all_thay_het(db, seed):
    user = db.get(User, seed.u_req_id)
    _grant(db, user.id, "purchase_request", scope="all")
    mine, other = _two_prs(db, seed)
    assert {r["entity_id"] for r in _logs(db, user, entity="purchase_request")} == {mine.id, other.id}


# ── hồ sơ chính mình ────────────────────────────────────────────────────────────
def test_ho_so_chinh_minh_doc_duoc_khong_can_khoa(db, seed):
    user = db.get(User, seed.u_req_id)
    record(db, user.id, "user", user.id, "write", "Cập nhật ảnh chữ ký cá nhân")
    record(db, seed.u_nstm_id, "user", seed.u_nstm_id, "write", "Người khác đổi chữ ký")

    assert [r["entity_id"] for r in _logs(db, user, "user", user.id)] == [user.id]
    assert _logs(db, user, "employee", seed.emp_req_id) == []
    assert _status(lambda: _logs(db, user, "user", seed.u_nstm_id)) == 403
    assert _status(lambda: _logs(db, user, "employee", seed.emp_nstm_id)) == 403


# ── entity không có model / alias / rác ─────────────────────────────────────────
def test_faq_di_bang_khoa_help_article(db, seed):
    user = db.get(User, seed.u_req_id)
    record(db, seed.u_nstm_id, "faq", 7, "create", "Tạo câu hỏi")
    assert _status(lambda: _logs(db, user, "faq", 7)) == 403

    _grant(db, user.id, "help_article", scope="own")
    assert [r["entity_id"] for r in _logs(db, user, "faq")] == [7]
    assert [r["entity_id"] for r in _logs(db, user, "help_article")] == []


def test_entity_khong_co_trong_bang_quyen_403_tru_quan_tri(db, seed):
    user = db.get(User, seed.u_req_id)
    _grant(db, user.id, "purchase_request", scope="all")
    assert _status(lambda: _logs(db, user, "assistant")) == 403
    assert _status(lambda: _logs(db, user, "khong_ton_tai", 1)) == 403

    #  Quản trị (setting) lọc theo entity nào cũng được — không khắt khe hơn "không lọc".
    _grant(db, user.id, "setting")
    assert _logs(db, user, "assistant") == []
    assert _logs(db, user, "khong_ton_tai", 1) == []
