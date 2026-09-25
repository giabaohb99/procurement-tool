"""Giờ Việt Nam cho những gì bot NÓI với đại ca (ai-CR-020).

Container của stack bot và MySQL đều chạy UTC (đo 23/09/2026: 05:00 trong container khi máy đại
ca là 12:00). Mọi mốc thời gian trong sổ (`created_at`, `started_at`, `scheduled_for`…) vì thế là
giờ UTC không kèm múi. Chỗ nào in giờ cho đại ca đọc, hoặc đọc giờ đại ca nhắn («hẹn 14:30»),
phải đổi qua đây — trước ai-CR-020 bot hẹn «14:30» thành 14:30 UTC, tức 21:30 giờ Việt Nam.

Việt Nam không đổi giờ theo mùa nên cộng cứng 7 tiếng là đúng, khỏi phụ thuộc gói tzdata.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

LOCAL_OFFSET = timedelta(hours=7)


def now_utc() -> datetime:
    """Giờ UTC không kèm múi — cùng kiểu với các cột thời gian trong sổ."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def now_local() -> datetime:
    return now_utc() + LOCAL_OFFSET


def to_local(dt: datetime | None) -> datetime | None:
    return dt + LOCAL_OFFSET if dt is not None else None


def to_utc(dt: datetime) -> datetime:
    return dt - LOCAL_OFFSET


def fmt_local(dt: datetime | None, fmt: str = "%H:%M %d/%m") -> str:
    return to_local(dt).strftime(fmt) if dt is not None else ""
