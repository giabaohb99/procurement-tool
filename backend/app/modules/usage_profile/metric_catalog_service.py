"""`GET /metrics` — danh mục chỉ số kèm trạng thái đo THỰC TẾ của tuần snapshot mới nhất (duoc-CR-649).

Đúng 2 truy vấn bất kể số người/tuần: (1) tối đa 8 tuần snapshot mới nhất · (2) cột `metrics` của mọi snapshot các tuần đó
(duoc-CR-651: thêm `histogram` của tuần mới nhất + `trend` trung vị theo tuần để vẽ biểu đồ). Gộp trong bộ nhớ
(≤ vài trăm người × ~55 khóa). Chỉ trả KHÓA và MÃ — nhãn/mô tả tiếng Việt nằm ở giao diện (luật R2).
`unmeasured_reason` = mã `UnmeasuredReason` hay gặp nhất khi KHÔNG ai đo được khóa đó (None nếu có người đo được).
"""
import json
from collections import Counter, defaultdict
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.usage_codes import PeriodKind

from .metric_chart_service import TREND_WEEKS, build_histogram, build_trend
from .metric_catalog import DEFERRED_METRICS, METRIC_CATALOG
from .metric_stats import median, rnd
from .model import UserUsageSnapshot


def _as_dict(raw) -> dict:
    """`json_extract` trả chuỗi JSON (MySQL/SQLite) hoặc dict (driver tự giải) — chuẩn hóa về dict."""
    if raw is None:
        return {}
    if isinstance(raw, (bytes, str)):
        raw = json.loads(raw)
    return raw if isinstance(raw, dict) else {}


def _collect(rows) -> tuple[dict[str, list[float]], dict[str, Counter], int]:
    """MỘT lượt qua các snapshot của một tuần: giá trị đo được theo khóa + lý do chưa đo theo khóa + số người."""
    values: dict[str, list[float]] = defaultdict(list)
    reasons: dict[str, Counter] = defaultdict(Counter)
    n = 0
    for metrics_raw, unmeasured_raw in rows:
        n += 1
        for key, cell in _as_dict(metrics_raw).items():
            v = cell.get("v") if isinstance(cell, dict) else None
            if v is not None:
                values[key].append(float(v))
        for key, reason in _as_dict(unmeasured_raw).items():
            if reason is not None:
                reasons[key][reason] += 1
    return values, reasons, n


def list_metrics(db: Session) -> dict:
    S = UserUsageSnapshot
    week_col = S.period_start
    #  (1) tối đa 8 tuần có snapshot gần nhất · (2) cột `metrics` của mọi snapshot trong các tuần đó.
    weeks = [w for (w,) in db.execute(
        select(week_col).where(S.period_kind == int(PeriodKind.WEEK)).distinct().order_by(week_col.desc()).limit(TREND_WEEKS)
    ).all()]
    #  Chỉ rút hai nhánh `metrics` + `unmeasured` ngay trong SQL — bỏ `lists` (heatmap, top màn…) vốn chiếm phần lớn JSON,
    #  rồi duyệt MỖI snapshot một lần (trước đây 58 khóa × mọi snapshot ≈ 64k lượt tra, ~1 giây — duoc-CR-651).
    rows_by_week: dict = {w: [] for w in weeks}
    if weeks:
        q = select(week_col, func.json_extract(S.metrics, "$.metrics"), func.json_extract(S.metrics, "$.unmeasured")) \
            .where(S.period_kind == int(PeriodKind.WEEK), week_col.in_(weeks))
        for w, m, u in db.execute(q).all():
            rows_by_week[w].append((m, u))
    collected = {w: _collect(rows) for w, rows in rows_by_week.items()}
    week = weeks[0] if weeks else None
    latest_values, latest_reasons, total = collected[week] if week else ({}, {}, 0)
    ordered = sorted(weeks)
    items = []
    for key, meta in METRIC_CATALOG.items():
        values = latest_values.get(key, [])
        reasons = latest_reasons.get(key)
        trend = build_trend([(w.isoformat(), collected[w][0].get(key, [])) for w in ordered])
        items.append({
            "key": key, "section": meta.section, "unit": meta.unit, "phase": meta.phase, "direction": meta.direction,
            "measured_users": len(values), "total_users": total,
            "company_median": rnd(median(values)) if values else None,
            "unmeasured_reason": (reasons.most_common(1)[0][0] if reasons and not values else None) if total else None,
            "histogram": build_histogram(meta.unit, values),
            "trend": trend if values or any(t["measured"] for t in trend) else [],
        })
    return {"week": week.isoformat() if isinstance(week, date) else None, "metrics": items,
            "deferred": list(DEFERRED_METRICS)}
