"""Cache ngắn hạn cho các `/summary` báo cáo kiểu Haravan (gói A2, 01/10/2026) — Trang Tổng quan
mở 13 lời gọi `/summary` song song, lặp lại trong vài phút (đổi tab/quay lại). Cache ngắn hạn
biến phần lớn thành HIT, giảm áp lực lên pool kết nối DB (gói A1), không đổi logic từng báo cáo.
Xem load-test `fullstack-developer-261001-1103-load-test-8-bao-cao-moi.md` §8.4.

Middleware ASGI THUẦN (không `BaseHTTPMiddleware`), chỉ can thiệp GET trong ALLOWLIST (13 đường
`/summary` tổng hợp, KHÔNG gồm `/summary/export`) VÀ có query `preset` (hợp đồng MỚI; gọi kiểu
CŨ bằng `year` — cùng path, xem `purchase_progress`/`survey_progress` controller — không cache).

Khóa = sha256(path + query ĐÃ CANH THỨ TỰ + sha256(token Bearer)) — PER-SESSION. ⚠️ Một HIT bỏ
qua hẳn `require()`/`apply_scope` (không gọi app bên trong) — an toàn vì khóa gắn với CHÍNH
token đó; đổi quyền/đăng xuất thì cache cũ vẫn phục vụ token cũ tối đa `REPORT_CACHE_TTL` giây.

Fail OPEN: Redis chết/chậm (timeout ~0.2s) → coi như miss, tính bình thường, không bao giờ làm
hỏng/chậm đáng kể response vì Redis (xem `_RedisDown`).
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from urllib.parse import parse_qsl, urlencode

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings

logger = logging.getLogger("app.report_cache")

#  13 đường `/summary` tổng hợp (verify ở `main.py`/`modules/*/report_controller.py`, 01/10/2026).
#  KHÔNG gồm `/summary/export` hay `/api/survey-requests/{sid}/report/summary` (path ĐỘNG).
REPORT_SUMMARY_PATHS = frozenset({
    "/api/reports/procurement/summary", "/api/reports/pr-lines/summary",
    "/api/survey-progress/summary", "/api/purchase-progress/summary",
    "/api/survey-report/summary", "/api/employees/summary", "/api/leave-requests/summary",
    "/api/leave-balances/summary", "/api/vehicle-bookings/summary", "/api/seal-requests/summary",
    "/api/documents/summary", "/api/approvals/summary", "/api/work/summary",
})

_SOCKET_TIMEOUT = 0.2   # giây — Redis chết thì fail NHANH, đừng kéo cả request theo
#  Single-flight: khóa tự hết hạn (ms) nếu tiến trình giữ khóa chết nửa chừng; chu kỳ/trần đợi.
_LOCK_TTL_MS, _LOCK_POLL_MS, _LOCK_MAX_WAIT_MS = 3000, 100, 1500

class _RedisDown(Exception):
    """NỘI BỘ — Redis không trả lời được; tắt sớm các lệnh còn lại của CÙNG request, không bao
    giờ thoát khỏi middleware."""

def _redis_client():
    """Client MỚI mỗi lần gọi — rẻ, và cho test monkeypatch hàm này dù middleware đã dựng xong
    (Starlette chỉ gọi lúc XỬ LÝ request, không lúc khởi tạo app)."""
    import redis.asyncio as redis_asyncio
    return redis_asyncio.from_url(settings.REDIS_URL, socket_connect_timeout=_SOCKET_TIMEOUT,
                                  socket_timeout=_SOCKET_TIMEOUT, decode_responses=True)

def _cache_key(path: str, query_string: bytes, token: str) -> str:
    """Thứ tự query KHÔNG quan trọng; TOKEN khác nhau luôn ra khóa khác nhau — không gộp hai
    phiên dù giống hệt tham số."""
    canon_query = urlencode(sorted(parse_qsl(query_string.decode(), keep_blank_values=True)))
    raw = f"{path}?{canon_query}|{hashlib.sha256(token.encode()).hexdigest()}"
    return "report_cache:" + hashlib.sha256(raw.encode()).hexdigest()

def _bearer_token(headers: list[tuple[bytes, bytes]]) -> str:
    for name, value in headers:
        if name == b"authorization":
            text = value.decode("latin-1")
            return text[7:].strip() if text.lower().startswith("bearer ") else text
    return ""

def _should_cache(scope: Scope) -> tuple[bool, str]:
    """(nên_cache, token) — chỉ GET, trong allowlist, VÀ có `preset` trên query (đường cũ theo
    `year`, `/export`, hay request không phải GET đều KHÔNG cache)."""
    if scope["method"] != "GET" or scope["path"] not in REPORT_SUMMARY_PATHS:
        return False, ""
    params = dict(parse_qsl(scope.get("query_string", b"").decode(), keep_blank_values=True))
    if "preset" not in params:
        return False, ""
    return True, _bearer_token(scope.get("headers", []))

async def _get(client, key: str) -> dict | None:
    try:
        raw = await client.get(key)
    except Exception as exc:  # noqa: BLE001 — Redis hỏng kiểu gì cũng là "không đọc được"
        raise _RedisDown from exc
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None   # giá trị hỏng trong Redis — coi như miss, đừng làm sập request

async def _try_lock(client, key: str) -> bool:
    try:
        return bool(await client.set(key + ":lock", "1", nx=True, px=_LOCK_TTL_MS))
    except Exception as exc:  # noqa: BLE001
        raise _RedisDown from exc

async def _release_lock(client, key: str) -> None:
    try:
        await client.delete(key + ":lock")
    except Exception:  # noqa: BLE001 — không quan trọng, khóa tự hết hạn sau _LOCK_TTL_MS
        pass

async def _set(client, key: str, payload: dict) -> None:
    try:
        await client.set(key, json.dumps(payload), ex=settings.REPORT_CACHE_TTL)
    except Exception:  # noqa: BLE001 — ghi cache hỏng thì thôi, response vẫn trả bình thường
        logger.warning("Redis SET lỗi cho %s — bỏ qua, không ảnh hưởng response", key, exc_info=True)

async def _wait_for_leader(client, key: str) -> dict | None:
    """Single-flight: đợi NGẮN tiến trình giữ khóa xong rồi THÔI — không chặn vô hạn nếu tiến
    trình kia chết giữa chừng (khóa tự hết hạn). Redis rớt giữa lúc đợi -> coi như không đợi
    được gì, không ném `_RedisDown` tiếp (phần chờ là TỐI ƯU, không bắt buộc)."""
    waited = 0
    while waited < _LOCK_MAX_WAIT_MS:
        await asyncio.sleep(_LOCK_POLL_MS / 1000)
        waited += _LOCK_POLL_MS
        try:
            result = await _get(client, key)
        except _RedisDown:
            return None
        if result is not None:
            return result
    return None

def _encode_headers(headers: list[tuple[bytes, bytes]]) -> list[list[str]]:
    return [[k.decode("latin-1"), v.decode("latin-1")] for k, v in headers]

async def _send_payload(send: Send, payload: dict, cache_header: str) -> None:
    headers = [(k.encode("latin-1"), v.encode("latin-1")) for k, v in payload["headers"]
              if k.lower() != "x-report-cache"]
    headers.append((b"x-report-cache", cache_header.encode()))
    await send({"type": "http.response.start", "status": payload["status"], "headers": headers})
    await send({"type": "http.response.body", "body": payload["body"].encode("utf-8"),
               "more_body": False})

async def _compute(app: ASGIApp, scope: Scope, receive: Receive) -> dict:
    """Chạy app THẬT, gom status+headers+body — cần ĐẦY ĐỦ để biết có cache được (chỉ 200)
    TRƯỚC khi gửi cho client, nên không chảy thẳng (streaming) được."""
    captured: dict = {"status": 500, "headers": [], "chunks": []}

    async def capture_send(message):
        if message["type"] == "http.response.start":
            captured["status"] = message["status"]
            captured["headers"] = message.get("headers", [])
        elif message["type"] == "http.response.body":
            captured["chunks"].append(message.get("body", b""))

    await app(scope, receive, capture_send)
    body = b"".join(captured["chunks"])
    return {"status": captured["status"], "headers": _encode_headers(captured["headers"]),
           "body": body.decode("utf-8", "replace")}

class ReportSummaryCacheMiddleware:
    """Cache GET `/summary` TTL `REPORT_CACHE_TTL` giây (0 = tắt), khóa theo (path, query, token).
    Đăng ký TRƯỚC `RequestContextMiddleware`/CORS ở `main.py` (thêm-sau-thành-ngoài, xem comment
    ở đó) — một HIT vẫn được `RequestContextMiddleware` ghi `tab_request_log` bình thường (nhanh
    hơn hẳn, tín hiệu tốt để nhận ra cache có chạy) và CORS vẫn bọc đúng."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or settings.REPORT_CACHE_TTL <= 0:
            return await self.app(scope, receive, send)
        cacheable, token = _should_cache(scope)
        if not cacheable:
            return await self.app(scope, receive, send)

        key = _cache_key(scope["path"], scope.get("query_string", b""), token)
        client = _redis_client()
        try:
            leader = True
            try:
                cached = await _get(client, key)
                if cached is not None:
                    return await _send_payload(send, cached, "hit")
                leader = await _try_lock(client, key)
                if not leader:
                    waited = await _wait_for_leader(client, key)
                    if waited is not None:
                        return await _send_payload(send, waited, "hit")
            except _RedisDown:
                logger.warning("Redis không phản hồi cho %s — tính trực tiếp (fail-open)", key)
                return await _send_payload(send, await _compute(self.app, scope, receive), "miss")

            payload = await _compute(self.app, scope, receive)
            if payload["status"] == 200:
                await _set(client, key, payload)
            if leader:
                await _release_lock(client, key)
            await _send_payload(send, payload, "miss")
        finally:
            await client.aclose()
