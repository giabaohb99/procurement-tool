"""bao-CR-313 / BM-003 + BM-004 — IP thật của người gọi và dấu vết gia hạn phiên.

- `get_client_ip`: `CF-Connecting-IP` thắng XFF giả; không có CF thì lấy phần tử CUỐI
  của XFF (nginx nối vào), không lấy phần tử đầu (client tự đặt); không có gì thì
  `request.client.host`; cả `request.client` cũng không có thì chuỗi cố định.
- limiter khóa theo cùng hàm đó (không còn `request.client.host`).
- `/api/auth/refresh`: token hỏng -> 401 + dòng `refresh_failed` ghi bởi hệ thống
  (created_by=0); tài khoản bị khóa -> 401 + `refresh_failed`.

⚠️ **Cập nhật bao-CR-360 (CR-312 P3a).** Hai điều ở đây đã đổi so với bản CR-313:

1. **QĐ-A** — gia hạn THÀNH CÔNG không còn đẻ dòng `refresh` nữa. Dấu vết chuyển
   sang hai cột đếm trên chính dòng phiên (`refresh_count`, `refreshed_at`), nên
   bài kiểm cũ "đúng 1 dòng `refresh`" nay đảo thành "KHÔNG dòng nào".
2. Gia hạn phải đi qua **cửa phiên**: refresh token không mang `jti`, hoặc phiên
   đã bị thu hồi, đều là 401 — không thì đăng xuất chẳng có hiệu lực gì, vì vé
   gia hạn cứ thế đẻ vé truy cập mới suốt bảy ngày.
"""
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers

from app.core.auth import create_refresh_token, perm_cache_clear
from app.core.client_ip import FALLBACK_IP, get_client_ip
from app.core.limiter import limiter
from app.modules.audit.model import AuditLog
from app.modules.auth import schema
from app.modules.auth.controller import refresh
from app.modules.login_session.constants import RevokeReason
from app.modules.login_session.service import revoke_session, start_session
from app.modules.user.model import User


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


def _req(headers: dict | None = None, host: str | None = "10.0.0.5"):
    return SimpleNamespace(
        headers=Headers(headers or {}),
        client=SimpleNamespace(host=host) if host else None,
    )


# ── get_client_ip ───────────────────────────────────────────────────────────────
def test_cf_connecting_ip_thang_xff_gia():
    req = _req({"CF-Connecting-IP": "203.0.113.9",
                "X-Forwarded-For": "9.9.9.9, 172.18.0.4",
                "X-Real-IP": "172.18.0.4"})
    assert get_client_ip(req) == "203.0.113.9"


def test_khong_cf_lay_phan_tu_cuoi_xff_chu_khong_lay_dau():
    req = _req({"X-Forwarded-For": "9.9.9.9, 198.51.100.7"})
    assert get_client_ip(req) == "198.51.100.7"
    assert get_client_ip(_req({"X-Forwarded-For": "198.51.100.7"})) == "198.51.100.7"


def test_khong_header_lay_client_host_roi_fallback():
    assert get_client_ip(_req({}, host="10.0.0.5")) == "10.0.0.5"
    assert get_client_ip(_req({}, host=None)) == FALLBACK_IP


def test_ip_bi_cat_ngan_khong_tran_cot():
    req = _req({"CF-Connecting-IP": "x" * 200})
    assert len(get_client_ip(req)) == 60


def test_limiter_khoa_theo_ip_that():
    req = _req({"CF-Connecting-IP": "203.0.113.9", "X-Forwarded-For": "9.9.9.9, 172.18.0.4"})
    assert limiter._key_func(req) == "203.0.113.9"


# ── refresh ─────────────────────────────────────────────────────────────────────
def _auth_rows(db, action):
    return db.query(AuditLog).filter(AuditLog.entity == "auth", AuditLog.action == action).all()


def _open_session(db, user_id, ip="203.0.113.9"):
    """Một phiên còn sống + refresh token hợp lệ của nó."""
    user = db.get(User, user_id)
    session = start_session(db, user, ip=ip, user_agent="Mozilla/5.0 (Windows NT 10.0) Chrome/120")
    return session, create_refresh_token(user.id, session.token_id, session.token_version)


def test_refresh_thanh_cong_khong_ghi_nhat_ky_chi_dap_cot_dem(db, seed):
    """QĐ-A: gia hạn êm xuôi thì đếm trên dòng phiên, không đẻ dòng nhật ký."""
    session, token = _open_session(db, seed.u_req_id)
    req = _req({"CF-Connecting-IP": "203.0.113.9", "X-Forwarded-For": "9.9.9.9, 172.18.0.4"})
    resp = refresh(req, schema.RefreshInput(refresh_token=token), db)

    assert json.loads(resp.body)["data"]["access_token"]
    assert _auth_rows(db, "refresh") == []
    db.refresh(session)
    assert session.refresh_count == 1 and session.refreshed_at is not None
    #  IP thật, không phải phần tử đầu của XFF do client tự đặt (BM-004).
    assert session.last_seen_ip == "203.0.113.9"


def test_refresh_doi_ip_van_cho_qua_nhung_ghi_lai(db, seed):
    session, token = _open_session(db, seed.u_req_id, ip="203.0.113.9")
    refresh(_req({"CF-Connecting-IP": "198.51.100.7"}),
            schema.RefreshInput(refresh_token=token), db)

    rows = _auth_rows(db, "refresh_ip_changed")
    assert len(rows) == 1
    assert "203.0.113.9" in rows[0].message and "198.51.100.7" in rows[0].message
    db.refresh(session)
    assert session.refresh_count == 1   # vẫn cho gia hạn, chỉ để lại dấu


def test_refresh_ve_khong_co_jti_bi_chan(db, seed):
    """Vé phát trước bao-CR-360 — chính là ca "mọi người bị đăng xuất một lần"."""
    with pytest.raises(HTTPException) as exc:
        refresh(_req({}), schema.RefreshInput(
            refresh_token=create_refresh_token(seed.u_req_id)), db)
    assert exc.value.status_code == 401
    assert len(_auth_rows(db, "refresh_failed")) == 1


def test_refresh_sau_khi_dang_xuat_bi_chan(db, seed):
    """Đây là BM-002: trước bản này, refresh token vẫn đẻ vé mới suốt 7 ngày."""
    session, token = _open_session(db, seed.u_req_id)
    revoke_session(db, session, RevokeReason.SELF_LOGOUT, seed.u_req_id)

    with pytest.raises(HTTPException) as exc:
        refresh(_req({}), schema.RefreshInput(refresh_token=token), db)
    assert exc.value.status_code == 401
    db.refresh(session)
    assert session.refresh_count == 0


def test_refresh_token_hong_401_va_ghi_that_bai(db, seed):
    req = _req({"X-Forwarded-For": "9.9.9.9, 198.51.100.7"})
    with pytest.raises(HTTPException) as exc:
        refresh(req, schema.RefreshInput(refresh_token="rac"), db)
    assert exc.value.status_code == 401

    rows = _auth_rows(db, "refresh_failed")
    assert len(rows) == 1
    assert rows[0].created_by == 0 and rows[0].entity_id == 0
    assert "IP 198.51.100.7" in rows[0].message
    assert _auth_rows(db, "refresh") == []


def test_refresh_tai_khoan_bi_khoa_401_va_ghi_that_bai(db, seed):
    user = db.get(User, seed.u_req_id)
    user.is_active = False
    db.flush()
    with pytest.raises(HTTPException) as exc:
        refresh(_req({}), schema.RefreshInput(refresh_token=create_refresh_token(user.id)), db)
    assert exc.value.status_code == 401

    rows = _auth_rows(db, "refresh_failed")
    assert len(rows) == 1 and rows[0].entity_id == user.id
    assert "IP 10.0.0.5" in rows[0].message
