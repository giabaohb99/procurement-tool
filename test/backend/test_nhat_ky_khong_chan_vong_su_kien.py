"""Middleware nhật ký KHÔNG được chạm DB ngay trên vòng sự kiện (ép tải 22/10/2026).

Lỗi đã xảy ra: `_write` / `_touch` / `flush_changes` mở `SessionLocal()` đồng bộ NGAY trong
`dispatch` (hàm async). Khi bể kết nối đầy, vòng sự kiện đứng chờ kết nối — mà kết nối đang bị
giữ chỉ được trả khi chính vòng đó chạy tiếp để dọn `get_db`. Hai bên chờ nhau: 60 lượt gọi đồng
thời vào báo cáo mua hàng ra 49 lượt 500 + 19 lượt treo 90 giây; 300 lượt thì API treo hẳn tới khi
restart. Bài này khẳng định cả ba lối ghi đều chạy ở LUỒNG PHỤ (không có vòng sự kiện đang chạy).
"""
import asyncio

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core import request_middleware
from app.core.request_middleware import RequestContextMiddleware


def _on_event_loop() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


@pytest.fixture
def calls(monkeypatch):
    seen: dict[str, list[bool]] = {"write": [], "touch": [], "flush": []}

    def fake_write(self, ctx, **kwargs):
        seen["write"].append(_on_event_loop())

    def fake_touch(self, ctx):
        seen["touch"].append(_on_event_loop())

    def fake_flush(ctx):
        seen["flush"].append(_on_event_loop())
        return 0

    monkeypatch.setattr(RequestContextMiddleware, "_write", fake_write)
    monkeypatch.setattr(RequestContextMiddleware, "_touch", fake_touch)
    monkeypatch.setattr(request_middleware, "flush_changes", fake_flush)
    return seen


def _client() -> TestClient:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/api/units")
    def ok():
        return {"success": True, "data": []}

    @app.get("/api/units/boom")
    def boom():
        raise RuntimeError("nổ giữa chừng")

    @app.delete("/api/units/{oid}")
    def cam(oid: int):
        raise HTTPException(403, "Không có quyền")

    return TestClient(app, raise_server_exceptions=False)


def test_luot_goi_thuong_ghi_nhat_ky_o_luong_phu(calls):
    _client().get("/api/units")
    assert calls["write"] == [False]
    assert calls["touch"] == [False]
    assert calls["flush"] == [False]


def test_luot_goi_bi_chan_van_ghi_o_luong_phu(calls):
    _client().delete("/api/units/1")
    assert calls["write"] == [False]
    assert calls["touch"] == [False]


def test_luot_goi_no_giua_chung_ghi_o_luong_phu(calls):
    _client().get("/api/units/boom")
    assert calls["write"] and not any(calls["write"])
    assert calls["touch"] and not any(calls["touch"])
    assert calls["flush"] and not any(calls["flush"])
