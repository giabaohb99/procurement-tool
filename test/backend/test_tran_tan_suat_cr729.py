"""bao-CR-729 / BM-020 — trần tần suất gọi API nghiệp vụ (`core/rate_limit.py`).

Phần lớn gọi middleware TRỰC TIẾP qua giao thức ASGI với Redis giả trong bộ nhớ (cùng khuôn
`test_bao_cao_cache_tong_quan.py`); một bài đi qua `app.main` thật để chắc middleware đã gắn và đọc đúng `user_id` từ vé
JWT mà `RequestContextMiddleware` giải mã. conftest tắt trần cho cả bộ test; tệp này tự bật lại.
"""
import asyncio
import logging

import pytest
from fastapi.testclient import TestClient

from app.core import rate_limit
from app.core.auth import create_access_token
from app.core.config import settings
from app.core.rate_limit import (GROUP_ASSISTANT, GROUP_EXPORT, GROUP_MARKET_SEARCH, TOO_FAST_MESSAGE,
                                 RateLimitMiddleware, classify_heavy_group, is_exempt)
from app.core.request_context import RequestContext, reset_context, set_context


class _FakePipeline:
    def __init__(self, store):
        self.store, self.ops = store, []

    def incr(self, key):
        self.ops.append(("incr", key))

    def expire(self, key, seconds):
        self.ops.append(("expire", key))

    async def execute(self):
        out = []
        for op, key in self.ops:
            if op == "incr":
                self.store[key] = self.store.get(key, 0) + 1
                out.append(self.store[key])
            else:
                out.append(True)
        return out


class _FakeRedis:
    def __init__(self):
        self.store: dict[str, int] = {}

    def pipeline(self, transaction=True):
        return _FakePipeline(self.store)


class _BrokenPipeline(_FakePipeline):
    async def execute(self):
        raise ConnectionError("redis down")


class _BrokenRedis:
    calls = 0

    def pipeline(self, transaction=True):
        _BrokenRedis.calls += 1
        return _BrokenPipeline({})


@pytest.fixture
def fake_redis(monkeypatch):
    redis = _FakeRedis()
    monkeypatch.setattr(rate_limit, "_redis_client", lambda: redis)
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_LOG_ONLY", False)
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 5)
    monkeypatch.setattr(settings, "RATE_LIMIT_ANON_PER_MINUTE", 4)
    monkeypatch.setattr(settings, "RATE_LIMIT_HEAVY_PER_MINUTE", 2)
    rate_limit.reset_state()
    yield redis
    rate_limit.reset_state()


def _make_app():
    calls = {"n": 0}

    async def app(scope, receive, send):
        calls["n"] += 1
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": b'{"success":true}'})

    return app, calls


async def _call(mw, method, path):
    messages = []

    async def send(message):
        messages.append(message)

    async def receive():
        return {"type": "http.disconnect"}

    scope = {"type": "http", "method": method, "path": path, "query_string": b"", "headers": [],
             "client": ("10.9.9.9", 1234)}
    await mw(scope, receive, send)
    start = next(m for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return start["status"], {k.decode(): v.decode() for k, v in start["headers"]}, body


def _hit(n, path="/api/purchase-requests", method="GET", user_id=0, ip="203.0.113.5", mw=None):
    """Gọi `n` lượt dưới ngữ cảnh của `user_id` (0 = chưa đăng nhập), trả danh sách mã trạng thái."""
    mw = mw or RateLimitMiddleware(_make_app()[0])
    token = set_context(RequestContext(user_id=user_id, ip=ip))
    try:
        async def run():
            return [(await _call(mw, method, path))[0] for _ in range(n)]
        return asyncio.run(run())
    finally:
        reset_context(token)


# ── bảng đường ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("method,path,group", [
    ("GET", "/api/purchase-orders/export/xlsx", GROUP_EXPORT),
    ("GET", "/api/employees/export/csv", GROUP_EXPORT),
    ("GET", "/api/reports/procurement/summary/export", GROUP_EXPORT),
    ("GET", "/api/customs/lines/export", GROUP_EXPORT),
    ("GET", "/api/documents/12/export/docx", GROUP_EXPORT),
    ("POST", "/api/customs/export-batches", GROUP_EXPORT),
    ("GET", "/api/exports/run", GROUP_EXPORT),
    ("GET", "/api/customs/lines", GROUP_MARKET_SEARCH),
    ("GET", "/api/customs/stats", GROUP_MARKET_SEARCH),
    ("GET", "/api/customs/compare", GROUP_MARKET_SEARCH),
    ("GET", "/api/customs/importers", GROUP_MARKET_SEARCH),
    ("POST", "/api/assistant/chat", GROUP_ASSISTANT),
    #  Không nặng: hỏi trạng thái lô xuất (màn hỏi vài giây một lần), xem một dòng, lịch sử hội thoại, danh sách lô xuất.
    ("GET", "/api/customs/export-batches/3", None),
    ("GET", "/api/customs/export-batches", None),
    ("GET", "/api/customs/lines/9", None),
    ("GET", "/api/assistant/conversations", None),
    ("GET", "/api/exports", None),
    ("GET", "/api/purchase-requests", None),
])
def test_bang_duong_nang(method, path, group):
    assert classify_heavy_group(method, path) == group


@pytest.mark.parametrize("method,path,exempt", [
    ("GET", "/api/health", True),
    ("POST", "/api/agent-gw/tools/run", True),
    ("POST", "/api/sync/datxe/events", True),
    ("POST", "/api/mcp", True),
    ("GET", "/api/v1/help-center/tree", True),
    ("GET", "/api/v1/faq", True),
    ("POST", "/api/v1/faq", False),          # ghi FAQ đòi quyền → vẫn đếm
    ("GET", "/api/healthz", False),
    ("GET", "/api/mcp-keys", False),         # tiền tố phải khớp trọn đoạn
    ("GET", "/api/purchase-requests", False),
])
def test_bang_mien_tran(method, path, exempt):
    assert is_exempt(method, path) is exempt


# ── đếm ───────────────────────────────────────────────────────────────────────

def test_dem_theo_tai_khoan_va_429_dung_phong_bi(fake_redis):
    mw = RateLimitMiddleware(_make_app()[0])
    assert _hit(5, user_id=7, mw=mw) == [200] * 5
    token = set_context(RequestContext(user_id=7, ip="203.0.113.5"))
    try:
        status, headers, body = asyncio.run(_call(mw, "GET", "/api/purchase-requests"))
    finally:
        reset_context(token)
    assert status == 429
    assert 1 <= int(headers["retry-after"]) <= 60
    import json
    payload = json.loads(body)
    assert payload == {"success": False,
                       "error": {"code": "rate_limited", "message": TOO_FAST_MESSAGE, "details": None}}
    assert TOO_FAST_MESSAGE == "Thao tác quá nhanh, vui lòng thử lại sau ít giây"


def test_khac_tai_khoan_khong_anh_huong_nhau_du_chung_ip(fake_redis):
    assert _hit(6, user_id=7, ip="203.0.113.5")[-1] == 429
    #  Cùng IP văn phòng, khác tài khoản: bộ đếm riêng.
    assert _hit(5, user_id=8, ip="203.0.113.5") == [200] * 5


def test_chua_dang_nhap_dem_theo_ip(fake_redis):
    assert _hit(5, user_id=0, ip="198.51.100.1") == [200] * 4 + [429]   # RATE_LIMIT_ANON_PER_MINUTE = 4
    assert _hit(1, user_id=0, ip="198.51.100.2") == [200]
    assert any(k.startswith("rl729:general:ip:198.51.100.1:") for k in fake_redis.store)
    #  Người đã đăng nhập trên cùng IP đó không bị liên lụy.
    assert _hit(1, user_id=9, ip="198.51.100.1") == [200]


def test_duong_nang_chat_hon_va_dem_theo_nhom(fake_redis):
    assert _hit(3, path="/api/purchase-orders/export/xlsx", user_id=7) == [200, 200, 429]
    #  Nhóm khác còn nguyên suất; đường thường vẫn chạy (mức chung 5, đã tiêu 3 + 1 = 4).
    assert _hit(1, path="/api/customs/lines", user_id=7) == [200]
    assert _hit(1, path="/api/purchase-requests", user_id=7) == [200]
    #  Lượt nặng cũng tiêu vào mức chung: lượt thứ 6 trong phút bị chặn dù nhóm tìm kiếm còn suất.
    assert _hit(1, path="/api/customs/lines", user_id=7) == [429]


def test_duong_mien_tran_khong_dem(fake_redis):
    app, calls = _make_app()
    mw = RateLimitMiddleware(app)
    for path, method in (("/api/health", "GET"), ("/api/agent-gw/tools/run", "POST"), ("/api/mcp", "POST"),
                         ("/api/sync/datxe/events", "POST"), ("/api/v1/help-center/tree", "GET")):
        assert _hit(20, path=path, method=method, user_id=7, mw=mw) == [200] * 20
    assert fake_redis.store == {}
    assert calls["n"] == 100


def test_ngoai_api_va_options_khong_dem(fake_redis):
    assert _hit(10, path="/assets/app.js") == [200] * 10
    assert _hit(10, path="/api/purchase-requests", method="OPTIONS", user_id=7) == [200] * 10
    assert fake_redis.store == {}


def test_chi_ghi_log_khong_chan_nhung_co_log(fake_redis, monkeypatch, caplog):
    monkeypatch.setattr(settings, "RATE_LIMIT_LOG_ONLY", True)
    with caplog.at_level(logging.WARNING, logger="app.rate_limit"):
        assert _hit(8, user_id=7) == [200] * 8
    lines = [r.getMessage() for r in caplog.records if r.name == "app.rate_limit"]
    assert lines, "log-only phải ghi lượt vượt"
    assert "chỉ ghi log" in lines[0] and "u:7" in lines[0] and "general" in lines[0]
    assert "/api/purchase-requests" in lines[0]


def test_chan_that_cung_ghi_log(fake_redis, caplog):
    with caplog.at_level(logging.WARNING, logger="app.rate_limit"):
        _hit(6, path="/api/assistant/chat", method="POST", user_id=7)
    lines = [r.getMessage() for r in caplog.records if r.name == "app.rate_limit"]
    assert any("assistant" in m and "u:7" in m and "chỉ ghi log" not in m for m in lines)


def test_cong_tac_tat_thi_khong_dem(fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
    assert _hit(20, user_id=7) == [200] * 20
    assert fake_redis.store == {}


def test_muc_0_la_khong_chan(fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 0)
    monkeypatch.setattr(settings, "RATE_LIMIT_HEAVY_PER_MINUTE", 0)
    assert _hit(20, path="/api/customs/lines", user_id=7) == [200] * 20
    assert fake_redis.store == {}


def test_redis_hong_thi_cho_qua_va_nghi_dem(monkeypatch, caplog):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_LOG_ONLY", False)
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 1)
    monkeypatch.setattr(rate_limit, "_redis_client", lambda: _BrokenRedis())
    rate_limit.reset_state()
    _BrokenRedis.calls = 0
    try:
        with caplog.at_level(logging.WARNING, logger="app.rate_limit"):
            assert _hit(10, user_id=7) == [200] * 10
        #  Hỏng một lần thì nghỉ đếm, không hỏi Redis ở từng lượt gọi sau.
        assert _BrokenRedis.calls == 1
        assert any("fail-open" in r.getMessage() for r in caplog.records)
    finally:
        rate_limit.reset_state()


# ── gắn thật vào app.main ─────────────────────────────────────────────────────

def test_app_that_dem_theo_user_id_trong_ve(fake_redis, monkeypatch):
    """Đi qua `app.main`: `RequestContextMiddleware` giải mã vé, trần đọc `user_id` từ ngữ cảnh."""
    from app.core.request_middleware import RequestContextMiddleware
    from app.main import app

    #  Không ghi `tab_request_log` / dấu phiên xuống MySQL thật của máy chạy bài.
    monkeypatch.setattr(RequestContextMiddleware, "_write", lambda self, *a, **k: None)
    monkeypatch.setattr(RequestContextMiddleware, "_touch", lambda self, *a, **k: None)
    rate_limit.reset_state()

    path = "/api/cr729-khong-co-duong-nay"
    alice = TestClient(app, headers={"Authorization": f"Bearer {create_access_token(70001)}"})
    bob = TestClient(app, headers={"Authorization": f"Bearer {create_access_token(70002)}"})
    codes = [alice.get(path).status_code for _ in range(6)]
    assert codes == [404] * 5 + [429]
    blocked = alice.get(path)
    assert blocked.status_code == 429
    assert blocked.json()["error"]["message"] == TOO_FAST_MESSAGE
    assert "retry-after" in blocked.headers
    assert bob.get(path).status_code == 404
    assert any(k.startswith("rl729:general:u:70001:") for k in fake_redis.store)
    assert alice.get("/api/health").status_code == 200
