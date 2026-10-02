"""Gói A2 (hiệu năng báo cáo, 01/10/2026) — `core.report_cache.ReportSummaryCacheMiddleware`.

Gọi middleware TRỰC TIẾP qua giao thức ASGI (không qua TestClient/httpx) — nhanh, không phụ
thuộc DB/auth thật, và cắm được client Redis GIẢ qua monkeypatch `report_cache._redis_client`.
Mỗi test tự `asyncio.run(...)` thay vì `async def test_...` — bộ này KHÔNG cài pytest-asyncio.
"""
import asyncio

import pytest

from app.core import report_cache
from app.core.report_cache import ReportSummaryCacheMiddleware

ALLOWED_PATH = "/api/vehicle-bookings/summary"


class _FakeRedis:
    """Redis giả TRONG BỘ NHỚ — đủ GET/SET(nx/ex)/DELETE/aclose cho middleware dùng. CHIA SẺ
    `store` giữa mọi lần `_redis_client()` trong MỘT test (mô phỏng một Redis server thật)."""

    def __init__(self):
        self.store: dict[str, str] = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None, px=None, nx=False):
        if nx and key in self.store:
            return None
        self.store[key] = value
        return True

    async def delete(self, key):
        self.store.pop(key, None)

    async def aclose(self):
        pass


class _BrokenRedis:
    """Mô phỏng Redis CHẾT/timeout — MỌI lệnh đọc/ghi ném lỗi."""

    async def get(self, key):
        raise ConnectionError("redis down")

    async def set(self, key, value, ex=None, px=None, nx=False):
        raise ConnectionError("redis down")

    async def delete(self, key):
        raise ConnectionError("redis down")

    async def aclose(self):
        pass


def _scope(path, query="preset=this_year", token="tok-a", method="GET"):
    headers = [(b"authorization", f"Bearer {token}".encode())] if token else []
    return {"type": "http", "method": method, "path": path,
           "query_string": query.encode(), "headers": headers}


def _make_app(body=b'{"success":true,"data":{"n":1}}', status=200, delay=0.0):
    """App ASGI giả, ĐẾM số lần được gọi — kiểm HIT có thật sự bỏ qua nó không."""
    calls = {"n": 0}

    async def app(scope, receive, send):
        calls["n"] += 1
        if delay:
            await asyncio.sleep(delay)
        await send({"type": "http.response.start", "status": status,
                   "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": body, "more_body": False})

    return app, calls


async def _call(mw, scope):
    """Gọi middleware, gom lại (status, headers dict, body bytes)."""
    messages = []

    async def send(message):
        messages.append(message)

    async def receive():
        return {"type": "http.disconnect"}

    await mw(scope, receive, send)
    start = next(m for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    headers = {k.decode(): v.decode() for k, v in start["headers"]}
    return start["status"], headers, body


@pytest.fixture(autouse=True)
def _ttl_60(monkeypatch):
    #  Đặt tường minh (dù trùng mặc định) — không phụ thuộc `.env` của máy chạy test.
    monkeypatch.setattr(report_cache.settings, "REPORT_CACHE_TTL", 60)


def test_allowlist_va_preset_lan_2_hit_bo_qua_app(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(report_cache, "_redis_client", lambda: fake)
    app, calls = _make_app()
    mw = ReportSummaryCacheMiddleware(app)

    async def run():
        return await _call(mw, _scope(ALLOWED_PATH)), await _call(mw, _scope(ALLOWED_PATH))

    (s1, h1, b1), (s2, h2, b2) = asyncio.run(run())
    assert s1 == 200 and h1["x-report-cache"] == "miss"
    assert s2 == 200 and h2["x-report-cache"] == "hit"
    assert b1 == b2
    assert calls["n"] == 1   # app CHỈ được gọi 1 lần — lần 2 phục vụ từ cache


def test_duong_khong_trong_allowlist_khong_cache(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(report_cache, "_redis_client", lambda: fake)
    app, calls = _make_app()
    mw = ReportSummaryCacheMiddleware(app)
    export_path = "/api/vehicle-bookings/summary/export"

    async def run():
        await _call(mw, _scope(export_path))
        return await _call(mw, _scope(export_path))

    status, headers, _ = asyncio.run(run())
    assert status == 200
    assert "x-report-cache" not in headers
    assert calls["n"] == 2   # KHÔNG cache — app chạy mỗi lần


def test_duong_cu_theo_year_khong_co_preset_khong_cache(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(report_cache, "_redis_client", lambda: fake)
    app, calls = _make_app()
    mw = ReportSummaryCacheMiddleware(app)

    async def run():
        await _call(mw, _scope(ALLOWED_PATH, query="year=2026"))
        return await _call(mw, _scope(ALLOWED_PATH, query="year=2026"))

    _, headers, _ = asyncio.run(run())
    assert "x-report-cache" not in headers
    assert calls["n"] == 2


def test_khoa_phan_biet_theo_token_hai_phien_khong_gop(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(report_cache, "_redis_client", lambda: fake)
    app, calls = _make_app()
    mw = ReportSummaryCacheMiddleware(app)

    async def run():
        return (await _call(mw, _scope(ALLOWED_PATH, token="user-a")),
                await _call(mw, _scope(ALLOWED_PATH, token="user-b")))

    (_, h1, _), (_, h2, _) = asyncio.run(run())
    assert h1["x-report-cache"] == "miss"
    assert h2["x-report-cache"] == "miss"   # KHÔNG hit dù cùng path+query — token khác
    assert calls["n"] == 2


def test_khoa_khong_phan_biet_thu_tu_query(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(report_cache, "_redis_client", lambda: fake)
    app, calls = _make_app()
    mw = ReportSummaryCacheMiddleware(app)

    async def run():
        await _call(mw, _scope(ALLOWED_PATH, query="preset=this_year&group_by=pic"))
        return await _call(mw, _scope(ALLOWED_PATH, query="group_by=pic&preset=this_year"))

    _, headers, _ = asyncio.run(run())
    assert headers["x-report-cache"] == "hit"
    assert calls["n"] == 1


def test_redis_chet_van_tra_200_fail_open(monkeypatch):
    monkeypatch.setattr(report_cache, "_redis_client", lambda: _BrokenRedis())
    app, calls = _make_app()
    mw = ReportSummaryCacheMiddleware(app)

    status, headers, body = asyncio.run(_call(mw, _scope(ALLOWED_PATH)))
    assert status == 200
    assert headers["x-report-cache"] == "miss"
    assert calls["n"] == 1
    assert b'"n":1' in body


def test_ttl_0_tat_cache_hoan_toan(monkeypatch):
    monkeypatch.setattr(report_cache.settings, "REPORT_CACHE_TTL", 0)
    fake = _FakeRedis()
    monkeypatch.setattr(report_cache, "_redis_client", lambda: fake)
    app, calls = _make_app()
    mw = ReportSummaryCacheMiddleware(app)

    async def run():
        await _call(mw, _scope(ALLOWED_PATH))
        return await _call(mw, _scope(ALLOWED_PATH))

    status, headers, _ = asyncio.run(run())
    assert status == 200
    assert "x-report-cache" not in headers
    assert calls["n"] == 2


def test_khong_cache_response_loi(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(report_cache, "_redis_client", lambda: fake)
    app, calls = _make_app(body=b'{"success":false}', status=500)
    mw = ReportSummaryCacheMiddleware(app)

    async def run():
        await _call(mw, _scope(ALLOWED_PATH))
        return await _call(mw, _scope(ALLOWED_PATH))

    status, headers, _ = asyncio.run(run())
    assert status == 500
    assert headers["x-report-cache"] == "miss"   # lần 2 vẫn miss — 500 không được cache
    assert calls["n"] == 2


def test_single_flight_khoa_tranh_tinh_trung(monkeypatch):
    """Hai request ĐỒNG THỜI cùng khóa, Redis trống: tiến trình thứ 2 thấy khóa bị giữ, ĐỢI rồi
    ăn kết quả của tiến trình 1 — app chỉ chạy ĐÚNG 1 lần."""
    monkeypatch.setattr(report_cache, "_LOCK_POLL_MS", 10)
    monkeypatch.setattr(report_cache, "_LOCK_MAX_WAIT_MS", 500)
    fake = _FakeRedis()
    monkeypatch.setattr(report_cache, "_redis_client", lambda: fake)
    app, calls = _make_app(delay=0.05)   # tiến trình 1 "tính" trong 50ms
    mw = ReportSummaryCacheMiddleware(app)

    async def run():
        return await asyncio.gather(_call(mw, _scope(ALLOWED_PATH)), _call(mw, _scope(ALLOWED_PATH)))

    (s1, h1, b1), (s2, h2, b2) = asyncio.run(run())
    assert calls["n"] == 1   # single-flight: CHỈ một request thật sự chạy app
    assert s1 == s2 == 200 and b1 == b2
    assert {h1["x-report-cache"], h2["x-report-cache"]} == {"miss", "hit"}
