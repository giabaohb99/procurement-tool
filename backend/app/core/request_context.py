"""NGỮ CẢNH CỦA MỘT LƯỢT GỌI — sợi dây nối ba lớp nhật ký (bao-CR-312, P1).

Vì sao là `ContextVar` chứ không phải tham số hàm: hôm nay có **213 lời gọi
`record(...)` nằm rải trong 54 tệp**. Truyền ngữ cảnh bằng tham số nghĩa là sửa
đủ 213 chỗ ngay lần này, và mỗi lời gọi viết thêm sau này lại phải nhớ truyền —
quên một chỗ thì dòng nhật ký đó mất IP, mất `request_id`, và không ai biết cho
tới lúc cần tra. Middleware đặt một lần ở đầu request, `record(...)` và tầng ORM
(P4) tự đọc; thêm cột ngữ cảnh nào về sau cũng không ai phải sửa lời gọi.

`ContextVar` chạy đúng cho cả `async def` lẫn `def`: FastAPI đẩy hàm `def` sang
threadpool bằng `anyio.to_thread`, thứ **chép ngữ cảnh** sang luồng con.

Việc nền Celery và script chạy tay **không đi qua middleware**, nên phải tự mở
ngữ cảnh bằng `open_context(...)` nếu muốn dòng nhật ký của chúng có `source`
và `actor_kind` đúng. Không mở cũng không sao: `record(...)` chịu được ngữ cảnh
rỗng, chỉ là dòng đó không có `request_id`.

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §6.
"""
import uuid
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field

from app.core.logging_codes import ACTOR_KIND_SYSTEM, ACTOR_KIND_USER, SOURCE_API


@dataclass
class RequestContext:
    """Thứ mà mọi dòng nhật ký sinh ra trong một lượt gọi đều cần biết."""

    #  QĐ-B (§4.5): giữ bản NHỊ PHÂN 16 byte, đổi sang chuỗi lúc trả ra API.
    request_id: bytes = b""
    source: int = SOURCE_API
    user_id: int = 0
    session_id: int | None = None  # P3 mới có bảng phiên để mà điền
    ip: str = ""
    actor_kind: int = ACTOR_KIND_USER
    #  Hai số đếm dòng con, để `tab_request_log` biết có gì đáng mở ra xem.
    audit_count: int = 0
    change_count: int = 0
    #  Bộ đệm của lớp ORM (P4) — khai sẵn để P4 không phải đổi kiểu dữ liệu này.
    changes: list = field(default_factory=list)


_current: ContextVar[RequestContext | None] = ContextVar("request_context", default=None)


def new_request_id() -> bytes:
    """Mã một lượt gọi, dạng 16 byte đúng kiểu cột `BINARY(16)` (QĐ-B)."""
    return uuid.uuid4().bytes


def request_id_text(raw: bytes | None) -> str:
    """Đổi sang chuỗi 36 ký tự có gạch — dạng người đọc, dạng API trả ra.

    ⚠️ Tra tay dưới DB thì phải dùng `UUID_TO_BIN('…')` / `BIN_TO_UUID(col)`;
    gõ thẳng chuỗi vào `WHERE request_id = '3f1c…'` sẽ ra **rỗng chứ không báo
    lỗi**, rất dễ tưởng là mất dữ liệu.
    """
    if not raw:
        return ""
    try:
        return str(uuid.UUID(bytes=bytes(raw)))
    except (ValueError, TypeError):
        return ""


def get_context() -> RequestContext | None:
    return _current.get()


def set_context(ctx: RequestContext | None) -> Token:
    return _current.set(ctx)


def reset_context(token: Token) -> None:
    _current.reset(token)


@contextmanager
def open_context(source: int, user_id: int = 0, actor_kind: int = ACTOR_KIND_SYSTEM,
                 ip: str = ""):
    """Mở ngữ cảnh cho thứ KHÔNG đi qua middleware (Celery, script, seed)."""
    ctx = RequestContext(request_id=new_request_id(), source=source, user_id=user_id,
                         actor_kind=actor_kind, ip=ip)
    token = set_context(ctx)
    try:
        yield ctx
    finally:
        reset_context(token)


def current_request_id() -> bytes | None:
    ctx = _current.get()
    return ctx.request_id if ctx and ctx.request_id else None


def current_request_id_text() -> str:
    return request_id_text(current_request_id())


def bump_audit_count(step: int = 1) -> None:
    """Đếm dòng audit của lượt này. Gọi từ `core/audit.record(...)`."""
    ctx = _current.get()
    if ctx is not None:
        ctx.audit_count += step
