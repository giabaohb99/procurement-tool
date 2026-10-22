"""Cổng số lượt gọi đồng thời mỗi tiến trình (duoc-CR-671, `core/concurrency_gate.py`).

Lỗi gốc (ép tải 22/10/2026): 40 luồng xử lý > 25 kết nối bể → lượt gọi giữ kết nối chờ luồng, luồng
chờ kết nối, 150 lượt dồn vào ra 277/300 lượt hết giờ chờ. Cổng giữ số lượt ĐANG CHẠY dưới số kết
nối bể; lượt dư xếp hàng, quá hạn thì 503 có phong bì chuẩn. Các bài dưới đo đúng ba điều đó.
"""
import asyncio

import httpx
import pytest
from fastapi import FastAPI

from app.core.concurrency_gate import ConcurrencyGateMiddleware, resolve_limit


def _app(limit: int, timeout: float, gate_open: asyncio.Event, peak: dict) -> FastAPI:
    app = FastAPI()
    app.add_middleware(ConcurrencyGateMiddleware, limit=limit, queue_timeout=timeout)

    @app.get("/api/slow")
    async def slow():
        peak["now"] += 1
        peak["max"] = max(peak["max"], peak["now"])
        await gate_open.wait()
        peak["now"] -= 1
        return {"success": True, "data": None}

    @app.get("/api/health")
    async def health():
        return {"ok": True}

    @app.get("/docs-like")
    async def free():
        return {"ok": True}

    return app


def _client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t")


def test_khong_bao_gio_qua_so_luot_cho_phep_va_luot_du_xep_hang_khong_hong():
    async def run():
        release, peak = asyncio.Event(), {"now": 0, "max": 0}
        async with _client(_app(3, 5.0, release, peak)) as client:
            tasks = [asyncio.create_task(client.get("/api/slow")) for _ in range(20)]
            await asyncio.sleep(0.2)
            assert peak["now"] == 3          # chỉ 3 lượt được vào, 17 lượt đang xếp hàng
            release.set()
            responses = await asyncio.gather(*tasks)
        assert [r.status_code for r in responses] == [200] * 20
        assert peak["max"] == 3
    asyncio.run(run())


def test_xep_hang_qua_han_thi_503_co_phong_bi_chuan():
    async def run():
        release, peak = asyncio.Event(), {"now": 0, "max": 0}
        async with _client(_app(1, 0.2, release, peak)) as client:
            first = asyncio.create_task(client.get("/api/slow"))
            await asyncio.sleep(0.05)
            busy = await client.get("/api/slow")
            release.set()
            assert (await first).status_code == 200
        assert busy.status_code == 503
        body = busy.json()
        assert body["success"] is False and body["error"]["code"] == "server_busy"
        assert int(busy.headers["retry-after"]) >= 1
    asyncio.run(run())


def test_kiem_suc_khoe_va_duong_ngoai_api_khong_bi_chan_khi_ban():
    async def run():
        release, peak = asyncio.Event(), {"now": 0, "max": 0}
        async with _client(_app(1, 0.2, release, peak)) as client:
            hold = asyncio.create_task(client.get("/api/slow"))
            await asyncio.sleep(0.05)
            health = await client.get("/api/health")
            free = await client.get("/docs-like")
            release.set()
            await hold
        assert health.status_code == 200 and free.status_code == 200
    asyncio.run(run())


def test_endpoint_no_van_tra_suat_cho_luot_sau():
    app = FastAPI()
    app.add_middleware(ConcurrencyGateMiddleware, limit=1, queue_timeout=0.5)

    @app.get("/api/boom")
    async def boom():
        raise RuntimeError("nổ")

    @app.get("/api/ok")
    async def ok():
        return {"success": True}

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
                                     base_url="http://t") as client:
            for _ in range(3):
                assert (await client.get("/api/boom")).status_code == 500
            assert (await client.get("/api/ok")).status_code == 200   # suất không bị rò sau lỗi
    asyncio.run(run())


@pytest.mark.parametrize("configured, pool, overflow, expected", [
    (0, 10, 15, 20),     # mặc định prod: chừa 5 kết nối
    (0, 2, 1, 1),        # bể quá nhỏ: tự tính ra âm thì kẹp về 1, không bao giờ 0
    (0, 1, 0, 1),
    (100, 10, 15, 24),   # khai quá tay vẫn bị kẹp dưới số kết nối bể
    (8, 10, 15, 8),
    (-3, 10, 15, 20),    # số âm = tự tính
])
def test_tran_luon_nho_hon_so_ket_noi_be(configured, pool, overflow, expected):
    assert resolve_limit(configured, pool, overflow) == expected


def test_mot_cong_dung_qua_nhieu_vong_su_kien_khong_no():
    """Bộ test mở nhiều TestClient (mỗi cái một vòng) trên cùng `app.main.app` — cổng phải chịu được."""
    release, peak = asyncio.Event(), {"now": 0, "max": 0}
    release.set()
    app = _app(1, 1.0, release, peak)

    async def burst():
        async with _client(app) as client:
            responses = await asyncio.gather(*[client.get("/api/slow") for _ in range(5)])
        return [r.status_code for r in responses]

    for _ in range(3):
        assert asyncio.run(burst()) == [200] * 5
