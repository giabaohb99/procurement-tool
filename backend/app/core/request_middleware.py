"""MIDDLEWARE NGỮ CẢNH — mỗi lượt gọi một dòng `tab_request_log` (bao-CR-312, P1).

Đây là phần "đáng làm nhất so với công bỏ ra" của cả thiết kế: một tệp trả lời
được bốn trong sáu câu hỏi ở §1 của tài liệu — **endpoint nào · gửi gì · nhận
lại gì · lượt nào BỊ CHẶN** — mà không đụng vào 213 lời gọi `record(...)`, không
đụng tầng ORM.

Ba luật cứng của tệp này:

1. **Ghi nhật ký hỏng thì lượt gọi vẫn phải chạy.** Mọi chỗ ghi nằm trong
   `try/except`, hỏng thì ghi cảnh báo ra log container rồi thôi. Nhật ký là
   thứ phụ trợ; để nó làm sập một cú duyệt phiếu là đánh đổi sai.
2. **Không đọc thân của lượt không ghi.** Quyết định ghi hay không xong TRƯỚC
   khi gọi endpoint (`should_log_request`), vì nó chi phối việc có đụng vào
   body và có đệm response hay không.
3. **Không đệm thứ không phải JSON.** Tệp đính kèm, Excel, PDF chảy thẳng qua;
   đệm chúng vào RAM để ghi nhật ký là đổi một dòng nhật ký lấy vài chục MB.

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §2, §4.1, §6.
"""
import json
import logging
import time
import traceback

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.client_ip import get_client_ip
from app.core.config import settings
from app.core.device_fingerprint import MAX_USER_AGENT, device_hash
from app.core.logging_codes import ACTOR_KIND_USER, SOURCE_API
from app.core.logging_policy import (MAX_BODY_BYTES, MAX_ERROR_DETAIL_BYTES, MAX_PATH,
                                     MAX_QUERY_STRING, MAX_REFERER, MAX_ROUTE,
                                     mask_error_detail, mask_payload, redact_raw_inputs,
                                     should_capture_response, should_log_request,
                                     should_skip_by_result, summarize_success)
from app.core.request_context import RequestContext, new_request_id, reset_context, set_context

log = logging.getLogger("app.request_log")

#  Kiểu nội dung được phép đệm để đọc thân trả về. Ngoài danh sách này (tệp
#  đính kèm, Excel, PDF, HTML bản in) thì response đi thẳng, không ai chạm vào.
CAPTURABLE_CONTENT_TYPES = ("application/json",)

#  Bằng đúng `MAX_BODY_BYTES` — trước đây 256 KB, tức đệm gấp bốn lần thứ có thể
#  ghi rồi vứt ba phần tư. Đệm nghĩa là nuốt vào RAM, và trần này nhân với số
#  lượt gọi đồng thời chứ không phải với một.
MAX_CAPTURE_BYTES = MAX_BODY_BYTES

#  Phương thức có thân request. GET/HEAD/OPTIONS thì đừng gọi `await
#  request.body()` — nay ghi cả GET nên đó là 3.000 lượt chờ vô ích mỗi ngày.
METHODS_WITH_BODY = ("POST", "PUT", "PATCH", "DELETE")


def _peek_user_id(request) -> int:
    """Đọc `sub` trong token — KHÔNG tra DB, không ném lỗi.

    Middleware chạy trước mọi dependency nên chưa có `get_current_user`. Token
    hỏng / hết hạn thì trả `0`: đó chính là dòng nhật ký của một lượt gọi không
    danh tính, thứ cần ghi lại chứ không phải thứ cần chặn (cửa quyền thật nằm
    ở `get_current_user`, không phải ở đây).
    """
    header = request.headers.get("authorization") or ""
    if not header.lower().startswith("bearer "):
        return 0
    try:
        payload = jwt.decode(header[7:].strip(), settings.JWT_SECRET,
                             algorithms=[settings.JWT_ALG])
        return int(payload.get("sub") or 0)
    except (JWTError, KeyError, ValueError, TypeError):
        return 0


def _route_pattern(path: str, path_params: dict) -> str:
    """Dựng lại mẫu route từ đường dẫn thật + tham số đã bóc.

    `/api/purchase-orders/129/items/4412` -> `/api/purchase-orders/{id}/items/{item_id}`.
    Thay theo TỪNG ĐOẠN chứ không `replace` cả chuỗi, để giá trị `1` của một
    tham số không nuốt mất chữ `1` nằm trong đoạn khác.

    Starlette 0.40 không đặt `scope["route"]` (chỉ có `endpoint` +
    `path_params`), nên phải dựng lại — đừng đi tìm khóa đó, nó không có.
    """
    if not path_params:
        return path
    lookup = {str(value): name for name, value in path_params.items()}
    return "/".join("{%s}" % lookup[seg] if seg in lookup else seg for seg in path.split("/"))


def _read_request_body(request, content_type: str) -> dict | None:
    """Thân request đã che, dạng JSON — hoặc `None` nếu không có gì đáng ghi."""
    if content_type.startswith("multipart/form-data"):
        #  CỐ Ý không đọc: thân multipart là tệp tải lên, có khi vài chục MB.
        #  Đọc để lấy tên tệp là buộc cả tệp vào RAM cho một dòng nhật ký, mà
        #  tên tệp thì `record(...)` của phân hệ đính kèm đã ghi rồi.
        return {"content_type": "multipart/form-data",
                "size": int(request.headers.get("content-length") or 0)}
    return None


def _parse_body(raw: bytes, content_type: str) -> dict | None:
    if not raw:
        return None
    if len(raw) > MAX_BODY_BYTES:
        return {"_truncated": True, "size": len(raw)}
    if not content_type.startswith("application/json"):
        return {"content_type": content_type or "?", "size": len(raw)}
    try:
        return mask_payload(json.loads(raw))
    except (ValueError, UnicodeDecodeError):
        return {"_unparsed": True, "size": len(raw)}


def _summarize_response(raw: bytes, status_code: int) -> tuple[dict | None, str]:
    """Thân trả về + mã lỗi, theo Q9.

    2xx giữ `message` + phần ĐỊNH DANH của `data` (`summarize_success`). Bản đầu
    chỉ giữ `data.id` và hụt ở ba ca gặp hằng ngày — thân không có khóa `id`
    (`/approve` trả cả phiếu), thân trả con số thay vì bản ghi (`/import` trả
    `{"created": 120}`), thân trả DANH SÁCH (duyệt hàng loạt). Cả ba ghi ra rỗng,
    tức dòng nhật ký nói "đã gọi" mà không nói "đụng vào cái gì".
    Không phải 2xx thì giữ nguyên văn, vì đó mới là thứ cần đọc — nhưng phải đi
    qua HAI lớp lọc, không phải một: `mask_payload` che theo tên khóa, rồi
    `redact_raw_inputs` bỏ giá trị thô mà thân lỗi 422 vác theo dưới khóa
    `input` (tên khóa đó chẳng nói gì nên lớp thứ nhất không bắt được).
    """
    if not raw:
        return None, ""
    try:
        parsed = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return None, ""
    if not isinstance(parsed, dict):
        return None, ""
    if 200 <= status_code < 300:
        brief: dict = {"message": parsed.get("message", "")}
        data = summarize_success(parsed.get("data"))
        if data is not None:
            brief["data"] = data
        return brief, ""
    error = parsed.get("error") if isinstance(parsed.get("error"), dict) else {}
    return redact_raw_inputs(mask_payload(parsed)), str(error.get("code") or "")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Đặt ngữ cảnh cho cả lượt gọi, rồi ghi lại lượt đó."""

    async def dispatch(self, request, call_next):
        path = request.url.path
        method = request.method
        wants_log = should_log_request(method, path)

        ctx = RequestContext(request_id=new_request_id(), source=SOURCE_API,
                             user_id=_peek_user_id(request), ip=get_client_ip(request),
                             actor_kind=ACTOR_KIND_USER)
        token = set_context(ctx)
        started = time.perf_counter()
        content_type = (request.headers.get("content-type") or "").lower()
        request_body = None
        if wants_log and method in METHODS_WITH_BODY:
            request_body = _read_request_body(request, content_type)
            if request_body is None:
                #  Starlette đệm sẵn thân đã đọc và phát lại cho endpoint
                #  (`_CachedRequest.wrapped_receive`), nên đọc ở đây KHÔNG làm
                #  endpoint nhận thân rỗng — bẫy 4 ở §6 đã được thư viện xử.
                try:
                    request_body = _parse_body(await request.body(), content_type)
                except Exception:  # noqa: BLE001 — thân hỏng thì vẫn phải chạy tiếp
                    request_body = None

        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001 — ghi vết rồi ném tiếp
            if wants_log:
                self._write(ctx, method=method, path=path, request=request,
                            request_body=request_body, status_code=500, response_body=None,
                            error_code="internal_error",
                            #  ⚠️ KHÔNG ghi thẳng `format_exc()`: SQLAlchemy dán
                            #  giá trị tham số vào vết lỗi, kể cả chuỗi băm mật
                            #  khẩu. Xem §4 của `logging_policy`.
                            error_detail=mask_error_detail(traceback.format_exc()),
                            duration_ms=int((time.perf_counter() - started) * 1000))
            self._touch(ctx)
            reset_context(token)
            raise exc

        try:
            if wants_log and not should_skip_by_result(path, response.status_code):
                response_body: dict | None = None
                error_code = ""
                if should_capture_response(method, response.status_code):
                    response, raw, oversize = await self._capture(response)
                    if oversize:
                        #  Nói rõ "to quá nên không đọc" thay vì để trống — trống
                        #  đọc ra như "endpoint này không trả gì".
                        response_body = {"_too_large": True, "size": oversize}
                    else:
                        response_body, error_code = _summarize_response(raw,
                                                                       response.status_code)
                self._write(ctx, method=method, path=path, request=request,
                            request_body=request_body, status_code=response.status_code,
                            response_body=response_body, error_code=error_code,
                            error_detail=None,
                            duration_ms=int((time.perf_counter() - started) * 1000))
        finally:
            #  ⚠️ Nằm trong `finally`, KHÔNG nằm trong `if wants_log`: dấu «lần
            #  cuối thấy thiết bị này» phải đúng kể cả với những đường không ghi
            #  nhật ký (`/api/notifications/unread-count` chẳng hạn). Ghi nhật ký
            #  và ghi phiên là hai câu hỏi khác nhau.
            self._touch(ctx)
            reset_context(token)
        return response

    def _touch(self, ctx):
        """Dập `last_seen_*` của phiên đang gọi (bao-CR-360, nửa dưới của QĐ-D).

        `ctx.session_id` do `core/auth._check_session` điền — tức chỉ những lượt
        gọi ĐÃ QUA cửa đăng nhập mới tới được đây. Lượt gọi công khai
        (`/api/auth/login`, `/refresh`) không có phiên trong ngữ cảnh, và đó là
        đúng: hai đường đó tự dập lấy, vì chỉ chúng mới biết `jti` nào.

        Kiểm tiết lưu TRƯỚC khi mở `SessionLocal()` — 99% số lượt gọi rơi vào
        trong khoảng 5 phút, mở kết nối rồi mới thấy chưa tới lúc là trả giá cho
        một việc không làm. Hỏng thì nuốt, theo luật 1 ở đầu tệp.
        """
        from app.modules.login_session.service import touch_is_due, touch_session

        if not ctx.session_id or not touch_is_due(ctx.session_id):
            return
        from app.core.database import SessionLocal

        db = None
        try:
            db = SessionLocal()
            touch_session(db, ctx.session_id, ctx.ip)
            db.commit()
        except Exception:  # noqa: BLE001
            log.warning("Không dập được last_seen cho phiên %s", ctx.session_id, exc_info=True)
            if db is not None:
                db.rollback()
        finally:
            if db is not None:
                db.close()

    async def _capture(self, response) -> tuple[Response, bytes, int]:
        """Đọc thân trả về nếu là JSON; thứ khác trả nguyên response cũ.

        Số thứ ba là **cỡ thân bị bỏ qua vì quá trần** (0 nếu không bỏ qua) —
        phân biệt "không đọc được" với "đọc rồi, rỗng".
        """
        content_type = (response.headers.get("content-type") or "").lower()
        if not content_type.startswith(CAPTURABLE_CONTENT_TYPES):
            return response, b"", 0
        try:
            length = int(response.headers.get("content-length") or 0)
        except ValueError:
            length = 0
        if length > MAX_CAPTURE_BYTES:
            return response, b"", length
        chunks = [chunk async for chunk in response.body_iterator]
        raw = b"".join(chunks)
        rebuilt = Response(content=raw, status_code=response.status_code,
                           headers=dict(response.headers), media_type=response.media_type)
        #  Giữ lại việc chạy sau khi trả lời (gửi mail, đẩy thông báo) — dựng
        #  response mới mà quên dòng này là chúng biến mất trong im lặng.
        rebuilt.background = response.background
        #  `content-length` KHÔNG phải lúc nào cũng có (thân chảy theo luồng), nên
        #  trần ở trên có thể trượt hẳn. Đo lại sau khi gom: tới đây thì đằng nào
        #  cũng đã đọc xong, nhưng ít ra không đem vài MB đi phân tích rồi ghi.
        if len(raw) > MAX_CAPTURE_BYTES:
            return rebuilt, b"", len(raw)
        return rebuilt, raw, 0

    def _write(self, ctx, *, method, path, request, request_body, status_code,
               response_body, error_code, error_detail, duration_ms):
        """Ghi một dòng. Hỏng thì nuốt lỗi — xem luật 1 ở đầu tệp."""
        from app.core.database import SessionLocal
        from app.modules.request_log.model import RequestLog

        db = None
        try:
            db = SessionLocal()
            db.add(RequestLog(
                request_id=ctx.request_id,
                source=ctx.source,
                user_id=ctx.user_id,
                session_id=ctx.session_id,
                ip=ctx.ip[:45],
                method=method[:8],
                path=path[:MAX_PATH],
                route=_route_pattern(path, request.scope.get("path_params") or {})[:MAX_ROUTE],
                query_string=str(request.url.query or "")[:MAX_QUERY_STRING],
                device_hash=device_hash(
                    (request.headers.get("user-agent") or "")[:MAX_USER_AGENT]),
                referer=(request.headers.get("referer") or "")[:MAX_REFERER],
                request_body=request_body,
                http_status=status_code,
                response_body=response_body,
                error_code=(error_code or "")[:60],
                error_detail=error_detail[:MAX_ERROR_DETAIL_BYTES] if error_detail else None,
                duration_ms=duration_ms,
                audit_count=ctx.audit_count,
                change_count=ctx.change_count,
            ))
            db.commit()
        except Exception:  # noqa: BLE001
            log.warning("Không ghi được tab_request_log cho %s %s", method, path, exc_info=True)
            if db is not None:
                db.rollback()
        finally:
            if db is not None:
                db.close()
