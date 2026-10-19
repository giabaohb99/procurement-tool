"""ai-CR-225 — mục NÊN 3 + 4 của bài rà Agent 1 (19/10/2026) trên OAuth cổng MCP, làm trước đợt prod hai.

Canh:
  3. Consent-phishing: tên ứng dụng là TỰ KHAI nên màn đồng ý phải dựa vào nơi quay về — tính theo HOSTNAME (bỏ userinfo,
     cổng), `https://chatgpt.com@evil.example/cb` không được hiện thành «chatgpt.com…»; host ngoài danh sách ứng dụng quen
     → `redirect_trusted = false`; đăng ký mới với userinfo trong redirect_uri bị từ chối. Màn quản trị xem / xóa ứng
     dụng (cổng quyền agent_group), xóa là thu hồi mọi kết nối của nó.
  4. Bảng không phình: mã cấp quyền hết hạn quá 1 ngày bị xóa; ứng dụng 7 ngày không có kết nối sống bị xóa (ứng dụng còn
     kết nối sống thì giữ dù lâu không đăng nhập lại); trần đăng ký 5 / phút / IP + trần ngày toàn hệ.
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.modules.agent_hub import mcp_keys, mcp_log, oauth
from app.modules.agent_hub.model import AgentMcpKey, AgentOAuthClient, AgentOAuthCode
from app.modules.user.model import User

BASE = "https://deverp.degoholding.vn"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_ERP_URL", BASE)
    monkeypatch.setattr(mcp_log, "_redis", lambda: (_ for _ in ()).throw(ConnectionError("không Redis")))
    monkeypatch.setattr(mcp_log, "_mem", {})


def _reg(db, uri="https://chatgpt.com/cb", name="ChatGPT"):
    return oauth.client_by_id(db, oauth.register(db, {"client_name": name, "redirect_uris": [uri]}, "1.2.3.4")["client_id"])


# ── 3. Nơi quay về theo hostname ──────────────────────────────────────────────

@pytest.mark.parametrize("uri,label,trusted", [
    ("https://chatgpt.com/connector_platform_oauth_redirect", "chatgpt.com", True),
    ("https://claude.ai/api/mcp/auth_callback", "claude.ai", True),
    ("https://auth.openai.com/cb", "auth.openai.com", True),
    ("https://chatgpt.com.evil.example/cb", "chatgpt.com.evil.example", False),     # đuôi giả
    ("https://evilchatgpt.com/cb", "evilchatgpt.com", False),                       # không phải tên miền con
    ("https://chatgpt.com@evil.example/cb", "evil.example", False),                 # userinfo giả tên miền
    ("https://CHATGPT.COM:8443/cb", "chatgpt.com", True),                           # hoa / cổng
    ("http://127.0.0.1:33418/callback", "máy tính của bạn (127.0.0.1)", True),
    ("cursor://anysphere.cursor-retrieval/oauth", "ứng dụng cài trên máy (cursor://)", False),
])
def test_noi_quay_ve_tinh_theo_hostname(uri, label, trusted):
    assert oauth.redirect_target(uri) == (label, trusted)


def test_dang_ky_redirect_co_userinfo_hoac_cong_hong_bi_tu_choi(db):
    for uri in ("https://chatgpt.com@evil.example/cb", "https://user:pw@claude.ai/cb", "https://chatgpt.com:99999/cb"):
        with pytest.raises(oauth.OAuthError) as e:
            oauth.register(db, {"redirect_uris": [uri]}, "")
        assert e.value.error == "invalid_redirect_uri", uri


def test_man_dong_y_tra_host_va_co_tin_cay(db):
    client = _reg(db, "https://evil.example/cb", "ChatGPT")
    _v, challenge = "x" * 43, "y" * 43
    kind, req = oauth.begin_authorize(db, {"response_type": "code", "client_id": client.client_id,
                                           "redirect_uri": "https://evil.example/cb", "code_challenge": challenge,
                                           "code_challenge_method": "S256"}, BASE)
    assert kind == "consent"
    info = oauth.describe_request(db, req)
    assert (info["client_name"], info["redirect_host"], info["redirect_trusted"]) == ("ChatGPT", "evil.example", False)


@pytest.fixture
def admin_client(db, seed):
    from app.core import auth

    user = db.get(User, seed.u_req_id)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    yield TestClient(app), user, auth
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def test_man_quan_tri_ung_dung_gac_quyen_va_xoa_la_thu_hoi(db, admin_client, monkeypatch):
    client, user, auth = admin_client
    app_row = _reg(db)
    grant, raw = mcp_keys.create(db, user.id, name="Qua ChatGPT")
    grant.kind, grant.oauth_client_id, grant.refresh_hash = mcp_keys.KIND_OAUTH, app_row.id, "h" * 64
    db.add(AgentOAuthCode(code_hash="c" * 64, client_pk=app_row.id, user_id=user.id, redirect_uri="https://chatgpt.com/cb",
                          code_challenge="z", expires_at=datetime.now() + timedelta(minutes=5)))
    db.commit()
    #  Không quyền agent_group → 403 cả xem lẫn xóa.
    monkeypatch.setattr(auth, "user_has_permission", lambda db, u, e, a: False)
    assert client.get("/api/agent-hub/oauth-clients").status_code == 403
    assert client.delete(f"/api/agent-hub/oauth-clients/{app_row.id}").status_code == 403
    monkeypatch.setattr(auth, "user_has_permission", lambda db, u, e, a: True)
    items = client.get("/api/agent-hub/oauth-clients").json()["data"]["items"]
    mine = next(i for i in items if i["id"] == app_row.id)
    assert mine["redirect_hosts"] == ["chatgpt.com"] and mine["trusted"] and mine["live_grants"] == 1
    res = client.delete(f"/api/agent-hub/oauth-clients/{app_row.id}")
    assert res.status_code == 200 and res.json()["data"]["revoked_grants"] == 1
    db.refresh(grant)
    assert grant.revoked_at is not None and grant.refresh_hash == ""
    assert db.get(AgentOAuthClient, app_row.id) is None and db.query(AgentOAuthCode).count() == 0
    assert client.delete(f"/api/agent-hub/oauth-clients/{app_row.id}").status_code == 404


# ── 4. Dọn bảng + trần đăng ký ───────────────────────────────────────────────

def test_don_ma_het_han_va_ung_dung_bo_khong(db, seed):
    now = datetime(2026, 11, 1, 3, 0)
    old = now - timedelta(days=oauth.UNUSED_CLIENT_DAYS + 1)
    unused = _reg(db, name="bỏ không")
    kept_live = _reg(db, name="còn kết nối")
    fresh = _reg(db, name="mới đăng ký")
    for c in (unused, kept_live):
        c.created_at = old
    fresh.created_at = now - timedelta(days=1)
    db.commit()
    grant, _ = mcp_keys.create(db, seed.u_req_id, name="Qua app")
    grant.kind, grant.oauth_client_id, grant.expires_at = mcp_keys.KIND_OAUTH, kept_live.id, now + timedelta(days=30)
    db.add_all([AgentOAuthCode(code_hash="a" * 64, client_pk=fresh.id, user_id=1, redirect_uri="x", code_challenge="z",
                               expires_at=now - timedelta(days=2)),
                AgentOAuthCode(code_hash="b" * 64, client_pk=fresh.id, user_id=1, redirect_uri="x", code_challenge="z",
                               expires_at=now - timedelta(hours=1))])
    db.commit()
    out = oauth.purge(db, now)
    assert out == {"oauth_codes_deleted": 1, "oauth_clients_deleted": 1}
    assert db.get(AgentOAuthClient, unused.id) is None
    assert db.get(AgentOAuthClient, kept_live.id) is not None and db.get(AgentOAuthClient, fresh.id) is not None
    assert oauth.purge(db, now) == {"oauth_codes_deleted": 0, "oauth_clients_deleted": 0}      # chạy lại không xóa thêm


def test_tran_dang_ky_moi_ip_va_toan_he(db, monkeypatch):
    app.dependency_overrides[get_db] = lambda: db
    try:
        client = TestClient(app)
        body = {"client_name": "x", "redirect_uris": ["https://chatgpt.com/cb"]}
        codes = [client.post("/api/oauth/register", json=body).status_code for _ in range(7)]
        assert codes[:5] == [201] * 5 and codes[5:] == [429, 429]
    finally:
        app.dependency_overrides.pop(get_db, None)
    monkeypatch.setattr(oauth, "REGISTER_PER_DAY", 6)
    _reg(db)                                     # 5 + 1 = 6 trong 24 giờ → cái thứ 7 bị chặn dù khác IP
    with pytest.raises(oauth.OAuthError) as e:
        _reg(db)
    assert e.value.status == 429
