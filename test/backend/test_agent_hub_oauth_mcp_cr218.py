"""ai-CR-218 — OAuth cho cổng MCP (K14, doc/erp/21 §7.2): ChatGPT / claude.ai tự đăng ký → người dùng đăng nhập ERP bấm
Cho phép → đổi mã lấy token (PKCE S256) → gọi /api/mcp.

Canh (đủ nhánh Agent 1 đặt):
  - tài liệu mô tả (.well-known) đúng đường; 401 của /api/mcp có `WWW-Authenticate: Bearer resource_metadata="…"`;
  - đi trọn luồng: đăng ký → authorize chuyển sang màn đồng ý → Cho phép → token → tools/list được, nhật ký ghi tên ứng dụng
    lúc đăng ký; kết nối hiện ở Khóa của tôi là «Kết nối OAuth», không ăn vào trần 5 khóa dán tay;
  - PKCE sai bị chặn; thiếu PKCE / không phải S256 trả lỗi về ứng dụng; mã cấp quyền dùng một lần;
  - ứng dụng chưa đăng ký / redirect_uri lạ bị từ chối và KHÔNG chuyển hướng;
  - mã truy cập hết hạn → 401 có header; làm mới xoay vòng (mã làm mới cũ chết);
  - thu hồi (RFC 7009 lẫn gỡ ở Khóa của tôi) chặn ngay; cấp lại cho cùng ứng dụng thì kết nối cũ chết;
  - ứng dụng có bí mật: sai bí mật bị chặn.
"""
import base64
import hashlib
import json
import secrets
from datetime import datetime, timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.modules.agent_hub import mcp_keys, mcp_log, oauth
from app.modules.agent_hub.model import AgentMcpCall, AgentMcpKey
from app.modules.user.model import User

BASE = "https://deverp.degoholding.vn"
REDIRECT = "https://chatgpt.com/connector_platform_oauth_redirect"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_ERP_URL", BASE)
    monkeypatch.setattr(mcp_log, "_redis", lambda: (_ for _ in ()).throw(ConnectionError("không Redis")))
    monkeypatch.setattr(mcp_log, "_mem", {})


@pytest.fixture
def owner(db, seed):
    return db.get(User, seed.u_req_id)


@pytest.fixture
def client(db, owner):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: owner
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _pkce():
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    return verifier, challenge


def _register(client, **extra):
    res = client.post("/api/oauth/register", json={"client_name": "ChatGPT", "redirect_uris": [REDIRECT], **extra})
    assert res.status_code == 201, res.text
    return res.json()


def _authorize(client, client_id, challenge, **extra):
    params = {"response_type": "code", "client_id": client_id, "redirect_uri": REDIRECT, "state": "st-1",
              "code_challenge": challenge, "code_challenge_method": "S256", "resource": f"{BASE}/api/mcp", **extra}
    return client.get("/api/oauth/authorize", params=params, follow_redirects=False)


def _consent(client, res, scope=0):
    loc = res.headers["location"]
    assert loc.startswith(f"{BASE}/oauth/consent/")
    req = loc.rsplit("/", 1)[1]
    info = client.get(f"/api/agent-hub/oauth/request/{req}").json()["data"]
    assert info["client_name"] == "ChatGPT" and info["redirect_host"] == "chatgpt.com"
    to = client.post("/api/agent-hub/oauth/approve", json={"req": req, "scope": scope}).json()["data"]["redirect_to"]
    q = parse_qs(urlsplit(to).query)
    assert to.startswith(REDIRECT) and q["state"] == ["st-1"] and q["iss"] == [BASE]
    return q["code"][0]


def _token(client, **form):
    return client.post("/api/oauth/token", data=form)


def _full_flow(client, scope=0):
    reg = _register(client)
    verifier, challenge = _pkce()
    code = _consent(client, _authorize(client, reg["client_id"], challenge), scope)
    res = _token(client, grant_type="authorization_code", code=code, redirect_uri=REDIRECT, client_id=reg["client_id"],
                 code_verifier=verifier, resource=f"{BASE}/api/mcp")
    assert res.status_code == 200, res.text
    return reg, res.json()


def _mcp(client, token, method="tools/list"):
    return client.post("/api/mcp", content=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method}),
                       headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})


# ── Tài liệu mô tả + 401 ──────────────────────────────────────────────────────

def test_tai_lieu_mo_ta_va_401_chi_duong_oauth(client):
    pr = client.get("/.well-known/oauth-protected-resource").json()
    assert pr["resource"] == f"{BASE}/api/mcp" and pr["authorization_servers"] == [BASE]
    assert client.get("/.well-known/oauth-protected-resource/api/mcp").json() == pr     # dạng gắn đường (RFC 9728 §3)
    asm = client.get("/.well-known/oauth-authorization-server").json()
    assert asm["issuer"] == BASE and asm["code_challenge_methods_supported"] == ["S256"]
    assert asm["registration_endpoint"] == f"{BASE}/api/oauth/register" and "refresh_token" in asm["grant_types_supported"]
    res = client.post("/api/mcp", content=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}),
                      headers={"Content-Type": "application/json"})
    assert res.status_code == 401
    assert res.headers["www-authenticate"] == f'Bearer resource_metadata="{BASE}/.well-known/oauth-protected-resource"'
    bad = _mcp(client, "dego_mcp_sai")
    assert 'error="invalid_token"' in bad.headers["www-authenticate"]


# ── Trọn luồng ────────────────────────────────────────────────────────────────

def test_tron_luong_dang_ky_cho_phep_token_goi_mcp(db, owner, client):
    reg, tok = _full_flow(client, scope=mcp_keys.SCOPE_READ)
    assert tok["token_type"] == "Bearer" and tok["expires_in"] == oauth.ACCESS_TTL_SEC and tok["scope"] == "mcp:read"
    assert tok["refresh_token"].startswith(oauth.REFRESH_PREFIX)
    res = _mcp(client, tok["access_token"])
    assert res.status_code == 200 and "tools" in res.json()["result"]
    log = db.query(AgentMcpCall).order_by(AgentMcpCall.id.desc()).first()
    assert log.client_name == "ChatGPT" and log.user_id == owner.id
    row = db.get(AgentMcpKey, log.key_id)
    assert (row.kind, row.scope, row.name) == (mcp_keys.KIND_OAUTH, mcp_keys.SCOPE_READ, "Qua ChatGPT")
    listed = client.get("/api/agent-hub/mcp-keys").json()["data"]["items"]
    assert [(k["kind_label"], k["state_label"]) for k in listed] == [("Kết nối OAuth", "Đang dùng")]
    #  Kết nối OAuth không ăn vào trần 5 khóa dán tay.
    for i in range(mcp_keys.MAX_KEYS):
        mcp_keys.create(db, owner.id, name=f"tay {i}")


def test_muc_duoc_ghi_va_cap_lai_thi_ket_noi_cu_chet(db, client):
    reg, first = _full_flow(client, scope=mcp_keys.SCOPE_WRITE)
    assert first["scope"] == "mcp:read mcp:write"
    verifier, challenge = _pkce()
    code = _consent(client, _authorize(client, reg["client_id"], challenge))
    second = _token(client, grant_type="authorization_code", code=code, redirect_uri=REDIRECT,
                    client_id=reg["client_id"], code_verifier=verifier).json()
    assert _mcp(client, first["access_token"]).status_code == 401                     # kết nối cũ đã bị thay
    assert _mcp(client, second["access_token"]).status_code == 200
    assert db.query(AgentMcpKey).filter(AgentMcpKey.revoked_at.is_(None), AgentMcpKey.kind == 2).count() == 1


# ── PKCE, mã một lần, ứng dụng lạ ─────────────────────────────────────────────

def test_pkce_sai_bi_chan_va_ma_chi_dung_mot_lan(client):
    reg = _register(client)
    verifier, challenge = _pkce()
    code = _consent(client, _authorize(client, reg["client_id"], challenge))
    bad = _token(client, grant_type="authorization_code", code=code, redirect_uri=REDIRECT, client_id=reg["client_id"],
                 code_verifier=secrets.token_urlsafe(48))
    assert bad.status_code == 400 and bad.json()["error"] == "invalid_grant" and "PKCE" in bad.json()["error_description"]
    #  ai-CR-222: lần hỏng cũng ĐỐT mã (RFC 6749 §4.1.2) — mã bị lộ thì kẻ đoán PKCE không có lần thử thứ hai.
    burned = _token(client, grant_type="authorization_code", code=code, redirect_uri=REDIRECT, client_id=reg["client_id"],
                    code_verifier=verifier)
    assert burned.status_code == 400 and "đã dùng" in burned.json()["error_description"]
    verifier, challenge = _pkce()
    code = _consent(client, _authorize(client, reg["client_id"], challenge))
    ok = _token(client, grant_type="authorization_code", code=code, redirect_uri=REDIRECT, client_id=reg["client_id"],
                code_verifier=verifier)
    assert ok.status_code == 200
    again = _token(client, grant_type="authorization_code", code=code, redirect_uri=REDIRECT,
                   client_id=reg["client_id"], code_verifier=verifier)
    assert again.status_code == 400 and "đã dùng" in again.json()["error_description"]


def test_thieu_pkce_hoac_khong_s256_tra_loi_ve_ung_dung(client):
    reg = _register(client)
    for extra in ({"code_challenge": ""}, {"code_challenge_method": "plain"}):
        res = _authorize(client, reg["client_id"], _pkce()[1], **extra)
        q = parse_qs(urlsplit(res.headers["location"]).query)
        assert res.status_code == 302 and res.headers["location"].startswith(REDIRECT)
        assert q["error"] == ["invalid_request"] and q["state"] == ["st-1"]


def test_ung_dung_la_va_redirect_la_khong_chuyen_huong(client):
    res = _authorize(client, "dego_oc_khong_co", _pkce()[1])
    assert res.status_code == 400 and "location" not in res.headers and "chưa đăng ký" in res.text
    reg = _register(client)
    res = _authorize(client, reg["client_id"], _pkce()[1], redirect_uri="https://ke-gian.example/cb")
    assert res.status_code == 400 and "location" not in res.headers
    tok = _token(client, grant_type="authorization_code", code="x", client_id="dego_oc_khong_co", code_verifier="y" * 43)
    assert tok.status_code == 401 and tok.json()["error"] == "invalid_client"


def test_dang_ky_tu_choi_redirect_nguy_hiem(client):
    for uris in (["http://ke-gian.example/cb"], ["javascript:alert(1)"], ["https://a.vn/cb#frag"], [], ["x"] * 11):
        res = client.post("/api/oauth/register", json={"client_name": "X", "redirect_uris": uris})
        assert res.status_code == 400, uris
    mcp_log._mem.clear()        # ai-CR-225: trần đăng ký 5 lượt / phút / IP — năm lượt hỏng ở trên đã ăn hết phút này
    ok = client.post("/api/oauth/register", json={"redirect_uris": ["http://127.0.0.1:33418/cb", "cursor://anysphere/cb"]})
    assert ok.status_code == 201 and ok.json()["token_endpoint_auth_method"] == "none" and "client_secret" not in ok.json()


# ── Hết hạn, làm mới, thu hồi ─────────────────────────────────────────────────

def test_ma_truy_cap_het_han_401_va_lam_moi_xoay_vong(db, client):
    reg, tok = _full_flow(client)
    row = db.query(AgentMcpKey).filter(AgentMcpKey.kind == 2).one()
    row.access_expires_at = datetime.now() - timedelta(seconds=1)
    db.commit()
    res = _mcp(client, tok["access_token"])
    assert res.status_code == 401 and 'error="invalid_token"' in res.headers["www-authenticate"]
    assert db.query(AgentMcpCall).order_by(AgentMcpCall.id.desc()).first().deny_reason == mcp_log.REASON_OAUTH_EXPIRED
    new = _token(client, grant_type="refresh_token", refresh_token=tok["refresh_token"], client_id=reg["client_id"])
    assert new.status_code == 200 and new.json()["refresh_token"] != tok["refresh_token"]
    assert _mcp(client, new.json()["access_token"]).status_code == 200
    old = _token(client, grant_type="refresh_token", refresh_token=tok["refresh_token"], client_id=reg["client_id"])
    assert old.status_code == 400 and old.json()["error"] == "invalid_grant"            # mã làm mới cũ đã chết


def test_thu_hoi_chan_ngay_ca_hai_duong(db, owner, client):
    reg, tok = _full_flow(client)
    assert client.post("/api/oauth/revoke", data={"token": tok["refresh_token"], "client_id": reg["client_id"]}).status_code == 200
    assert _mcp(client, tok["access_token"]).status_code == 401
    assert _token(client, grant_type="refresh_token", refresh_token=tok["refresh_token"],
                  client_id=reg["client_id"]).status_code == 400
    #  Gỡ ở Khóa của tôi cũng cắt ngay.
    reg2, tok2 = _full_flow(client)
    row = db.query(AgentMcpKey).filter(AgentMcpKey.kind == 2, AgentMcpKey.revoked_at.is_(None)).one()
    assert client.delete(f"/api/agent-hub/mcp-keys/{row.id}").status_code == 200
    assert _mcp(client, tok2["access_token"]).status_code == 401


def test_tu_choi_va_ung_dung_co_bi_mat(client):
    reg = _register(client, token_endpoint_auth_method="client_secret_post")
    assert reg["client_secret"]
    verifier, challenge = _pkce()
    loc = _authorize(client, reg["client_id"], challenge).headers["location"]
    req = loc.rsplit("/", 1)[1]
    denied = client.post("/api/agent-hub/oauth/deny", json={"req": req}).json()["data"]["redirect_to"]
    assert parse_qs(urlsplit(denied).query)["error"] == ["access_denied"]
    code = _consent(client, _authorize(client, reg["client_id"], challenge))
    bad = _token(client, grant_type="authorization_code", code=code, redirect_uri=REDIRECT, client_id=reg["client_id"],
                 client_secret="sai", code_verifier=verifier)
    assert bad.status_code == 401 and bad.json()["error"] == "invalid_client"
    basic = base64.b64encode(f"{reg['client_id']}:{reg['client_secret']}".encode()).decode()
    ok = client.post("/api/oauth/token", data={"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT,
                                               "code_verifier": verifier}, headers={"Authorization": f"Basic {basic}"})
    assert ok.status_code == 200


def test_yeu_cau_ky_sai_hoac_het_han(client):
    assert oauth.read_request("rac") is None
    tok = oauth.sign_request({"c": "x"}, now=1000)
    assert oauth.read_request(tok, now=1000 + oauth.REQUEST_TTL_SEC + 1) is None
    payload, sig = tok.rsplit(".", 1)
    assert oauth.read_request(payload + "." + "0" * len(sig), now=1000) is None
    assert client.get(f"/api/agent-hub/oauth/request/{tok}").status_code == 400
