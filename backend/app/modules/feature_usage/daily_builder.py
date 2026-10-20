"""Gom MỘT ngày VN từ `tab_ui_event` vào `tab_feature_usage_daily` (duoc-CR-655, D0c) — idempotent.

Đúng 2 truy vấn nguồn, cố định bất kể số người: (1) GROUP BY sự kiện giao diện, (2) phòng ban / pháp nhân của từng
người ngày đó lấy từ `tab_usage_daily` (job gom ngày 04:30 chạy TRƯỚC job này 04:45). Ghi: DELETE ngày rồi bulk INSERT.
"""
from collections import defaultdict
from datetime import date

from sqlalchemy import case, delete, func, insert, select
from sqlalchemy.orm import Session

from app.core.usage_codes import FeatureKind as K
from app.core.usage_codes import UiEventType as E
from app.modules.usage_profile.daily_builder import guard_day_age
from app.modules.usage_profile.daily_window import vn_day_bounds
from app.modules.usage_profile.model import UiEvent, UsageDaily

from .model import FeatureUsageDaily

_COUNTS = ("uses", "completes", "abandons", "fails", "duration_ms")


def load_events(db: Session, day: date) -> list[tuple]:
    """[(user_id, event_type, action_key, form_key, route, n, Σduration_ms, n_không_kết_quả)] của ngày."""
    lo, hi = vn_day_bounds(day)
    empty = func.sum(case((UiEvent.result_count == 0, 1), else_=0))
    return [tuple(r) for r in db.execute(
        select(UiEvent.user_id, UiEvent.event_type, UiEvent.action_key, UiEvent.form_key, UiEvent.route_pattern,
               func.count(), func.coalesce(func.sum(UiEvent.duration_ms), 0), func.coalesce(empty, 0))
        .where(UiEvent.occurred_at >= lo, UiEvent.occurred_at < hi, UiEvent.user_id > 0)
        .group_by(UiEvent.user_id, UiEvent.event_type, UiEvent.action_key, UiEvent.form_key,
                  UiEvent.route_pattern)).all()]


def load_org(db: Session, day: date) -> dict[int, tuple[int, int]]:
    return {r[0]: (r[1] or 0, r[2] or 0) for r in db.execute(
        select(UsageDaily.user_id, UsageDaily.company_id, UsageDaily.department_id).where(UsageDaily.day == day))}


def build_rows(day: date, events: list[tuple], org: dict[int, tuple[int, int]]) -> list[dict]:
    """Thuần: gộp sự kiện đã GROUP BY thành dòng `(user, kind, code, route)`. Sự kiện lạ (PAGE_LEAVE không route…) bỏ qua."""
    acc: dict[tuple, dict] = defaultdict(lambda: dict.fromkeys(_COUNTS, 0))
    for uid, etype, action, form, route, n, dur, empty in events:
        route = route or ""
        if etype == E.UI_ACTION and action:
            slot = acc[(uid, K.ACTION, action, route)]
            slot["uses"] += n
        elif etype in (E.FORM_OPEN, E.FORM_SUBMIT, E.FORM_ABANDON) and form:
            slot = acc[(uid, K.FORM, form, "")]
            if etype == E.FORM_OPEN:
                slot["uses"] += n
            elif etype == E.FORM_SUBMIT:
                slot["completes"] += n
                slot["duration_ms"] += dur
            else:
                slot["abandons"] += n
        elif etype == E.PAGE_VIEW:
            acc[(uid, K.SCREEN, 0, route)]["uses"] += n
        elif etype == E.PAGE_LEAVE:
            acc[(uid, K.SCREEN, 0, route)]["duration_ms"] += dur
        elif etype == E.SEARCH:
            slot = acc[(uid, K.SEARCH, 0, route)]
            slot["uses"] += n
            slot["fails"] += empty
        elif etype == E.CLIENT_ERROR:
            acc[(uid, K.CLIENT_ERROR, 0, route)]["uses"] += n
    rows = []
    for (uid, kind, code, route), c in acc.items():
        company, dept = org.get(uid, (0, 0))
        rows.append({"day": day, "user_id": uid, "company_id": company, "department_id": dept,
                     "kind": int(kind), "code": int(code), "route": route[:120], **c})
    return rows


def aggregate_day(db: Session, day: date, force: bool = False) -> int:
    """Gom một ngày; trả số dòng ghi. Từ chối ngày quá hạn giữ sự kiện thô (cùng luật `usage_profile`)."""
    guard_day_age(day, force)
    rows = build_rows(day, load_events(db, day), load_org(db, day))
    db.execute(delete(FeatureUsageDaily).where(FeatureUsageDaily.day == day))
    if rows:
        db.execute(insert(FeatureUsageDaily.__table__), rows)
    db.commit()
    return len(rows)
