"""Ghi lô sự kiện giao diện vào `tab_ui_event` (duoc-CR-641, phase 03).

Chuẩn hóa LẠI route ở server dù FE đã chuẩn hóa (FE lỗi cũng không để lọt id). Một lô = MỘT câu
INSERT nhiều dòng. `occurred_at = now − clamp(age_ms, 0, 24 giờ)` — không tin đồng hồ máy khách.
"""
import re
from datetime import datetime, timedelta

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.usage_codes import UiEventType

from .model import UiEvent
from .route_pattern import canonical_route, normalize_route
from .telemetry_schema import MAX_AGE_MS, MAX_UI_ACTIONS_PER_BATCH, UiEventBatch

META_NAME_MAX = 60
META_MESSAGE_MAX = 200


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_QUERY = re.compile(r"\?\S+")
_LONG_DIGITS = re.compile(r"\d{6,}")


def scrub_message(text: str, limit: int = META_MESSAGE_MAX) -> str:
    """Làm sạch thông điệp lỗi do client gửi — SERVER là bên quyết định (FE cũng che nhưng không tin được).

    Che email, query string (`?q=...`) và dãy ≥ 6 chữ số (SĐT, CCCD, mã phiếu dài), rồi cắt độ dài.
    Thứ tự: query trước để `?email=a@b.c` bị che trọn.
    """
    out = _QUERY.sub("?[q]", text or "")
    out = _EMAIL.sub("[email]", out)
    out = _LONG_DIGITS.sub("[num]", out)
    return out[:limit]


def tracking_enabled() -> bool:
    """Công tắc `usage_tracking_enabled` (mặc định BẬT; tắt trên màn Cấu hình hệ thống)."""
    return bool(app_settings.get("usage_tracking_enabled"))


def build_rows(batch: UiEventBatch, user_id: int, session_id: int | None,
               now: datetime | None = None) -> list[dict]:
    now = now or datetime.utcnow()
    rows: list[dict] = []
    n_actions = 0
    for ev in batch.events:
        if ev.type == int(UiEventType.UI_ACTION):
            n_actions += 1
            if n_actions > MAX_UI_ACTIONS_PER_BATCH:
                continue   # trần/lô (duoc-CR-654): bỏ phần thừa, không từ chối cả lô
        is_search = ev.type == int(UiEventType.SEARCH)
        is_error = ev.type == int(UiEventType.CLIENT_ERROR)
        meta = None
        if is_error and ev.error is not None:
            meta = {"n": scrub_message(ev.error.name, META_NAME_MAX), "m": scrub_message(ev.error.message)}
        rows.append({
            "created_at": now,
            "occurred_at": now - timedelta(milliseconds=min(max(ev.age_ms, 0), MAX_AGE_MS)),
            "user_id": int(user_id),
            "session_id": session_id,
            "app": batch.app,
            "tab_key": ev.tab_key,
            "event_type": ev.type,
            #  bao-CR-649: chuẩn hóa rồi quy route app cũ về route v2 (cùng màn → cùng tên chức năng trên báo cáo)
            "route_pattern": canonical_route(normalize_route(ev.route), batch.app),
            "form_key": ev.form,
            "action_key": ev.action,
            "duration_ms": ev.duration_ms,
            "result_count": ev.result_count if is_search else None,
            "meta": meta,
        })
    return rows


def store_batch(db: Session, batch: UiEventBatch, user_id: int, session_id: int | None) -> int:
    """Ghi cả lô trong MỘT câu INSERT; trả số dòng đã ghi."""
    rows = build_rows(batch, user_id, session_id)
    db.execute(insert(UiEvent.__table__), rows)
    db.commit()
    return len(rows)
