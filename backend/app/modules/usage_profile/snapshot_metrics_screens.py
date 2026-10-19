"""Chỉ số màn hình, biểu mẫu, phiếu theo ngày — tính từ `tab_usage_daily` của một người (duoc-CR-641, phase 04).

Chỉ số pha 2 (cần sự kiện giao diện) mà chưa thu thập → `unmeasured` mã 1, không ghi 0.
"""
import calendar
from collections import Counter, defaultdict
from datetime import date, timedelta

from app.core.usage_codes import UnmeasuredReason as Why

from .metric_partial import Partial
from .metric_stats import median, ratio

SOURCE_UI, SOURCE_API = 1, 2   # lists.screens_source
MIN_FOR_RATE = 3
MIN_SEARCHES = 5
MIN_CREATED_FOR_MONTH_END = 10
_FORM_SUFFIXES = ("/new", "/create", "/edit")


def is_list_screen(route: str) -> bool:
    return ":id" not in route and not route.endswith(_FORM_SUFFIXES)


def _sum_docs(rows) -> dict[str, Counter]:
    out: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        for entity, verbs in (r.docs or {}).items():
            out[entity].update(verbs)
    return out


def month_end_share(dated_docs: list[tuple[date, dict]]) -> tuple[float | None, int]:
    created = last3 = 0
    for day, docs in dated_docs:
        n = sum((v or {}).get("c", 0) for v in (docs or {}).values())
        created += n
        if day.day >= calendar.monthrange(day.year, day.month)[1] - 2:
            last3 += n
    return ratio(last3, created), created


def screens_metrics(rows: list, ui_collected: bool) -> Partial:
    p = Partial()
    views = sum(r.page_views for r in rows)
    screens: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for r in rows:
        for route, (v, d, a) in (r.screens or {}).items():
            slot = screens[route]
            slot[0] += v
            slot[1] += d
            slot[2] += a
    use_ui = views > 0
    order = sorted(screens.items(), key=lambda kv: (kv[1][0], kv[1][2]) if use_ui else (kv[1][2], kv[1][0]),
                   reverse=True)
    p.lists["top_screens"] = [[k, v[0], v[1], v[2]] for k, v in order[:10]]
    p.lists["module_time"] = [[k, v[1]] for k, v in sorted(screens.items(), key=lambda kv: -kv[1][1])[:10] if v[1]]
    p.lists["screens_source"] = SOURCE_UI if use_ui else SOURCE_API
    firsts = [(r.day, r.first_route) for r in sorted(rows, key=lambda x: x.day) if r.first_route]
    mode = Counter(f for _, f in firsts).most_common(1)
    changes = sum(1 for a, b in zip(firsts, firsts[1:]) if a[1] != b[1])
    p.lists["first_screen"] = [mode[0][0], mode[0][1], changes] if mode else []

    why = Why.NOT_COLLECTED
    p.put("page_views", views if ui_collected else None, why)
    p.put("screen_dwell_avg", ratio(sum(r.dwell_ms for r in rows), views) if ui_collected else None, why)
    p.put("distinct_screens_30d", sum(1 for v in screens.values() if v[0] > 0) if ui_collected else None, why)
    p.put("help_views", sum(v[0] for k, v in screens.items() if k.startswith("/help")) if ui_collected else None, why)
    list_views = sum(v[0] for k, v in screens.items() if is_list_screen(k))
    p.put("export_per_list_view",
          ratio(sum(r.exports for r in rows), list_views) if ui_collected else None,
          why if not ui_collected else Why.NOT_APPLICABLE)

    searches = sum(r.searches for r in rows)
    p.put("search_empty_rate",
          ratio(sum(r.searches_empty for r in rows), searches) if ui_collected and searches >= MIN_SEARCHES else None,
          why if not ui_collected else Why.BELOW_THRESHOLD)

    reports: Counter = Counter()
    forbidden: Counter = Counter()
    for r in rows:
        reports.update(r.reports or {})
        forbidden.update(r.forbidden_routes or {})
    p.lists["reports"] = [[int(k), n] for k, n in reports.most_common(10)]
    p.lists["top_403_routes"] = [[k, n] for k, n in forbidden.most_common(5)]
    p.put("reports_opened", sum(reports.values()))
    p.counts["views"] = views
    p.counts["list_views"] = list_views
    return p


def docs_forms_metrics(rows: list, old_rows: list, ui_collected: bool) -> Partial:
    p = Partial()
    docs = _sum_docs(rows)
    p.lists["docs"] = {e: dict(c) for e, c in docs.items()}
    created = sum(c.get("c", 0) for c in docs.values())
    submitted = sum(c.get("s", 0) for c in docs.values())
    p.put("docs_created", created)
    p.put("docs_submitted", submitted)
    p.counts.update({"docs_created": created, "docs_submitted": submitted})

    opens = sum(v[0] for r in rows for v in (r.forms or {}).values())
    submits = sum(v[1] for r in rows for v in (r.forms or {}).values())
    abandons = sum(v[2] for r in rows for v in (r.forms or {}).values())
    day_means = []
    for r in rows:
        n = sum(v[1] for v in (r.forms or {}).values())
        if n:
            day_means.append(sum(v[3] for v in (r.forms or {}).values()) / n)
    why = Why.NOT_COLLECTED if not ui_collected else Why.BELOW_THRESHOLD
    p.put("form_submit_p50_ms", median(day_means) if ui_collected and submits >= MIN_FOR_RATE else None, why)
    p.put("form_abandon_rate", ratio(abandons, opens) if ui_collected and opens >= MIN_FOR_RATE else None, why)

    cutoff = max((r.day for r in rows), default=date.today()) - timedelta(days=91)
    dated = [(r.day, r.docs) for r in rows] + [(d, docs_) for _u, d, _x, docs_ in old_rows if d > cutoff]
    share, total_created = month_end_share(dated)
    p.put("month_end_create_share", share if total_created >= MIN_CREATED_FOR_MONTH_END else None,
          Why.BELOW_THRESHOLD)
    done = sum(r.on_behalf_done for r in rows)
    received = sum(r.on_behalf_received for r in rows)
    own = max(0, created - done)
    p.put("proxy_share", ratio(received, own + received))
    p.counts["proxy_docs"] = own + received
    return p
