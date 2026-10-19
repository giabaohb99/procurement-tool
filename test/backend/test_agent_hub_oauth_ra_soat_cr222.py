"""ai-CR-222 — vá theo bài rà độc lập của Agent 1 (19/10/2026) trên OAuth cổng MCP (ai-CR-218) + khóa (ai-CR-221).

Canh:
  - chống nhúng (clickjacking): nginx erp đặt header chống nhúng cho cả site, màn đồng ý cấm nhúng hẳn;
  - issuer CHỈ lấy AGENT_ERP_URL: X-Forwarded-Host người gọi tự đặt không đổi được issuer; chưa khai thì 503 (trừ máy
    local) và 401 của /api/mcp không chỉ đường OAuth về gốc nội bộ;
  - mã cấp quyền bị ĐỐT ngay lần đổi đầu, kể cả lần hỏng (sai PKCE) — không thử lại được, không đua hai yêu cầu;
  - chuỗi ký yêu cầu có `exp` lạ → coi như hỏng, không 500;
  - các ca thiếu bài kiểm Agent 1 nêu: làm mới / thu hồi bằng mã của ứng dụng KHÁC; đổi mã với redirect_uri khác;
    resource lạ → invalid_target.
"""
import base64
import hashlib
import json
import secrets
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.modules.agent_hub import mcp_keys, mcp_log, oauth
from app.modules.agent_hub.model import AgentMcpKey
from app.modules.user.model import User

BASE = "https://deverp.degoholding.vn"
REDIRECT = "https://chatgpt.com/connector_platform_oauth_redirect"
NGINX = Path(__file__).resolve().parents[2] / "docker" / "nginx.erp.prod.conf"


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
    return verifier, base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")


def _register(client, name="ChatGPT", redirect=REDIRECT):
    res = client.post("/api/oauth/register", json={"client_name": name, "redirect_uris": [redirect]})
    assert res.status_code == 201, res.text
    return res.json()


def _code(client, reg, challenge, redirect=REDIRECT):
    res = client.get("/api/oauth/authorize", follow_redirects=False, params={
        "response_type": "code", "client_id": reg["client_id"], "redirect_uri": redirect, "state": "s",
        "code_challenge": challenge, "code_challenge_method": "S256", "resource": f"{BASE}/api/mcp"})
    req = res.headers["location"].rsplit("/", 1)[1]
    to = client.post("/api/agent-hub/oauth/approve", json={"req": req, "scope": 0}).json()["data"]["redirect_to"]
    return parse_qs(urlsplit(to).query)["code"][0]


def _exchange(client, reg, code, verifier, redirect=REDIRECT, resource=f"{BASE}/api/mcp"):
    return client.post("/api/oauth/token", data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect,
                                                  "client_id": reg["client_id"], "code_verifier": verifier,
                                                  "resource": resource})


def _connect(client, name="ChatGPT"):
    reg = _register(client, name)
    verifier, challenge = _pkce()
    res = _exchange(client, reg, _code(client, reg, challenge), verifier)
    assert res.status_code == 200, res.text
    return reg, res.json()


# ── 1. Chống nhúng ────────────────────────────────────────────────────────────

def test_nginx_erp_chong_nhung_ca_site_va_cam_han_man_dong_y():
    #  Container api chỉ gắn backend/ + test/ — thiếu docker/ thì bỏ qua (đã thử thật bằng nginx:alpine + curl 19/10).
    if not NGINX.is_file():
        pytest.skip("không thấy docker/nginx.erp.prod.conf trong môi trường chạy bài kiểm")
    import re

    conf = NGINX.read_text(encoding="utf-8")
    lines = [ln.split("#", 1)[0] for ln in conf.splitlines()]          # bỏ chú thích (chú thích cũng có chữ location)
    first_loc = next(i for i, ln in enumerate(lines) if re.match(r"\s*location\s", ln))
    server_level = "\n".join(lines[:first_loc])
    assert 'add_header X-Frame-Options "SAMEORIGIN" always;' in server_level
    assert "add_header Content-Security-Policy \"frame-ancestors 'self'\" always;" in server_level
    blocks: dict[str, str] = {}
    current = None
    for ln in lines[first_loc:]:
        m = re.match(r"\s*location\s+(.*?)\s*\{", ln)
        if m:
            current = m.group(1)
            blocks[current] = ""
        elif current is not None:
            blocks[current] += ln + "\n"
    consent = blocks["^~ /oauth/consent/"]
    assert 'X-Frame-Options "DENY" always' in consent and "frame-ancestors 'none'" in consent
    assert "try_files /index.html" in consent
    #  nginx BỎ kế thừa add_header khi location tự đặt add_header — location nào có add_header thì phải tự mang chống nhúng.
    for name, body in blocks.items():
        if "add_header" in body:
            assert "X-Frame-Options" in body and "frame-ancestors" in body, name


# ── 2. Issuer chỉ lấy AGENT_ERP_URL ──────────────────────────────────────────

def test_x_forwarded_host_khong_doi_duoc_issuer(client):
    evil = {"X-Forwarded-Host": "evil.example", "X-Forwarded-Proto": "http"}
    asm = client.get("/.well-known/oauth-authorization-server", headers=evil).json()
    assert asm["issuer"] == BASE and "evil" not in json.dumps(asm)
    reg = _register(client)
    _v, challenge = _pkce()
    res = client.get("/api/oauth/authorize", headers=evil, follow_redirects=False, params={
        "response_type": "code", "client_id": reg["client_id"], "redirect_uri": REDIRECT,
        "code_challenge": challenge, "code_challenge_method": "S256"})
    assert res.headers["location"].startswith(f"{BASE}/oauth/consent/")
    bad = client.post("/api/mcp", content="{}", headers={**evil, "Content-Type": "application/json"})
    assert "evil" not in bad.headers["www-authenticate"]


def test_chua_khai_agent_erp_url_thi_503_tru_may_local(client, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_ERP_URL", "")
    res = client.get("/.well-known/oauth-protected-resource", headers={"X-Forwarded-Host": "erp.degoholding.vn"})
    assert res.status_code == 503 and "AGENT_ERP_URL" in res.text
    #  401 của cổng: không trỏ resource_metadata về địa chỉ đến (ở chế độ tách là gốc nội bộ agent:8001).
    unauth = client.post("/api/mcp", content="{}", headers={"Content-Type": "application/json"})
    assert unauth.status_code == 401 and unauth.headers["www-authenticate"] == "Bearer"
    local = TestClient(app, base_url="http://localhost:8000")
    assert local.get("/.well-known/oauth-protected-resource").json()["resource"] == "http://localhost:8000/api/mcp"
    assert oauth.issuer("http", "127.0.0.1:5174") == "http://127.0.0.1:5174"
    for host in ("agent:8001", "localhost.evil.example", "127.0.0.1.nip.io", "", "[::1"):
        with pytest.raises(oauth.OAuthError):
            oauth.issuer("http", host)


# ── 6, 8. Mã một lần + chuỗi ký hỏng ─────────────────────────────────────────

def test_ma_cap_quyen_dot_ngay_ca_khi_lan_dau_sai_pkce(client):
    reg = _register(client)
    verifier, challenge = _pkce()
    code = _code(client, reg, challenge)
    assert _exchange(client, reg, code, "sai-" + verifier).json()["error"] == "invalid_grant"
    again = _exchange(client, reg, code, verifier)
    assert again.status_code == 400 and "đã dùng" in again.json()["error_description"]


def test_chuoi_ky_exp_la_thi_hong_khong_500():
    for exp in ("abc", [1], {"x": 1}, 1.5e30):
        payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).decode().rstrip("=")
        token = f"{payload}.{oauth._sign(payload)}"
        assert oauth.read_request(token) is None or exp == 1.5e30
    assert oauth.read_request("khong-co-dau-cham") is None


# ── Ca thiếu bài kiểm ────────────────────────────────────────────────────────

def test_lam_moi_va_thu_hoi_bang_ma_cua_ung_dung_khac_bi_chan(db, client):
    reg_a, tok_a = _connect(client, "ChatGPT")
    reg_b = _register(client, "Ứng dụng khác", "https://evil.example/cb")
    res = client.post("/api/oauth/token", data={"grant_type": "refresh_token", "refresh_token": tok_a["refresh_token"],
                                                 "client_id": reg_b["client_id"]})
    assert res.status_code == 400 and res.json()["error"] == "invalid_grant"
    client.post("/api/oauth/revoke", data={"token": tok_a["access_token"], "client_id": reg_b["client_id"]})
    row = db.query(AgentMcpKey).filter(AgentMcpKey.kind == mcp_keys.KIND_OAUTH).one()
    assert row.revoked_at is None                                       # ứng dụng B không thu hồi được kết nối của A
    ok = client.post("/api/oauth/token", data={"grant_type": "refresh_token", "refresh_token": tok_a["refresh_token"],
                                                "client_id": reg_a["client_id"]})
    assert ok.status_code == 200


def test_doi_ma_voi_redirect_khac_hoac_resource_la_bi_chan(client):
    reg = _register(client)
    verifier, challenge = _pkce()
    res = _exchange(client, reg, _code(client, reg, challenge), verifier, redirect="https://chatgpt.com/khac")
    assert res.json()["error"] == "invalid_grant"
    verifier, challenge = _pkce()
    res = _exchange(client, reg, _code(client, reg, challenge), verifier, resource="https://evil.example/api/mcp")
    assert res.json()["error"] == "invalid_target"


# ── 5. Nghỉ việc xóa trắng bí mật của khóa ───────────────────────────────────

def test_nghi_viec_xoa_trang_ban_xem_lai_niem_phong_va_ma_lam_moi(db, owner, seed):
    from app.modules.agent_hub import service

    manual, _raw = mcp_keys.create(db, owner.id, name="tay")
    issued = mcp_keys.issue(db, owner.id, seed.u_nstm_id, days=30)
    oa, _ = mcp_keys.create(db, owner.id, name="Qua ChatGPT")
    oa.kind, oa.refresh_hash, oa.raw_view = mcp_keys.KIND_OAUTH, "h" * 64, ""
    db.commit()
    assert manual.raw_view and issued.raw_sealed
    service.revoke_user_access(db, owner.id)
    db.commit()
    for row in (manual, issued, oa):
        db.refresh(row)
        assert row.revoked_at is not None and not row.raw_view and not row.raw_sealed and not row.refresh_hash
