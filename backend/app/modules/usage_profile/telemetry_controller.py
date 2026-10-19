"""POST /api/telemetry/ui-events — thu lô sự kiện giao diện (duoc-CR-641, phase 03).

- Mọi người đã đăng nhập đều gửi được (không `require(entity)`): chỉ ghi sự kiện của CHÍNH mình,
  `user_id`/`session_id` lấy từ token + phiên, không bao giờ từ body.
- FE dùng `fetch(..., {keepalive: true})` kèm `Authorization: Bearer` (sendBeacon không mang được
  header nên không dùng). Đường này KHÔNG vào `tab_request_log` (`core/logging_policy.SKIP_PATH_PREFIXES`):
  mỗi lô đẻ một dòng nhật ký thì bảng nhật ký phình vô nghĩa.
- Công tắc tắt: nhận và bỏ (204), không ghi gì.
- Thân > 64 KB → 413 TRƯỚC khi parse JSON: đọc `request.stream()` với trần cứng 64 KB + 1 byte (không tin `Content-Length`,
  thân chunked cũng bị chặn). Giới hạn tần suất 30 lô/phút theo user (không theo IP:
  văn phòng chung NAT).
"""
import logging

from pydantic import ValidationError

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.limiter import limiter
from app.core.request_context import get_context
from app.core.request_middleware import _peek_user_id
from app.core.client_ip import get_client_ip
from app.core.response import success

from . import telemetry_service as service
from .telemetry_schema import MAX_BODY_BYTES, UiEventBatch

log = logging.getLogger("app.usage_profile.telemetry")

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


def _rate_key(request: Request) -> str:
    uid, _expired = _peek_user_id(request)
    return f"u{uid}" if uid else get_client_ip(request)


async def _read_batch(request: Request) -> UiEventBatch:
    """Đọc thân với trần cứng MAX_BODY_BYTES rồi mới parse JSON (không để FastAPI nạp cả thân vào RAM)."""
    try:
        declared = int(request.headers.get("content-length") or 0)
    except ValueError:
        declared = 0
    too_big = HTTPException(413, f"Lô sự kiện quá lớn (tối đa {MAX_BODY_BYTES // 1024} KB)")
    if declared > MAX_BODY_BYTES:
        raise too_big
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > MAX_BODY_BYTES:   # dừng đọc ngay, không cần biết thân còn dài bao nhiêu
            raise too_big
        chunks.append(chunk)
    try:
        return UiEventBatch.model_validate_json(b"".join(chunks))
    except ValidationError as exc:
        first = exc.errors(include_url=False, include_context=False, include_input=False)[0]
        loc = ".".join(str(p) for p in first["loc"])
        raise HTTPException(422, f"Lô sự kiện không hợp lệ ({loc}: {first['msg']})")


@router.post("/ui-events")
@limiter.limit("30/minute", key_func=_rate_key)
def post_ui_events(request: Request, payload: UiEventBatch = Depends(_read_batch),
                   user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not service.tracking_enabled():
        return Response(status_code=204)
    ctx = get_context()
    session_id = ctx.session_id if ctx else None
    try:
        accepted = service.store_batch(db, payload, user.id, session_id)
    except Exception:  # noqa: BLE001 — thu thập hỏng không được làm hỏng màn người dùng đang dùng
        db.rollback()
        log.exception("Không ghi được lô sự kiện giao diện của user %s", user.id)
        raise HTTPException(500, "Không ghi được lô sự kiện")
    return success({"accepted": accepted})
