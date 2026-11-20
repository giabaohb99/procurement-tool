"""Đổi số `Decimal` sang số JSON (4 số lẻ) cho đầu ra của màn Giá bao bì (duoc-CR-784) — một chỗ cho cả ba dịch vụ."""
from datetime import date
from decimal import Decimal


def num(value: Decimal | int | float | None, places: int = 4) -> float | None:
    """Số hoặc None; làm tròn `places` số lẻ, bỏ đuôi `.0` thừa khi giá trị nguyên."""
    if value is None:
        return None
    return round(float(value), places)


def iso(value: date | None) -> str | None:
    return value.isoformat() if value else None
