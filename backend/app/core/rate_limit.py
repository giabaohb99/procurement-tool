"""TRẦN TẦN SUẤT GỌI API NGHIỆP VỤ (bao-CR-729, vá BM-020).

Trước CR này `core/limiter.py` khai `default_limits=["300/minute"]` nhưng không có hiệu lực: một tài khoản hợp lệ rút sạch
dữ liệu trong phạm vi của mình ở tốc độ tối đa. Tệp này là middleware ASGI thuần, không dùng `SlowAPIMiddleware`, vì:

- slowapi đếm theo `key_func(request)` cho mọi đường như nhau, bộ nhớ trong tiến trình (mỗi worker uvicorn đếm riêng),
  không có chế độ chỉ-ghi-log, không fail-open khi Redis hỏng, và trả 429 không đúng phong bì `{success, error}`;
- gắn `SlowAPIMiddleware` còn làm `default_limits` áp cả lên bốn đường auth vốn đã có trần riêng — đổi hành vi cũ.

Bốn luật của tệp:

1. **Đếm theo TÀI KHOẢN, không theo IP** — cả công ty ra Internet chung một IP văn phòng. Id lấy từ ngữ cảnh mà
   `RequestContextMiddleware` đã dựng (nó đã giải mã vé JWT một lần để ghi nhật ký), KHÔNG giải mã lần hai, không đụng DB.
   Lượt chưa đăng nhập (không vé / vé hỏng chữ ký) rơi về IP thật (`ctx.ip`, cùng nguồn với limiter cũ).
2. **Bộ đếm ở Redis** (cửa sổ cố định một phút, `INCR` + `EXPIRE`) để mọi worker đếm chung.
3. **Redis hỏng thì KHÔNG chặn ai** (fail-open): ghi cảnh báo một lần rồi bỏ đếm trong `_REDIS_BACKOFF_SECONDS` giây, để
   mỗi lượt gọi không phải chờ hết thời gian chờ của Redis.
4. **Chặn là 429 đúng phong bì** kèm `Retry-After` tới đầu phút sau; `RATE_LIMIT_LOG_ONLY` thì chỉ ghi log, cho đi tiếp.

Vị trí trong `main.py`: nằm TRONG `RequestContextMiddleware` (để đọc được ngữ cảnh, và để lượt bị 429 vẫn có dòng
`tab_request_log`), NGOÀI `ReportSummaryCacheMiddleware` (lượt trúng bộ nhớ đệm vẫn bị đếm).
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass

from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings
from app.core.request_context import get_context

logger = logging.getLogger("app.rate_limit")

WINDOW_SECONDS = 60
_REDIS_TIMEOUT = 0.2          # giây — Redis chậm thì bỏ qua nhanh, đừng kéo cả lượt gọi theo
_REDIS_BACKOFF_SECONDS = 30   # Redis vừa hỏng thì nghỉ đếm chừng này giây rồi mới thử lại
_KEY_PREFIX = "rl729"

GROUP_GENERAL = "general"
GROUP_EXPORT = "export"
GROUP_MARKET_SEARCH = "market_search"
GROUP_ASSISTANT = "assistant"

TOO_FAST_MESSAGE = "Thao tác quá nhanh, vui lòng thử lại sau ít giây"


@dataclass(frozen=True)
class PathRule:
    """Một dòng của bảng đường: `path` khớp đúng, hoặc khớp tiền tố khi `prefix=True` (chính nó + mọi đường con).
    `method=None` = mọi phương thức."""

    path: str
    prefix: bool = False
    method: str | None = None

    def matches(self, method: str, path: str) -> bool:
        if self.method and self.method != method:
            return False
        if path == self.path:
            return True
        return self.prefix and path.startswith(self.path.rstrip("/") + "/")


#  MIỄN TRẦN — mỗi dòng phải có lý do.
EXEMPT_RULES: tuple[PathRule, ...] = (
    #  Kiểm sức khỏe container: phải trả lời kể cả khi bận, không chạm DB.
    PathRule("/api/health"),
    #  Cổng B (máy gọi máy): dịch vụ AI gọi ERP, ký HMAC (`core/agent_signature.py`), không có vé người dùng — đếm ở
    #  đây là đếm chung một IP container cho MỌI người đang dùng Trợ lý / bot / MCP. Lượt của người dùng đã bị đếm
    #  ở ERP lúc vào `/api/assistant`, `/api/mcp`.
    PathRule("/api/agent-gw", prefix=True),
    #  App đặt xe / duyệt dấu cũ đẩy sự kiện sang, ký HMAC (`core/sync_signature.py`); một máy chủ gửi thay cả công ty.
    PathRule("/api/sync/datxe", prefix=True),
    #  Cổng MCP đã có trần riêng ở Redis theo khóa + theo IP + lượt khóa sai (ai-CR-209, chỉnh ở màn cấu hình MCP);
    #  xác thực bằng khóa MCP chứ không phải vé JWT nên ở đây chỉ đếm được theo IP chung văn phòng; và máy khách MCP
    #  cần câu 429 dạng lỗi JSON-RPC, không phải phong bì `{success, error}`.
    PathRule("/api/mcp", prefix=True),
    #  Trung tâm trợ giúp + FAQ: đọc công khai không cần đăng nhập (không có vé → cả văn phòng chung một bộ đếm IP),
    #  dữ liệu vốn công khai, nhẹ. Đường GHI vẫn đòi quyền nên vẫn bị đếm.
    PathRule("/api/v1/help-center", prefix=True, method="GET"),
    PathRule("/api/v1/faq", prefix=True, method="GET"),
)

#  ĐƯỜNG NẶNG — mỗi nhóm một bộ đếm riêng, mức `RATE_LIMIT_HEAVY_PER_MINUTE`, đếm THÊM vào mức chung.
#  Xuất tệp còn khớp theo luật đoạn `export` ở `classify_heavy_group` (mọi `/export`, `/export/csv`, `/export/xlsx`,
#  `/summary/export`, `/{id}/export/docx`...), bảng dưới chỉ ghi phần luật đó không phủ.
HEAVY_RULES: tuple[tuple[str, PathRule], ...] = (
    #  Tạo lô xuất tra cứu thị trường (dựng tệp lớn ở nền). KHÔNG gồm GET `/export-batches/...`: màn hỏi trạng thái lô
    #  vài giây một lần, đếm vào đây là tự chặn người đang chờ tệp.
    (GROUP_EXPORT, PathRule("/api/customs/export-batches", method="POST")),
    #  Màn Xuất dữ liệu tập trung (`export_log`): mỗi lượt dựng nguyên một tệp của một danh mục.
    (GROUP_EXPORT, PathRule("/api/exports/run", method="GET")),
    #  Tìm kiếm tra cứu thị trường: danh sách dòng + ba thẻ tổng hợp trên bảng hải quan lớn nhất hệ thống.
    (GROUP_MARKET_SEARCH, PathRule("/api/customs/lines", method="GET")),
    (GROUP_MARKET_SEARCH, PathRule("/api/customs/stats", method="GET")),
    (GROUP_MARKET_SEARCH, PathRule("/api/customs/compare", method="GET")),
    (GROUP_MARKET_SEARCH, PathRule("/api/customs/importers", method="GET")),
    #  Trợ lý AI: mỗi lượt gửi gọi model (tốn tiền) + công cụ đọc dữ liệu. Chỉ POST; GET lịch sử hội thoại là nhẹ.
    (GROUP_ASSISTANT, PathRule("/api/assistant", prefix=True, method="POST")),
)


def is_exempt(method: str, path: str) -> bool:
    return any(rule.matches(method, path) for rule in EXEMPT_RULES)


def classify_heavy_group(method: str, path: str) -> str | None:
    """Tên nhóm đường nặng của lượt gọi, hoặc `None` nếu chỉ chịu mức chung."""
    if "export" in path.split("/"):
        return GROUP_EXPORT
    for group, rule in HEAVY_RULES:
        if rule.matches(method, path):
            return group
    return None


def resolve_subject(scope: Scope) -> tuple[str, bool]:
    """(chủ thể đếm, đã đăng nhập). Đọc ngữ cảnh `RequestContextMiddleware` đã dựng — không giải mã vé lần hai.

    Vé hết hạn vẫn mang `user_id` (chữ ký đúng, BM-012) nên vẫn đếm theo tài khoản. Không có ngữ cảnh (gọi middleware
    ngoài `app.main`) thì rơi về IP TCP."""
    ctx = get_context()
    if ctx is not None and ctx.user_id:
        return f"u:{ctx.user_id}", True
    ip = ctx.ip if ctx is not None and ctx.ip else ""
    if not ip:
        client = scope.get("client")
        ip = (client[0] if client else "") or "unknown"
    return f"ip:{ip}", False


def _redis_client():
    """Một client cho mỗi vòng sự kiện (kết nối redis.asyncio gắn với vòng tạo ra nó; prod một vòng một tiến trình,
    bộ test mở nhiều `TestClient`). Bài kiểm monkeypatch hàm này để cắm Redis giả."""
    loop = asyncio.get_running_loop()
    cached = _client_cache.get("client")
    if cached is not None and _client_cache.get("loop") is loop:
        return cached
    import redis.asyncio as redis_asyncio
    client = redis_asyncio.from_url(settings.REDIS_URL, socket_connect_timeout=_REDIS_TIMEOUT,
                                    socket_timeout=_REDIS_TIMEOUT)
    _client_cache.update(client=client, loop=loop)
    return client


_client_cache: dict = {}
_state = {"redis_down_until": 0.0}


def reset_state() -> None:
    """Cho bài kiểm: quên client đã dựng + mốc nghỉ đếm vì Redis hỏng."""
    _client_cache.clear()
    _state["redis_down_until"] = 0.0


async def _incr_counters(keys: list[str]) -> list[int] | None:
    """Tăng các bộ đếm trong MỘT lượt khứ hồi. `None` = Redis hỏng (đã ghi log, đã bật nghỉ đếm)."""
    if time.monotonic() < _state["redis_down_until"]:
        return None
    try:
        pipe = _redis_client().pipeline(transaction=False)
        for key in keys:
            pipe.incr(key)
            pipe.expire(key, WINDOW_SECONDS + 10)
        results = await pipe.execute()
        return [int(results[i * 2]) for i in range(len(keys))]
    except Exception as exc:  # noqa: BLE001 — Redis hỏng kiểu gì cũng là "không đếm được", không được chặn người dùng
        _state["redis_down_until"] = time.monotonic() + _REDIS_BACKOFF_SECONDS
        logger.warning("Redis không phản hồi, tạm bỏ đếm trần tần suất %ss (fail-open): %s", _REDIS_BACKOFF_SECONDS, exc)
        return None


def _too_fast_body() -> bytes:
    return json.dumps({"success": False, "error": {"code": "rate_limited", "message": TOO_FAST_MESSAGE,
                                                    "details": None}}, ensure_ascii=False).encode("utf-8")


async def _send_too_fast(send: Send, retry_after: int) -> None:
    await send({"type": "http.response.start", "status": 429, "headers": [
        (b"content-type", b"application/json; charset=utf-8"),
        (b"retry-after", str(retry_after).encode()),
    ]})
    await send({"type": "http.response.body", "body": _too_fast_body()})


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, prefix: str = "/api"):
        self.app = app
        self.prefix = prefix

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        if (scope["type"] != "http" or not settings.RATE_LIMIT_ENABLED or not path.startswith(self.prefix)
                or scope.get("method") == "OPTIONS"):
            await self.app(scope, receive, send)
            return
        method = scope.get("method", "")
        if is_exempt(method, path):
            await self.app(scope, receive, send)
            return

        subject, signed_in = resolve_subject(scope)
        general_limit = settings.RATE_LIMIT_PER_MINUTE if signed_in else settings.RATE_LIMIT_ANON_PER_MINUTE
        heavy_group = classify_heavy_group(method, path)
        #  (nhóm, mức) — mức 0 là không chặn nhóm đó, khỏi đếm.
        checks = [(GROUP_GENERAL, general_limit)]
        if heavy_group:
            checks.append((heavy_group, settings.RATE_LIMIT_HEAVY_PER_MINUTE))
        checks = [(group, limit) for group, limit in checks if limit > 0]
        if not checks:
            await self.app(scope, receive, send)
            return

        now = time.time()
        window = int(now // WINDOW_SECONDS)
        counts = await _incr_counters([f"{_KEY_PREFIX}:{group}:{subject}:{window}" for group, _ in checks])
        if counts is None:
            await self.app(scope, receive, send)
            return

        exceeded = [(group, limit, count) for (group, limit), count in zip(checks, counts) if count > limit]
        if not exceeded:
            await self.app(scope, receive, send)
            return

        log_only = settings.RATE_LIMIT_LOG_ONLY
        for group, limit, count in exceeded:
            #  Ghi lượt vượt ĐẦU TIÊN của cửa sổ và mỗi bội số của mức (2x, 3x...) — đủ thấy ai vượt, vượt bao xa, mà
            #  một vòng lặp gọi điên không dội ngập log.
            if count == limit + 1 or count % limit == 0:
                logger.warning("Vượt trần tần suất%s: chu_the=%s nhom=%s muc=%s/phut dem=%s %s %s",
                               " (chỉ ghi log)" if log_only else "", subject, group, limit, count, method, path)
        if log_only:
            await self.app(scope, receive, send)
            return
        retry_after = max(1, WINDOW_SECONDS - int(now % WINDOW_SECONDS))
        await _send_too_fast(send, retry_after)
