"""ai-CR-221 — chủ khóa XEM LẠI khóa MCP + BẬT / TẮT tạm (đại ca chốt 19/10/2026 qua Agent 1).

Canh (đủ nhánh Agent 1 đặt + chỗ dễ lủng):
  - chỉ CHỦ KHÓA xem lại được: khóa người khác → 404 y như khóa không tồn tại; danh sách / tạo / admin KHÔNG lộ khóa thô;
  - mỗi lần xem ghi một dòng nhật ký cổng MCP (`key/reveal`); câu trả có `Cache-Control: no-store`;
  - khóa cũ (trước ai-CR-221, không có `raw_view`), kết nối OAuth, khóa chờ nhận, hết hạn → 409 kèm câu, không lộ gì;
  - khóa phát hộ: nhận xong xem lại được; thu hồi xong bản xem lại bị xóa trắng;
  - tắt → /api/mcp 401 và nhật ký ghi «Khóa đang tắt»; bật lại chạy ngay; tắt vẫn tính trần 5 khóa;
  - tắt kết nối OAuth: mã truy cập bị chặn và KHÔNG làm mới được (khỏi vòng 401 → làm mới → 401);
  - bấm tắt hai lần chỉ ghi một dòng nhật ký.
"""
import json
from datetime import datetime, timedelta

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


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_ERP_URL", BASE)
    monkeypatch.setattr(mcp_log, "_redis", lambda: (_ for _ in ()).throw(ConnectionError("không Redis")))
    monkeypatch.setattr(mcp_log, "_mem", {})


@pytest.fixture
def owner(db, seed):
    return db.get(User, seed.u_req_id)


@pytest.fixture
def other(db, seed):
    return db.get(User, seed.u_nstm_id)


@pytest.fixture
def as_user(db):
    holder = {}
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: holder["user"]

    def login(user):
        holder["user"] = user
        return TestClient(app)

    yield login
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _mcp(client, token):
    return client.post("/api/mcp", content=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}),
                       headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})


def _logs(db, key_id, method):
    return db.query(AgentMcpCall).filter(AgentMcpCall.key_id == key_id, AgentMcpCall.method == method).count()


# ── Xem lại ───────────────────────────────────────────────────────────────────

def test_chu_khoa_xem_lai_dung_khoa_va_ghi_nhat_ky(db, owner, as_user):
    client = as_user(owner)
    made = client.post("/api/agent-hub/mcp-keys", json={"name": "Claude", "scope": 0}).json()["data"]
    assert made["revealable"] is True and made["enabled"] is True
    #  Danh sách không bao giờ mang khóa thô (kể cả trong trường khác).
    listed = client.get("/api/agent-hub/mcp-keys").json()["data"]["items"]
    assert made["key"] not in json.dumps(listed) and "key" not in listed[0]
    res = client.get(f"/api/agent-hub/mcp-keys/{made['id']}/reveal")
    assert res.status_code == 200 and res.json()["data"]["key"] == made["key"]
    assert res.headers["cache-control"] == "no-store"
    client.get(f"/api/agent-hub/mcp-keys/{made['id']}/reveal")
    assert _logs(db, made["id"], mcp_log.METHOD_KEY_REVEAL) == 2
    row = db.query(AgentMcpCall).filter(AgentMcpCall.method == mcp_log.METHOD_KEY_REVEAL).first()
    assert row.user_id == owner.id and row.client_name == mcp_log.KEY_ACTION_CLIENT
    #  Bản lưu trong DB là bản mã hóa, không phải khóa thô.
    assert made["key"] not in (db.get(AgentMcpKey, made["id"]).raw_view or "")


def test_nguoi_khac_xem_khoa_cua_minh_ra_404_khong_ghi_nhat_ky(db, owner, other, as_user):
    row, _raw = mcp_keys.create(db, owner.id, name="của owner")
    res = as_user(other).get(f"/api/agent-hub/mcp-keys/{row.id}/reveal")
    assert res.status_code == 404
    assert as_user(other).get("/api/agent-hub/mcp-keys/999999/reveal").json() == res.json()   # không dò được id
    assert as_user(other).patch(f"/api/agent-hub/mcp-keys/{row.id}", json={"enabled": False}).status_code == 404
    assert db.get(AgentMcpKey, row.id).disabled_at is None
    assert _logs(db, row.id, mcp_log.METHOD_KEY_REVEAL) == 0


def test_khoa_cu_oauth_het_han_thu_hoi_khong_xem_duoc(db, owner, as_user):
    client = as_user(owner)
    old, _ = mcp_keys.create(db, owner.id, name="cũ")
    old.raw_view = None                      # khóa tạo trước ai-CR-221
    oa, _ = mcp_keys.create(db, owner.id, name="Qua ChatGPT")
    oa.kind, oa.raw_view, oa.access_expires_at = mcp_keys.KIND_OAUTH, "", datetime.now() + timedelta(hours=1)
    exp, _ = mcp_keys.create(db, owner.id, name="hết hạn")
    exp.expires_at = datetime.now() - timedelta(minutes=1)
    db.commit()
    for row, word in ((old, "tạo khóa mới"), (oa, "OAuth"), (exp, "hết hạn")):
        res = client.get(f"/api/agent-hub/mcp-keys/{row.id}/reveal")
        assert res.status_code == 409 and word in res.text, (row.name, res.text)
        assert "dego_mcp_" not in res.text
    serial = {k["id"]: k for k in client.get("/api/agent-hub/mcp-keys").json()["data"]["items"]}
    assert not serial[old.id]["revealable"] and not serial[oa.id]["revealable"] and not serial[exp.id]["revealable"]
    #  Thu hồi xong: bản xem lại bị xóa trắng, xem lại → 404.
    live, _ = mcp_keys.create(db, owner.id, name="sẽ gỡ")
    assert client.delete(f"/api/agent-hub/mcp-keys/{live.id}").status_code == 200
    assert db.get(AgentMcpKey, live.id).raw_view == ""
    assert client.get(f"/api/agent-hub/mcp-keys/{live.id}/reveal").status_code == 404


def test_khoa_phat_ho_chua_nhan_khong_xem_nhan_xong_xem_lai_duoc(db, owner, other, as_user):
    row = mcp_keys.issue(db, owner.id, other.id, days=30)
    db.commit()
    client = as_user(owner)
    assert client.get(f"/api/agent-hub/mcp-keys/{row.id}/reveal").status_code == 409
    assert client.patch(f"/api/agent-hub/mcp-keys/{row.id}", json={"enabled": False}).status_code == 409
    raw = client.post(f"/api/agent-hub/mcp-keys/{row.id}/claim").json()["data"]["key"]
    assert client.get(f"/api/agent-hub/mcp-keys/{row.id}/reveal").json()["data"]["key"] == raw
    assert db.get(AgentMcpKey, row.id).raw_sealed == ""
    #  Người PHÁT (quản trị) không xem được khóa của người nhận.
    assert as_user(other).get(f"/api/agent-hub/mcp-keys/{row.id}/reveal").status_code == 404


# ── Bật / tắt ─────────────────────────────────────────────────────────────────

def test_tat_thi_cong_401_ghi_ly_do_bat_lai_chay(db, owner, as_user):
    client = as_user(owner)
    row, raw = mcp_keys.create(db, owner.id, name="Claude")
    assert _mcp(client, raw).status_code == 200
    res = client.patch(f"/api/agent-hub/mcp-keys/{row.id}", json={"enabled": False})
    assert res.status_code == 200 and res.json()["data"]["enabled"] is False
    assert res.json()["data"]["state_label"] == "Đang tắt"
    client.patch(f"/api/agent-hub/mcp-keys/{row.id}", json={"enabled": False})       # bấm hai lần
    assert _logs(db, row.id, mcp_log.METHOD_KEY_DISABLE) == 1
    denied = _mcp(client, raw)
    assert denied.status_code == 401 and 'error="invalid_token"' in denied.headers["www-authenticate"]
    last = db.query(AgentMcpCall).filter(AgentMcpCall.key_id == row.id).order_by(AgentMcpCall.id.desc()).first()
    assert last.deny_reason == mcp_log.REASON_DISABLED
    #  Tắt rồi vẫn xem lại được (để chép lại khi bật).
    assert client.get(f"/api/agent-hub/mcp-keys/{row.id}/reveal").status_code == 200
    assert client.patch(f"/api/agent-hub/mcp-keys/{row.id}", json={"enabled": True}).json()["data"]["enabled"] is True
    assert _logs(db, row.id, mcp_log.METHOD_KEY_ENABLE) == 1
    assert _mcp(client, raw).status_code == 200


def test_khoa_tat_van_tinh_tran_nam_khoa(db, owner):
    rows = [mcp_keys.create(db, owner.id, name=f"k{i}")[0] for i in range(mcp_keys.MAX_KEYS)]
    mcp_keys.set_enabled(db, owner.id, rows[0].id, False)
    assert mcp_keys.live_count(db, owner.id) == mcp_keys.MAX_KEYS
    with pytest.raises(ValueError):
        mcp_keys.create(db, owner.id, name="thứ sáu")


def test_tat_ket_noi_oauth_chan_ca_ma_truy_cap_lan_lam_moi(db, owner, as_user):
    client = as_user(owner)
    reg = oauth.register(db, {"client_name": "ChatGPT", "redirect_uris": ["https://chatgpt.com/cb"]}, "1.2.3.4")
    oclient = oauth.client_by_id(db, reg["client_id"])
    row, raw = mcp_keys.create(db, owner.id, name="Qua ChatGPT")
    row.kind, row.oauth_client_id = mcp_keys.KIND_OAUTH, oclient.id
    row.access_expires_at = datetime.now() + timedelta(hours=1)
    row.refresh_hash = oauth._hash("dego_mcr_thu")
    db.commit()
    assert _mcp(client, raw).status_code == 200
    assert client.patch(f"/api/agent-hub/mcp-keys/{row.id}", json={"enabled": False}).status_code == 200
    assert _mcp(client, raw).status_code == 401
    with pytest.raises(oauth.OAuthError) as e:
        oauth.refresh(db, oclient, "dego_mcr_thu")
    assert e.value.error == "invalid_grant" and "đang tắt" in e.value.description
    client.patch(f"/api/agent-hub/mcp-keys/{row.id}", json={"enabled": True})
    assert oauth.refresh(db, oclient, "dego_mcr_thu")["access_token"].startswith(mcp_keys.PREFIX)


def test_quan_tri_loc_duoc_trang_thai_dang_tat(db, owner):
    row, _ = mcp_keys.create(db, owner.id, name="k")
    mcp_keys.set_enabled(db, owner.id, row.id, False)
    assert mcp_keys.state_of(db.get(AgentMcpKey, row.id)) == mcp_keys.KeyState.DISABLED
    assert mcp_keys.STATE_LABELS[mcp_keys.KeyState.DISABLED] == "Đang tắt"
    assert "key" not in mcp_keys.serialize(row) and "raw_view" not in mcp_keys.serialize(row)


# ── Hướng dẫn nối công khai (cho màn /connect-ai) ───────────────────────────────

def test_huong_dan_noi_cong_khai_khong_can_dang_nhap_khong_co_khoa(db, owner):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides.pop(get_current_user, None)          # không đăng nhập
    try:
        mcp_keys.create(db, owner.id, name="có khóa thật trong DB")
        client = TestClient(app)
        cat = client.get("/api/agent-hub/mcp-setup/public").json()["data"]
        assert cat["endpoint"] == f"{BASE}/api/mcp" and {c["client"] for c in cat["clients"]} >= {"chatgpt", "claude_desktop"}
        one = client.get("/api/agent-hub/mcp-setup/public", params={"client": "claude_desktop"}).json()["data"]
        assert cat["placeholder"] in one["snippet"] and "dego_mcp_" not in one["snippet"].replace(cat["placeholder"], "")
        assert client.get("/api/agent-hub/mcp-setup/public", params={"client": "khong-co"}).status_code == 404
        assert client.get("/api/agent-hub/mcp-keys").status_code == 401             # đường riêng vẫn đòi đăng nhập
    finally:
        app.dependency_overrides.pop(get_db, None)
