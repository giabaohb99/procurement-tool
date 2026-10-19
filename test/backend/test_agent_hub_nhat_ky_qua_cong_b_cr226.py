"""ai-CR-226 — Agent 1 đọc log dev 19/10/2026: ở CHẾ ĐỘ TÁCH, nhật ký công cụ của Trợ lý / bot ghi vào DB agent_hub (không có
`tab_audit_log`) → «Table 'agent_hub.tab_audit_log' doesn't exist», mọi dấu vết «ai nhờ bot làm gì» mất trắng (8 lượt / giờ,
4 lần tạo lịch Google). Gộp mục 7 của bài rà: xem lại / bật / tắt khóa MCP có thêm dòng nhật ký ERP lâu dài.

Canh:
  - chế độ nhúng: dòng nhật ký công cụ ghi thẳng như cũ;
  - chế độ tách: đi qua cổng B `POST /api/agent-gw/audit`, dòng nằm ở DB ERP, người ghi lấy từ CHỮ KÝ (không từ thân);
  - cổng B hỏng → lượt công cụ vẫn chạy, chỉ mất dòng nhật ký (không ném);
  - thân sai (action > 50 ký tự, entity rỗng) → 422, không ghi;
  - xem lại khóa MCP để lại dòng `agent_mcp_key / key_reveal` trong nhật ký thao tác ERP.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.modules.agent_hub import erp
from app.modules.audit.model import AuditLog


def _rows(db, **kw):
    return db.query(AuditLog).filter_by(**kw).all()


def test_che_do_nhung_ghi_thang(db, seed):
    from app.modules.assistant import tools

    tools._audit(db, type("U", (), {"id": seed.u_req_id})(), "my_calendar_events", {"days": 3}, {"count": 2})
    rows = _rows(db, entity="assistant", action="tool:my_calendar_events")
    assert len(rows) == 1 and rows[0].created_by == seed.u_req_id and '"rows": 2' in rows[0].message


@pytest.fixture
def gateway(db, monkeypatch):
    from app.modules.agent_gateway.controller import router as gw_router

    gw = FastAPI()
    gw.include_router(gw_router)
    gw.dependency_overrides[get_db] = lambda: db
    client = TestClient(gw)
    monkeypatch.setattr(settings, "AGENT_SERVICE_SECRET", "khoa-ky-thu-nghiem")
    monkeypatch.setattr(settings, "AGENT_GATEWAY_URL", "http://erp.test")
    monkeypatch.setattr(settings, "AGENT_MODE", "service")
    monkeypatch.setattr(erp, "_remote", None)
    calls: list[tuple[str, str]] = []

    def fake_request(method, url, params=None, data=None, headers=None, timeout=0, **kw):
        path = url.replace("http://erp.test", "")
        calls.append((method, path))
        return client.request(method, path, params=params, content=data, headers=headers)

    monkeypatch.setattr(erp.requests, "request", fake_request)
    yield calls
    monkeypatch.setattr(erp, "_remote", None)


def test_che_do_tach_day_qua_cong_b_nguoi_ghi_theo_chu_ky(db, seed, gateway):
    from app.modules.assistant import tools

    user = type("U", (), {"id": seed.u_req_id})()
    tools._audit(db, user, "create_calendar_event", {"title": "Phan Rang"}, {"ok": True})
    assert ("POST", "/api/agent-gw/audit") in gateway
    rows = _rows(db, entity="assistant", action="tool:create_calendar_event")
    assert len(rows) == 1 and rows[0].created_by == seed.u_req_id and "Phan Rang" in rows[0].message


def test_cong_b_hong_thi_chi_mat_dong_nhat_ky(db, seed, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_MODE", "service")
    monkeypatch.setattr(settings, "AGENT_GATEWAY_URL", "http://erp.test")
    monkeypatch.setattr(settings, "AGENT_SERVICE_SECRET", "khoa-ky-thu-nghiem")
    monkeypatch.setattr(erp, "_remote", None)
    monkeypatch.setattr(erp, "CONNECT_RETRY_WAITS", ())

    def down(*a, **k):
        raise erp.requests.ConnectionError("ERP đang khởi động lại")

    monkeypatch.setattr(erp.requests, "request", down)
    try:
        assert erp.audit(db, seed.u_req_id, "assistant", 0, "tool:x", "m") is False
    finally:
        monkeypatch.setattr(erp, "_remote", None)
    assert _rows(db, action="tool:x") == []


def test_cong_b_tu_choi_than_sai(db, seed, gateway):
    from app.core import agent_signature
    import json

    client_calls = gateway
    for body in ({"entity": "assistant", "action": "x" * 51}, {"entity": "", "action": "tool:a"},
                 {"entity": "assistant", "action": "tool:a", "entity_id": -1}):
        data = json.dumps(body).encode()
        headers = {**agent_signature.sign_headers("POST", "/api/agent-gw/audit", data, seed.u_req_id),
                   "content-type": "application/json"}
        res = erp.requests.request("POST", "http://erp.test/api/agent-gw/audit", data=data, headers=headers)
        assert res.status_code == 422, body
    assert ("POST", "/api/agent-gw/audit") in client_calls
    assert db.query(AuditLog).count() == 0


def test_xem_lai_khoa_de_lai_dong_nhat_ky_erp(db, seed, monkeypatch):
    from app.core.auth import get_current_user
    from app.main import app
    from app.modules.agent_hub import mcp_keys, mcp_log
    from app.modules.user.model import User

    monkeypatch.setattr(mcp_log, "_redis", lambda: (_ for _ in ()).throw(ConnectionError("không Redis")))
    owner = db.get(User, seed.u_req_id)
    row, _ = mcp_keys.create(db, owner.id, name="Claude")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: owner
    try:
        client = TestClient(app)
        assert client.get(f"/api/agent-hub/mcp-keys/{row.id}/reveal").status_code == 200
        assert client.patch(f"/api/agent-hub/mcp-keys/{row.id}", json={"enabled": False}).status_code == 200
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
    actions = {r.action for r in _rows(db, entity="agent_mcp_key", entity_id=row.id)}
    assert actions == {"key_reveal", "key_disable"}
    assert all(r.created_by == owner.id for r in _rows(db, entity="agent_mcp_key"))
