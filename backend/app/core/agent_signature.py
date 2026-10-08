"""Chữ ký máy-nói-máy giữa ERP (nút B) và dịch vụ AI (nút A) — ai-CR-119, phase S.

Cùng khuôn với `core/sync_signature.py` (HMAC-SHA256, lệch giờ quá 5 phút thì từ chối, so bằng `compare_digest`) nhưng
khóa riêng `AGENT_SERVICE_SECRET` ở `.env` hai đầu, và ký THÊM danh tính người dùng:

    HMAC(secret, "<ts>.<method>.<path>.<user_id>.<sha256(body)>")

`X-Agent-User` = id tài khoản ERP mà lượt gọi chạy DƯỚI QUYỀN. Chiều AI → ERP: ERP tra tài khoản đó, kiểm quyền và lọc
phạm vi như mọi API khác — dịch vụ AI không có «khóa thần». Chiều ERP → AI (chuyển tiếp web): ERP đã xác thực JWT rồi mới
ký, dịch vụ AI tin danh tính trong chữ ký.
"""
from __future__ import annotations

import hashlib
import hmac
import time

from app.core.config import settings

HEADER_TS = "X-Agent-Ts"
HEADER_SIGN = "X-Agent-Sign"
HEADER_USER = "X-Agent-User"
MAX_SKEW_SEC = 300


def body_digest(body: bytes | str) -> str:
    data = body.encode("utf-8") if isinstance(body, str) else (body or b"")
    return hashlib.sha256(data).hexdigest()


def build(secret: str, ts: str, method: str, path: str, user_id: int | str, body: bytes | str) -> str:
    payload = f"{ts}.{method.upper()}.{path}.{int(user_id or 0)}.{body_digest(body)}".encode("utf-8")
    return hmac.new((secret or "").encode("utf-8"), payload, hashlib.sha256).hexdigest()


def sign_headers(method: str, path: str, body: bytes | str = b"", user_id: int = 0) -> dict[str, str]:
    """Bộ header để GỬI ĐI. Chưa khai khóa thì ném lỗi ngay thay vì ký bằng chuỗi rỗng."""
    secret = settings.AGENT_SERVICE_SECRET
    if not secret:
        raise ValueError("Chưa khai AGENT_SERVICE_SECRET — hai đầu ERP và dịch vụ AI phải cùng một khóa")
    ts = str(int(time.time()))
    return {HEADER_TS: ts, HEADER_SIGN: build(secret, ts, method, path, user_id, body), HEADER_USER: str(int(user_id or 0))}


def verify(method: str, path: str, body: bytes, headers, *, now: float | None = None) -> tuple[bool, str, int]:
    """(hợp lệ?, lý do, user_id) cho một yêu cầu NHẬN VỀ. `headers` là mapping không phân biệt hoa thường."""
    secret = settings.AGENT_SERVICE_SECRET
    if not secret:
        return False, "máy chủ chưa khai AGENT_SERVICE_SECRET", 0
    ts = str(headers.get(HEADER_TS) or "")
    sign = str(headers.get(HEADER_SIGN) or "")
    user = str(headers.get(HEADER_USER) or "0")
    if not ts.isdigit() or not sign:
        return False, "thiếu chữ ký", 0
    if abs((now or time.time()) - int(ts)) > MAX_SKEW_SEC:
        return False, "chữ ký quá hạn (lệch giờ hơn 5 phút)", 0
    if not user.lstrip("-").isdigit():
        return False, "danh tính không hợp lệ", 0
    expected = build(secret, ts, method, path, int(user), body)
    if not hmac.compare_digest(expected, sign):
        return False, "chữ ký sai", 0
    return True, "", int(user)
