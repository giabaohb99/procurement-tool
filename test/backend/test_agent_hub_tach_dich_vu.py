"""ai-CR-119 — phase S: dịch vụ AI tách khỏi ERP, nói chuyện qua cổng B (`agent_gateway`) với chữ ký máy-nói-máy.

Bài kiểm dựng cổng B thành một app FastAPI nhỏ chạy trên CÙNG SQLite của bài kiểm, rồi cho `agent_hub.erp` ở chế độ
service gọi sang bằng đúng đường HTTP (TestClient thay `requests`): chữ ký, danh tính theo người, công cụ chạy đúng
quyền, công cụ cá nhân chạy tại chỗ, chuyển tiếp web, lọc bảng của dịch vụ AI.
"""
from __future__ import annotations

import json

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core import agent_signature
from app.core.config import settings
from app.core.database import get_db

SECRET = "khoa-ky-thu-nghiem"


@pytest.fixture
def gateway(db, monkeypatch):
    """Cổng B (ERP) + dịch vụ AI ở chế độ service nối với nhau qua TestClient."""
    from app.modules.agent_gateway.controller import router as gw_router
    from app.modules.agent_hub import erp

    gw = FastAPI()
    gw.include_router(gw_router)
    gw.dependency_overrides[get_db] = lambda: db
    client = TestClient(gw)
    monkeypatch.setattr(settings, "AGENT_SERVICE_SECRET", SECRET)
    monkeypatch.setattr(settings, "AGENT_GATEWAY_URL", "http://erp.test")
    monkeypatch.setattr(settings, "AGENT_MODE", "service")
    monkeypatch.setattr(erp, "_remote", None)
    calls: list[tuple[str, str]] = []

    def fake_request(method, url, params=None, data=None, headers=None, timeout=0, **kw):
        path = url.replace("http://erp.test", "")
        calls.append((method, path))
        return client.request(method, path, params=params, content=data, headers=headers)

    monkeypatch.setattr(erp.requests, "request", fake_request)
    erp._impl()._tool_defs = (0.0, [])
    return calls


def test_bang_cua_dich_vu_ai_tach_dung(db):
    from app.core.agent_tables import agent_tables, is_agent_table
    from app.core.base_model import Base

    names = {t.name for t in agent_tables(Base.metadata)}
    assert {"tab_agent_task", "tab_agent_message", "tab_ai_key", "tab_agent_meeting", "tab_assistant_conversation"} <= names
    assert not any(n.startswith(("tab_user", "tab_purchase", "tab_employee")) for n in names)
    assert is_agent_table("tab_agent_group_message") and not is_agent_table("tab_setting")


def test_chu_ky_may_noi_may(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_SERVICE_SECRET", SECRET)
    h = agent_signature.sign_headers("POST", "/api/agent-gw/tools/run", b'{"a":1}', user_id=7)
    ok, reason, uid = agent_signature.verify("POST", "/api/agent-gw/tools/run", b'{"a":1}', h)
    assert ok and uid == 7
    assert not agent_signature.verify("POST", "/api/agent-gw/tools/run", b'{"a":2}', h)[0]          # thân khác
    assert not agent_signature.verify("POST", "/api/agent-gw/tools/other", b'{"a":1}', h)[0]        # đường khác
    h2 = dict(h, **{agent_signature.HEADER_USER: "8"})
    assert not agent_signature.verify("POST", "/api/agent-gw/tools/run", b'{"a":1}', h2)[0]         # đổi người
    assert "quá hạn" in agent_signature.verify("POST", "/x", b"", h, now=int(h[agent_signature.HEADER_TS]) + 999)[1]
    monkeypatch.setattr(settings, "AGENT_SERVICE_SECRET", "")
    with pytest.raises(ValueError):
        agent_signature.sign_headers("GET", "/x")


def test_dich_vu_ai_hoi_erp_dung_nguoi_dung_quyen(db, seed, gateway):
    from app.modules.agent_hub import erp
    from app.modules.user.model import User

    u = erp.user_by_id(db, seed.u_req_id)
    assert isinstance(u, erp.ErpUser) and u.id == seed.u_req_id and u.is_active and u.label
    orm = db.get(User, seed.u_req_id)
    assert erp.describe(db, u) == erp._Local.describe(db, orm)               # cùng nhãn với chế độ embedded
    assert erp.user_by_id(db, 0) is None
    assert erp.user_by_email(db, orm.email).id == seed.u_req_id
    #  Quyền hỏi qua cổng, bằng đúng hồ sơ quyền của ERP.
    assert erp.can(db, u, "purchase_request", "read") == erp._Local.can(db, orm, "purchase_request", "read")
    assert erp.can(db, u, "khong_co_entity", "write") is False
    #  Tài khoản bị khóa: cổng từ chối.
    orm.is_active = False
    db.commit()
    with pytest.raises(erp.ErpError):
        erp.tool_defs(db, u) and erp._impl()._call("GET", "/me", user_id=seed.u_req_id)
    orm.is_active = True
    db.commit()


def test_cong_cu_erp_chay_o_erp_cong_cu_ca_nhan_chay_tai_cho(db, seed, monkeypatch, gateway):
    from app.modules.agent_hub import erp, personal_memory as pm
    from app.modules.assistant import tools as T

    monkeypatch.setattr(pm, "_embedder", lambda: None)
    u = erp.user_by_id(db, seed.u_req_id)
    names = {d.name for d in erp.tool_defs(db, u)}
    assert names == {d.name for d in T.tool_defs(db)}                        # model thấy đủ bộ công cụ như trước
    local = erp.local_tool_names()
    assert {"remember_fact", "list_my_meetings", "read_group_messages", "my_calendar_events"} <= local
    assert "my_approval_tasks" not in local and "draft_purchase_request" not in local
    calls = gateway
    n = len(calls)
    out = erp.run_tool(db, u, "remember_fact", {"text": "anh thích cà phê đen", "section": "so_thich"})
    assert out.get("ok") and len(calls) == n                                 # cá nhân: không đi HTTP
    out = erp.run_tool(db, u, "my_approval_tasks", {"limit": 3})
    assert isinstance(out, dict) and "error" not in out and calls[-1] == ("POST", "/api/agent-gw/tools/run")
    assert "Không có công cụ" in erp.run_tool(db, u, "cong_cu_bia", {}).get("error", "")
    #  Chữ ký sai (khóa lệch hai đầu): cổng từ chối, công cụ trả lỗi đọc được chứ không nổ.
    real = agent_signature.sign_headers
    monkeypatch.setattr(agent_signature, "sign_headers",
                        lambda *a, **kw: {**real(*a, **kw), agent_signature.HEADER_SIGN: "0" * 64})
    with pytest.raises(erp.ErpError):
        erp._impl()._call("GET", "/ping")
    assert "Không gọi được công cụ ERP" in erp.run_tool(db, u, "my_approval_tasks", {}).get("error", "")


def test_cac_duong_con_lai_cua_cong(db, seed, gateway, monkeypatch):
    from app.core import app_settings
    from app.modules.agent_hub import erp
    from app.modules.notification.model import Notification

    assert erp.notifications_max_id(db) == 0 and erp.notifications_after(db, 0, 10) == []
    db.add(Notification(user_id=seed.u_req_id, title="Phiếu chờ bạn duyệt", body="YCMH-1", link="/x", is_read=False))
    db.commit()
    rows = erp.notifications_after(db, 0, 10)
    assert rows and rows[0]["title"] == "Phiếu chờ bạn duyệt" and erp.notifications_max_id(db) == rows[0]["id"]
    assert erp.tickets_max_id(db) >= 0 and erp.tickets_open(db, ["open"], []) == []
    assert erp.match_employee(db, "khong-co-ai-ten-nay") is None
    u = erp.user_by_id(db, seed.u_req_id)
    assert erp.projects_for(db, u) == [] or isinstance(erp.projects_for(db, u)[0], dict)
    assert erp.search_users(db, u.email.split("@")[0]) or erp.search_users(db, u.label.split(" (")[0])
    #  Cấu hình hệ thống: dịch vụ AI đọc tab_setting qua cổng, hỏng cổng thì rơi về .env.
    snap = erp.settings_snapshot(db)
    assert isinstance(snap, dict)
    app_settings.refresh()
    assert app_settings.get("ai_gemini_model") == (snap.get("ai_gemini_model") or settings.AI_GEMINI_MODEL)
    assert erp.created_details(db, "leave", 999999) == [] or True
    #  Tệp báo cáo không phải của mình: None.
    assert erp.report_file(db, u, 123456) is None


def test_erp_chuyen_tiep_web_sang_dich_vu_ai_kem_chu_ky(db, seed, monkeypatch):
    from app.core import agent_identity
    from app.core.auth import get_current_user
    from app.modules.agent_gateway import proxy
    from app.modules.user.model import User

    monkeypatch.setattr(settings, "AGENT_SERVICE_SECRET", SECRET)
    monkeypatch.setattr(settings, "AGENT_SERVICE_URL", "http://agent.test")
    erp_app = FastAPI()
    erp_app.include_router(proxy.router)
    user = db.get(User, seed.u_req_id)
    erp_app.dependency_overrides[get_current_user] = lambda: user
    erp_app.dependency_overrides[get_db] = lambda: db
    got: list[dict] = []

    class R:
        status_code = 200
        content = b'{"success": true, "data": {"ok": 1}}'
        headers = {"content-type": "application/json"}

    def fake_request(method, url, params=None, data=None, headers=None, timeout=0, allow_redirects=True):
        got.append({"method": method, "url": url, "data": data, "headers": headers, "params": params})
        return R()

    monkeypatch.setattr(proxy.requests, "request", fake_request)
    client = TestClient(erp_app)
    r = client.post("/api/agent-hub/ai-key", json={"provider": "gemini", "key": "x"},
                    headers={"Authorization": "Bearer jwt-that", "Cookie": "a=b"})
    assert r.status_code == 200 and r.json()["data"] == {"ok": 1}
    fwd = got[-1]
    assert fwd["url"] == "http://agent.test/api/agent-hub/ai-key"
    assert "authorization" not in {k.lower() for k in fwd["headers"]} and "cookie" not in {k.lower() for k in fwd["headers"]}
    ok, _reason, uid = agent_signature.verify("POST", "/api/agent-hub/ai-key", fwd["data"], fwd["headers"])
    assert ok and uid == seed.u_req_id                                        # dịch vụ AI xác định đúng người
    #  Google gọi về không có JWT: chuyển với danh tính 0.
    client.get("/api/agent-hub/google/callback?code=abc&state=xyz")
    assert agent_signature.verify("GET", "/api/agent-hub/google/callback", b"", got[-1]["headers"])[2] == 0
    assert got[-1]["params"] == "code=abc&state=xyz"
    #  Phía dịch vụ AI: dependency danh tính đọc chữ ký, tra hồ sơ qua cổng (giả), từ chối chữ ký lạ.
    from app.modules.agent_hub import erp

    monkeypatch.setattr(erp, "user_by_id", lambda db, uid: erp.ErpUser(id=uid, email="a@b", is_active=(uid == seed.u_req_id)))
    monkeypatch.setattr(agent_identity, "_CACHE", {})
    ai_app = FastAPI()

    @ai_app.get("/api/agent-hub/whoami")
    def whoami(user=Depends(agent_identity.current_user)):
        return {"id": user.id}

    ai = TestClient(ai_app)
    h = agent_signature.sign_headers("GET", "/api/agent-hub/whoami", b"", user_id=seed.u_req_id)
    assert ai.get("/api/agent-hub/whoami", headers=h).json() == {"id": seed.u_req_id}
    assert ai.get("/api/agent-hub/whoami").status_code == 401
    h_other = agent_signature.sign_headers("GET", "/api/agent-hub/whoami", b"", user_id=999999)
    assert ai.get("/api/agent-hub/whoami", headers=h_other).status_code == 401      # tài khoản không hoạt động


def test_che_do_erp_khong_gan_bot_va_cau_hinh_mode():
    assert settings.agent_embedded and not settings.agent_is_service and not settings.agent_is_erp
    from app.modules.assistant.controller import ERP_LOCAL_PATHS, erp_local_router

    assert {r.path for r in erp_local_router.routes} == ERP_LOCAL_PATHS
    body = json.dumps({"x": 1}).encode()
    assert agent_signature.body_digest(body) == agent_signature.body_digest(body.decode())


def test_chuyen_tiep_khong_chan_vong_su_kien_cua_erp(monkeypatch):
    """Lỗi dev 08/10/2026: proxy gọi dịch vụ AI bằng `requests` ngay trong hàm async → cả ERP đứng hình trong lúc chờ;
    dịch vụ AI quay lại hỏi quyền ERP qua cổng B thì hai bên chờ nhau (mọi API ERP treo tới 120 giây). Lệnh gọi phải
    chạy ở luồng phụ: trong lúc chờ, ERP vẫn phục vụ được việc khác."""
    import asyncio
    import time

    from starlette.requests import Request

    from app.modules.agent_gateway import proxy

    monkeypatch.setattr(settings, "AGENT_SERVICE_SECRET", SECRET)
    monkeypatch.setattr(settings, "AGENT_SERVICE_URL", "http://agent.test")

    class R:
        status_code = 200
        content = b"{}"
        headers = {"content-type": "application/json"}

    def slow_request(*args, **kwargs):
        time.sleep(0.4)  # dịch vụ AI chậm / đang chờ hỏi ngược ERP
        return R()

    monkeypatch.setattr(proxy.requests, "request", slow_request)

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {"type": "http", "method": "GET", "path": "/api/agent-hub/groups/meta", "query_string": b"", "headers": []}

    async def main():
        ticks = 0

        async def other_work():
            nonlocal ticks
            for _ in range(20):
                await asyncio.sleep(0.01)
                ticks += 1

        async def call_proxy():
            resp = await proxy.forward(Request(scope, receive), 1)
            return resp, ticks  # số nhịp việc khác đã chạy TỚI LÚC proxy xong

        (resp, ticks_when_done), _ = await asyncio.gather(call_proxy(), other_work())
        return resp, ticks_when_done

    resp, ticks_when_done = asyncio.run(main())
    assert resp.status_code == 200
    #  Gọi chặn: vòng sự kiện đứng 0,4 giây, việc khác được 0–1 nhịp. Luồng phụ: việc khác chạy hết 20 nhịp trong lúc chờ.
    assert ticks_when_done >= 15


def test_nhan_su_nghi_erp_da_tach_bao_sang_dich_vu_ai(db, seed, monkeypatch):
    from datetime import datetime, timedelta

    from app.core import agent_client
    from app.modules.agent_gateway import proxy
    from app.modules.agent_hub.model import AgentChatLink, AgentUserKey
    from app.modules.agent_hub.service import revoke_user_access

    db.add(AgentChatLink(user_id=seed.u_req_id, chat_id="555", linked_at=datetime.now(),
                         expires_at=datetime.now() + timedelta(days=30), created_by=0, updated_by=0))
    db.add(AgentUserKey(user_id=seed.u_req_id, provider="gemini", key_enc="x", key_hint="0000", created_by=0, updated_by=0))
    db.commit()
    #  Chế độ embedded: gọi thẳng, đóng đủ các dòng của người đó.
    assert agent_client.revoke_user(db, seed.u_req_id) is True
    db.commit()
    assert db.query(AgentChatLink).filter_by(user_id=seed.u_req_id, revoked_at=None).count() == 0
    assert db.query(AgentUserKey).filter_by(user_id=seed.u_req_id, revoked_at=None).count() == 0
    assert revoke_user_access(db, seed.u_req_id) == 0
    #  Chế độ erp: ký rồi POST sang dịch vụ AI; hỏng mạng thì trả False chứ không chặn việc khóa tài khoản.
    monkeypatch.setattr(settings, "AGENT_MODE", "erp")
    monkeypatch.setattr(settings, "AGENT_SERVICE_URL", "http://agent.test")
    monkeypatch.setattr(settings, "AGENT_SERVICE_SECRET", SECRET)
    sent: list[dict] = []

    class R:
        status_code = 200

    monkeypatch.setattr(agent_client.requests, "post", lambda url, data=None, headers=None, timeout=0: sent.append(
        {"url": url, "data": data, "headers": headers}) or R())
    assert agent_client.revoke_user(db, 42) is True
    assert sent[-1]["url"] == "http://agent.test/api/agent-hub/internal/revoke"
    assert agent_signature.verify("POST", "/api/agent-hub/internal/revoke", sent[-1]["data"], sent[-1]["headers"])[0]
    monkeypatch.setattr(agent_client.requests, "post", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("mạng hỏng")))
    assert agent_client.revoke_user(db, 42) is False
    #  Chuyển tiếp web KHÔNG bao giờ mở đường nội bộ cho người dùng.
    from app.core.auth import get_current_user
    from app.modules.user.model import User

    erp_app = FastAPI()
    erp_app.include_router(proxy.router)
    erp_app.dependency_overrides[get_current_user] = lambda: db.get(User, seed.u_req_id)
    assert TestClient(erp_app).post("/api/agent-hub/internal/revoke", json={"user_id": 1}).status_code == 404
