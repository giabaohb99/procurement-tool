"""Cửa sổ ngày VN và các phép đổi giờ (thuần) cho phần gom ngày (duoc-CR-641, phase 02).

Mọi `created_at` trong DB là UTC naive; một NGÀY VN `D` = [D 00:00 VN, D+1 00:00 VN) = [D−1 17:00 UTC, D 17:00 UTC).
"""
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit

from app.core.export_xlsx import VN_OFFSET

from .route_pattern import normalize_route


def vn_day_bounds(day: date) -> tuple[datetime, datetime]:
    """`[utc_from, utc_to)` của ngày VN `day`."""
    start = datetime(day.year, day.month, day.day) - VN_OFFSET
    return start, start + timedelta(days=1)


def to_vn(dt_utc: datetime) -> datetime:
    return dt_utc + VN_OFFSET


def minute_of_day(dt_utc: datetime) -> int:
    """Phút-trong-ngày theo giờ VN (0..1439)."""
    v = to_vn(dt_utc)
    return v.hour * 60 + v.minute


def vn_hour(dt_utc: datetime) -> int:
    return to_vn(dt_utc).hour


def vn_date(dt_utc: datetime) -> date:
    return to_vn(dt_utc).date()


def referer_to_pattern(referer: str | None) -> str | None:
    """`https://erp.x.vn/procurement/purchase-orders/129?q=abc` → `/procurement/purchase-orders/:id`.

    Chỉ lấy PATH (query có thể chứa `q=` từ khóa tìm kiếm). Rỗng → None (bỏ qua).
    """
    if not referer:
        return None
    try:
        path = urlsplit(referer).path
    except ValueError:
        return None
    if not path or path == "/":
        return None
    return normalize_route(path)
