"""Danh tính người dùng web ở DỊCH VỤ AI (ai-CR-119, phase S-3).

ERP đã xác thực JWT rồi ký `X-Agent-User` (`core/agent_signature.py`) khi chuyển tiếp; dịch vụ AI không có bảng tài khoản
nên chỉ kiểm chữ ký, rồi hỏi cổng B lấy hồ sơ (`erp.user_by_id`, bộ đệm 60 giây). `app.agent_main` ghi đè dependency
`get_current_user` bằng hàm này; `require(...)` giữ nguyên nhưng `user_has_permission` ở chế độ service hỏi cổng B.
"""
from __future__ import annotations

import time

from fastapi import HTTPException, Request

from app.core import agent_signature

_CACHE: dict[int, tuple[float, object]] = {}
_TTL = 60.0


async def current_user(request: Request):
    body = await request.body()
    ok, reason, user_id = agent_signature.verify(request.method, request.url.path, body, request.headers)
    if not ok:
        raise HTTPException(401, f"Yêu cầu không qua ERP ({reason})")
    if user_id <= 0:
        raise HTTPException(401, "Thiếu danh tính người dùng")
    hit = _CACHE.get(user_id)
    if hit and time.monotonic() - hit[0] < _TTL:
        return hit[1]
    from app.modules.agent_hub import erp

    try:
        user = erp.user_by_id(None, user_id)
    except erp.ErpError as e:
        raise HTTPException(503, f"Không hỏi được ERP: {e}") from None
    if user is None or not user.is_active:
        raise HTTPException(401, "Tài khoản không tồn tại hoặc đã bị khóa")
    _CACHE[user_id] = (time.monotonic(), user)
    return user
