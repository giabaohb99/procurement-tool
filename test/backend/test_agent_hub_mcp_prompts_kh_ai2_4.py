"""kh-AI2-4 — cổng MCP mở `prompts`: mỗi cẩm nang (skill) người dùng được đọc thành một lời nhắc sẵn, để Claude Desktop /
ChatGPT chọn từ danh sách là AI đọc cẩm nang trước khi làm. Đúng quyền Kho skill: skill không được giao và skill không
tồn tại trả cùng một lỗi; nhóm Kho skill bị tắt ở cấu hình MCP thì không liệt kê."""
from app.core.subject_match import SUBJECT_EMPLOYEE
from app.modules.agent_hub import mcp, mcp_keys

from test_ai_skill_kho_k1 import admin, give, make_skill, org  # noqa: F401


class _Key:
    def __init__(self, scope=mcp_keys.SCOPE_READ):
        self.scope = scope


def _rpc(db, user, method, params=None):
    return mcp.handle(db, user, _Key(), {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}, {})


def test_initialize_khai_prompts(org):
    res = _rpc(org.db, org.boss, "initialize", {"clientInfo": {"name": "Claude Desktop"}})
    assert "prompts" in res["result"]["capabilities"]


def test_danh_sach_loi_nhac_theo_skill_duoc_giao(org, admin):  # noqa: F811
    db = org.db
    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_EMPLOYEE, org.boss.employee_id)])
    prompts = _rpc(db, org.boss, "prompts/list")["result"]["prompts"]
    names = [p["name"] for p in prompts]
    assert names[0] == mcp.START_PROMPT and "quy-trinh-mua" in names
    skill = next(p for p in prompts if p["name"] == "quy-trinh-mua")
    assert "Khi lập YCMH" in skill["description"] and skill["arguments"][0]["name"] == "yeu_cau"
    #  Người không được giao chỉ thấy lời nhắc chung.
    assert [p["name"] for p in _rpc(db, org.kt, "prompts/list")["result"]["prompts"]] == [mcp.START_PROMPT]


def test_lay_loi_nhac_dan_doc_skill_roi_lam(org, admin):  # noqa: F811
    db = org.db
    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_EMPLOYEE, org.boss.employee_id)])
    res = _rpc(db, org.boss, "prompts/get", {"name": "quy-trinh-mua", "arguments": {"yeu_cau": "Lập YCMH 10 thùng giấy"}})
    text = res["result"]["messages"][0]["content"]["text"]
    assert res["result"]["messages"][0]["role"] == "user"
    assert 'read_skill' in text and "quy-trinh-mua" in text and "Lập YCMH 10 thùng giấy" in text
    start = _rpc(db, org.boss, "prompts/get", {"name": mcp.START_PROMPT, "arguments": {"yeu_cau": "x" * 5000}})
    assert "list_skills" in start["result"]["messages"][0]["content"]["text"]
    assert len(start["result"]["messages"][0]["content"]["text"]) < 3000         # yêu cầu bị cắt trần


def test_skill_khong_duoc_giao_va_khong_ton_tai_cung_mot_loi(org, admin):  # noqa: F811
    db = org.db
    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_EMPLOYEE, org.boss.employee_id)])
    hidden = _rpc(db, org.kt, "prompts/get", {"name": "quy-trinh-mua"})["error"]
    missing = _rpc(db, org.kt, "prompts/get", {"name": "khong-ton-tai"})["error"]
    assert hidden["code"] == missing["code"] == -32602
    assert hidden["message"].replace("quy-trinh-mua", "X") == missing["message"].replace("khong-ton-tai", "X")


def test_nhom_kho_skill_tat_thi_khong_liet_ke(org, admin, monkeypatch):  # noqa: F811
    from app.modules.agent_hub import mcp_settings

    db = org.db
    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_EMPLOYEE, org.boss.employee_id)])
    monkeypatch.setattr(mcp_settings, "tool_listed", lambda db, name: name not in mcp.SKILL_TOOLS)
    assert _rpc(db, org.boss, "prompts/list")["result"]["prompts"] == []
    assert _rpc(db, org.boss, "prompts/get", {"name": "quy-trinh-mua"})["error"]["code"] == -32602


# ── đếm lỗi 5xx + hàng đợi của dịch vụ AI (O-01) ──────────────────────────────────────────────────────────────────

class _FakeRedis:
    def __init__(self, broken=False):
        self.kv, self.ttl, self.lists, self.broken = {}, {}, {"celery": [1, 2, 3], "agent_code": []}, broken

    def _check(self):
        if self.broken:
            raise ConnectionError("redis tắt")

    def incr(self, k):
        self._check()
        self.kv[k] = int(self.kv.get(k, 0)) + 1
        return self.kv[k]

    def expire(self, k, s):
        self.ttl[k] = s

    def mget(self, keys):
        self._check()
        return [self.kv.get(k) for k in keys]

    def llen(self, q):
        self._check()
        return len(self.lists.get(q, []))


def test_dem_5xx_theo_gio_va_hang_doi(monkeypatch):
    from datetime import datetime, timedelta

    from app.modules.agent_hub import service_health as H

    fake = _FakeRedis()
    monkeypatch.setattr(H, "_redis", lambda: fake)
    now = datetime(2026, 10, 23, 10, 30)
    for at in (now, now, now - timedelta(hours=5), now - timedelta(hours=30)):       # lỗi 30 giờ trước không tính
        H.record_5xx(at)
    assert H.count_5xx(now=now) == 3 and set(fake.ttl.values()) == {H.KEEP_SECONDS}
    assert H.queue_lengths() == {"celery": 3, "agent_code": 0}
    fake.broken = True
    H.record_5xx(now)                                                                  # Redis hỏng: không ném lỗi
    snap = H.snapshot(now=now)
    assert snap["errors_5xx_24h"] is None and snap["queues"] == {"celery": None, "agent_code": None}


def test_middleware_dem_500_va_loi_chua_bat(monkeypatch):
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.testclient import TestClient

    from app.modules.agent_hub import service_health as H

    fake = _FakeRedis()
    monkeypatch.setattr(H, "_redis", lambda: fake)
    app = FastAPI()
    app.middleware("http")(H.count_server_errors)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/loi")
    def loi():
        return JSONResponse({"x": 1}, status_code=503)

    @app.get("/vo")
    def vo():
        raise RuntimeError("vỡ")

    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/ok").status_code == 200 and client.get("/loi").status_code == 503
    assert client.get("/vo").status_code == 500
    assert H.count_5xx() == 2


def test_tong_quan_ai_co_khoi_suc_khoe(monkeypatch):
    from app.modules.agent_hub import service_health as H

    monkeypatch.setattr(H, "_redis", lambda: _FakeRedis())
    snap = H.snapshot()
    assert set(snap) == {"errors_5xx_24h", "queues", "counting_5xx", "note"}
    import inspect

    from app.modules.agent_hub import ai_overview

    assert "service_health.snapshot()" in inspect.getsource(ai_overview.build)
