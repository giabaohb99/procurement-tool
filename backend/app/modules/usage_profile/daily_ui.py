"""Số liệu từ sự kiện giao diện (`tab_ui_event`) của MỘT người trong MỘT ngày (thuần) — duoc-CR-641, phase 02."""
from app.core.usage_codes import UiEventType

MAX_SCREENS = 40


def ui_columns(events: list) -> dict:
    """events: [(occurred_at, event_type, route, form_key, duration_ms, result_count)] của một người."""
    views = dwell = searches = empty = errors = 0
    first_route, first_at = "", None
    screens: dict[str, list[int]] = {}
    forms: dict[str, list[int]] = {}
    for occurred, etype, route, form, duration, result in sorted(events, key=lambda e: e[0]):
        if etype == UiEventType.PAGE_VIEW:
            views += 1
            screens.setdefault(route, [0, 0, 0])[0] += 1
            if first_at is None:
                first_route, first_at = route, occurred
        elif etype == UiEventType.PAGE_LEAVE:
            dwell += duration
            screens.setdefault(route, [0, 0, 0])[1] += duration
        elif etype == UiEventType.SEARCH:
            searches += 1
            empty += 1 if result == 0 else 0
        elif etype == UiEventType.CLIENT_ERROR:
            errors += 1
        elif form and etype in (UiEventType.FORM_OPEN, UiEventType.FORM_SUBMIT, UiEventType.FORM_ABANDON):
            slot = forms.setdefault(str(form), [0, 0, 0, 0])   # [mở, gửi, bỏ, tổng ms các lần gửi]
            if etype == UiEventType.FORM_OPEN:
                slot[0] += 1
            elif etype == UiEventType.FORM_SUBMIT:
                slot[1] += 1
                slot[3] += duration
            else:
                slot[2] += 1
    return {"page_views": views, "dwell_ms": dwell, "searches": searches, "searches_empty": empty,
            "client_errors": errors, "first_route": first_route, "forms": forms, "_screens_ui": screens}


def merge_screens(api: dict, ui: dict) -> dict:
    """Gộp `[views, dwell_ms, api_calls]` của hai nguồn; giữ top `MAX_SCREENS` theo (views, api_calls)."""
    merged: dict[str, list[int]] = {}
    for part in (api, ui):
        for route, (v, d, a) in part.items():
            slot = merged.setdefault(route, [0, 0, 0])
            slot[0] += v
            slot[1] += d
            slot[2] += a
    top = sorted(merged.items(), key=lambda kv: (kv[1][0], kv[1][2]), reverse=True)[:MAX_SCREENS]
    return dict(top)
