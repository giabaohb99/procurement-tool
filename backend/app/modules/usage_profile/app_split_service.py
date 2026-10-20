"""Sự kiện giao diện tách theo ỨNG DỤNG gửi (bao-CR-649) — đọc thẳng `tab_ui_event` (giữ 90 ngày).

Số gom ngày (`tab_usage_daily`) cố ý GIỮ NGUYÊN, cộng cả hai app: hồ sơ một người là một người, dù làm trên
thumua hay ERP v2. Màn này chỉ trả lời «phòng Thu mua đang làm ở app nào, bao nhiêu» để biết bộ thu bên thumua có
dữ liệu và để chủ sản phẩm quyết tắt app cũ lúc nào. Chỉ số + mã, không có chữ người dùng.
"""
from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.usage_codes import UI_APP_LABELS, UiApp, UiEventType

from .daily_window import vn_day_bounds
from .model import UiEvent


def _count(event_type: UiEventType):
    return func.sum(case((UiEvent.event_type == int(event_type), 1), else_=0))


def split_by_app(db: Session, date_from: date, date_to: date) -> dict:
    """Một dòng mỗi app (kể cả app chưa có sự kiện: số 0) trong kỳ [date_from, date_to] theo ngày VN."""
    lo, _ = vn_day_bounds(date_from)
    _, hi = vn_day_bounds(date_to)
    rows = db.execute(
        select(UiEvent.app, func.count(UiEvent.id), func.count(func.distinct(UiEvent.user_id)),
               _count(UiEventType.PAGE_VIEW), _count(UiEventType.FORM_OPEN), _count(UiEventType.FORM_SUBMIT),
               _count(UiEventType.FORM_ABANDON), _count(UiEventType.SEARCH), _count(UiEventType.CLIENT_ERROR))
        .where(UiEvent.occurred_at >= lo, UiEvent.occurred_at < hi)
        .group_by(UiEvent.app)
    ).all()
    by_app = {int(r[0]): r for r in rows}
    items = []
    for app in UiApp:
        r = by_app.get(int(app))
        items.append({
            "app": int(app), "label": UI_APP_LABELS[app],
            "events": int(r[1]) if r else 0, "users": int(r[2]) if r else 0,
            "page_views": int(r[3] or 0) if r else 0, "form_open": int(r[4] or 0) if r else 0,
            "form_submit": int(r[5] or 0) if r else 0, "form_abandon": int(r[6] or 0) if r else 0,
            "searches": int(r[7] or 0) if r else 0, "client_errors": int(r[8] or 0) if r else 0,
        })
    return {"date_from": date_from.isoformat(), "date_to": date_to.isoformat(), "items": items}
