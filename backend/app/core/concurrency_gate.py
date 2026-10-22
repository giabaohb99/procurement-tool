"""CỔNG SỐ LƯỢT GỌI ĐỒNG THỜI — mỗi tiến trình chỉ cho N lượt `/api` chạy cùng lúc (duoc-CR-671).

Vì sao cần (ép tải 22/10/2026, py-spy): mỗi tiến trình có 40 luồng anyio cho hàm đồng bộ nhưng
chỉ 25 kết nối bể (10 + 15). Lượt gọi lấy kết nối ở `get_current_user`, rồi phải XẾP HÀNG chờ luồng
cho `require`/endpoint trong khi vẫn GIỮ kết nối. Dồn ~150 lượt: 37 luồng đứng chờ kết nối, 25 kết
nối nằm trong tay lượt gọi đang chờ luồng — giữ chỗ của nhau, cứ 30 giây nổ `QueuePool TimeoutError`
(277/300 lượt hết giờ). Giới hạn số lượt được VÀO dưới số kết nối bể thì luôn còn kết nối cho
lượt đã vào, nên không thể khóa chết; lượt dư xếp hàng (không hỏng), chờ quá lâu thì 503 rõ ràng.

Middleware ASGI thuần (không `BaseHTTPMiddleware`), bọc NGOÀI `RequestContextMiddleware` để cả phần
ghi `tab_request_log` cũng nằm trong suất đã cấp, và nằm TRONG CORS (xem `main.py`).
"""
import asyncio
import json

from starlette.types import ASGIApp, Receive, Scope, Send

#  Đường không chạm DB hoặc phải trả lời kể cả lúc bận (kiểm sức khỏe container).
EXEMPT_PATHS = ("/api/health",)

BUSY_BODY = json.dumps({
    "success": False,
    "error": {"code": "server_busy",
              "message": "Hệ thống đang bận, vui lòng thử lại sau ít giây.", "details": None},
}, ensure_ascii=False).encode("utf-8")


def resolve_limit(configured: int, pool_size: int, max_overflow: int) -> int:
    """0 = tự tính: chừa 5 kết nối cho việc nền / hai kết nối trong một lượt gọi."""
    pool_total = pool_size + max_overflow
    limit = configured if configured > 0 else pool_total - 5
    return max(1, min(limit, pool_total - 1))


class ConcurrencyGateMiddleware:
    def __init__(self, app: ASGIApp, limit: int, queue_timeout: float, prefix: str = "/api"):
        self.app = app
        self.limit = limit
        self.queue_timeout = queue_timeout
        self.prefix = prefix
        #  Dựng lười và theo TỪNG vòng sự kiện: Semaphore của asyncio gắn vào vòng đầu tiên phải chờ
        #  nó. Prod một tiến trình một vòng; nhưng bộ test mở nhiều TestClient (mỗi cái một vòng).
        self._semaphore: asyncio.Semaphore | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        if scope["type"] != "http" or not path.startswith(self.prefix) or path in EXEMPT_PATHS:
            await self.app(scope, receive, send)
            return
        loop = asyncio.get_running_loop()
        if self._semaphore is None or self._loop is not loop:
            self._semaphore, self._loop = asyncio.Semaphore(self.limit), loop
        semaphore = self._semaphore
        try:
            await asyncio.wait_for(semaphore.acquire(), self.queue_timeout)
        except TimeoutError:
            await _send_busy(send, self.queue_timeout)
            return
        try:
            await self.app(scope, receive, send)
        finally:
            semaphore.release()


async def _send_busy(send: Send, retry_after: float) -> None:
    await send({"type": "http.response.start", "status": 503, "headers": [
        (b"content-type", b"application/json; charset=utf-8"),
        (b"retry-after", str(max(1, int(retry_after // 6))).encode()),
    ]})
    await send({"type": "http.response.body", "body": BUSY_BODY})
