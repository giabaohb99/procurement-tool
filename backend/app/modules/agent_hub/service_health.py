"""Sức khỏe dịch vụ AI (kh-AI2-4, O-01): đếm lỗi 5xx theo giờ và độ dài hàng đợi Celery, hiện ở màn Tổng quan Kho skill
AI / cổng MCP (`ai_overview.build`).

Đếm bằng Redis (khóa theo giờ, giữ 26 giờ) để mọi tiến trình api của dịch vụ AI cộng chung một chỗ, không thêm bảng. Redis
hỏng thì đếm mất lặng lẽ và số liệu trả `None` — sức khỏe không bao giờ được làm hỏng chính lượt gọi đang chạy.
Middleware chỉ gắn ở ứng dụng dịch vụ AI chạy tách (`app/agent_main.py`); chế độ nhúng trong ERP thì không đếm 5xx.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

log = logging.getLogger("app.agent_hub.service_health")

KEY = "agent:http5xx:{hour}"
KEEP_SECONDS = 26 * 3600
WINDOW_HOURS = 24
QUEUES = ("celery", "agent_code")       # hàng đợi mặc định + hàng đợi máy sửa mã (celery_app.task_routes)


def _redis():
    from .mcp_log import _redis as shared

    return shared()


def _hour_key(at: datetime) -> str:
    return KEY.format(hour=at.strftime("%Y%m%d%H"))


def record_5xx(now: datetime | None = None) -> None:
    try:
        r = _redis()
        key = _hour_key(now or datetime.utcnow())
        if int(r.incr(key)) == 1:
            r.expire(key, KEEP_SECONDS)
    except Exception:  # noqa: BLE001
        log.debug("agent_hub: không đếm được lỗi 5xx", exc_info=True)


def count_5xx(hours: int = WINDOW_HOURS, now: datetime | None = None) -> int | None:
    now = now or datetime.utcnow()
    try:
        values = _redis().mget([_hour_key(now - timedelta(hours=h)) for h in range(hours)])
        return sum(int(v or 0) for v in values)
    except Exception:  # noqa: BLE001
        return None


def queue_lengths() -> dict[str, int | None]:
    out: dict[str, int | None] = {}
    for q in QUEUES:
        try:
            out[q] = int(_redis().llen(q))
        except Exception:  # noqa: BLE001
            out[q] = None
    return out


def snapshot(now: datetime | None = None) -> dict:
    from app.core.config import settings

    return {"errors_5xx_24h": count_5xx(now=now), "queues": queue_lengths(),
            "counting_5xx": bool(settings.agent_is_service),
            "note": ("Lỗi 5xx đếm ở dịch vụ AI chạy tách, 24 giờ gần nhất; hàng đợi là số việc nền đang chờ máy chạy. "
                     "Số trống = không đọc được Redis.")}


async def count_server_errors(request, call_next):
    """Middleware HTTP: phản hồi ≥ 500 hoặc lỗi chưa bắt đều cộng một."""
    try:
        response = await call_next(request)
    except Exception:
        record_5xx()
        raise
    if response.status_code >= 500:
        record_5xx()
    return response
