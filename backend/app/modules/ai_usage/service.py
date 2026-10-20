"""Nhận số dùng AI từ dịch vụ AI và ghi `tab_ai_usage_daily` (ai-CR-230). Có rồi thì thay, chưa có thì thêm — gom lại
một ngày bao nhiêu lần cũng ra cùng kết quả."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.logging_codes import AI_CHANNEL_LABELS, AI_CHANNEL_NONE

from .model import AiUsageDaily

MAX_ROWS = 20_000                     # một lượt đẩy (một ngày cả công ty) — chặn thân phình
MAX_MAP_KEYS = 50                     # số khóa của clients / tool_groups
COUNT_FIELDS = ("turns", "tool_calls", "denied", "errors", "drafts_created", "drafts_confirmed")


def _count(value) -> int:
    try:
        return max(0, min(int(value or 0), 10_000_000))
    except (TypeError, ValueError):
        return 0


def _counter(value) -> dict:
    if not isinstance(value, dict):
        return {}
    out = {}
    for k, v in list(value.items())[:MAX_MAP_KEYS]:
        n = _count(v)
        if n:
            out[str(k)[:100]] = n
    return out


def upsert_rows(db: Session, rows: list[dict]) -> dict:
    """Ghi các dòng số; dòng sai (thiếu ngày / người / kênh lạ) bỏ qua và đếm vào `skipped`."""
    from app.modules.user.model import User

    written = skipped = 0
    employee_of: dict[int, int] = {}
    for raw in (rows or [])[:MAX_ROWS]:
        try:
            day = date.fromisoformat(str(raw.get("day"))[:10])
            user_id = int(raw.get("user_id") or 0)
            channel = int(raw.get("channel") or 0)
        except (TypeError, ValueError, AttributeError):
            skipped += 1
            continue
        if user_id <= 0 or channel == AI_CHANNEL_NONE or channel not in AI_CHANNEL_LABELS:
            skipped += 1
            continue
        if user_id not in employee_of:
            user = db.get(User, user_id)
            employee_of[user_id] = int(getattr(user, "employee_id", 0) or 0) if user is not None else 0
        row = db.query(AiUsageDaily).filter(AiUsageDaily.day == day, AiUsageDaily.user_id == user_id,
                                            AiUsageDaily.channel == channel).first()
        if row is None:
            row = AiUsageDaily(day=day, user_id=user_id, channel=channel)
            db.add(row)
        row.employee_id = employee_of[user_id]
        for field in COUNT_FIELDS:
            setattr(row, field, _count(raw.get(field)))
        row.clients = _counter(raw.get("clients"))
        row.tool_groups = _counter(raw.get("tool_groups"))
        written += 1
    db.commit()
    return {"written": written, "skipped": skipped}
