"""`GET /metrics` — danh mục chỉ số kèm trạng thái đo THỰC TẾ của tuần snapshot mới nhất (duoc-CR-649).

Đúng 2 truy vấn bất kể số người: (1) tuần mới nhất · (2) cột `metrics` của mọi snapshot tuần đó. Gộp trong bộ nhớ
(≤ vài trăm người × ~55 khóa). Chỉ trả KHÓA và MÃ — nhãn/mô tả tiếng Việt nằm ở giao diện (luật R2).
`unmeasured_reason` = mã `UnmeasuredReason` hay gặp nhất khi KHÔNG ai đo được khóa đó (None nếu có người đo được).
"""
from collections import Counter
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.usage_codes import PeriodKind

from .metric_catalog import DEFERRED_METRICS, METRIC_CATALOG
from .metric_stats import median, rnd
from .model import UserUsageSnapshot


def list_metrics(db: Session) -> dict:
    S = UserUsageSnapshot
    week = db.execute(select(func.max(S.period_start)).where(S.period_kind == int(PeriodKind.WEEK))).scalar()
    docs = [m or {} for (m,) in db.execute(
        select(S.metrics).where(S.period_kind == int(PeriodKind.WEEK), S.period_start == week)).all()] if week else []
    total = len(docs)
    items = []
    for key, meta in METRIC_CATALOG.items():
        values = [float(v) for d in docs
                  if (v := ((d.get("metrics") or {}).get(key) or {}).get("v")) is not None]
        reasons = Counter(r for d in docs if (r := (d.get("unmeasured") or {}).get(key)) is not None)
        items.append({
            "key": key, "section": meta.section, "unit": meta.unit, "phase": meta.phase, "direction": meta.direction,
            "measured_users": len(values), "total_users": total,
            "company_median": rnd(median(values)) if values else None,
            "unmeasured_reason": (reasons.most_common(1)[0][0] if reasons and not values else None) if total else None,
        })
    return {"week": week.isoformat() if isinstance(week, date) else None, "metrics": items,
            "deferred": list(DEFERRED_METRICS)}
