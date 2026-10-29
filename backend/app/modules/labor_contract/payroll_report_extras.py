"""Phần phụ của báo cáo A5 (duoc-CR-688): lương cơ bản thấp nhất / cao nhất theo nhóm (không cộng được
nên tính riêng từ chính các hàng) và xu hướng theo tháng — cả hai chỉ lọc trong bộ nhớ trên số HĐ đã nạp."""
from __future__ import annotations

from datetime import date, timedelta

from app.core.report_aggregate import DimensionSpec
from app.core.report_compute import bucket_rows
from app.core.report_period import Period, bucket_axis

from .payroll_report_data import PayRecord, rows_at

MINMAX_METRICS = (("base_min", "Lương cơ bản thấp nhất"), ("base_max", "Lương cơ bản cao nhất"))


def _minmax(rows: list[PayRecord]) -> dict:
    if not rows:
        return {"base_min": None, "base_max": None}
    sal = [r.base_salary for r in rows]
    return {"base_min": min(sal), "base_max": max(sal)}


def add_minmax(data: dict, dim: DimensionSpec | None, rows_cur: list[PayRecord],
               rows_cmp: list[PayRecord] | None) -> None:
    """Ghi `base_min`/`base_max` vào Tổng và từng nhóm (nhóm gộp «__other__» để None) + khai ở `meta`."""
    data["totals"]["current"].update(_minmax(rows_cur))
    if data["totals"]["compare"] is not None:
        data["totals"]["compare"].update(_minmax(rows_cmp or []))
    if dim is not None and data.get("groups") is not None:
        cur_b = bucket_rows(rows_cur, dim.key_of, dim.empty_label)
        cmp_b = bucket_rows(rows_cmp or [], dim.key_of, dim.empty_label)
        for g in data["groups"]:
            g["current"].update(_minmax(cur_b.get(g["key"], {}).get("rows", [])))
            if g.get("compare") is not None:
                g["compare"].update(_minmax(cmp_b.get(g["key"], {}).get("rows", [])))
    for key, label in MINMAX_METRICS:
        data["meta"]["metrics"].append({"key": key, "label": label, "kind": "money", "good": None,
                                         "helper": False, "snapshot": False,
                                         "additive": False})  # min / max không cộng được


def _values(rows: list[PayRecord]) -> dict:
    return {"payroll_total": sum(r.base_salary + r.allowance for r in rows), "people_paid": len(rows)}


def _same_day_last_year(d: date) -> date:
    try:
        return d.replace(year=d.year - 1)
    except ValueError:
        return date(d.year - 1, 2, 28)


def build_trend(records: list[PayRecord], period: Period, today: date) -> list[dict]:
    """Quỹ lương + số người hưởng lương tại CUỐI mỗi tháng của kỳ (mốc = min(cuối tháng, cuối kỳ, hôm nay));
    tháng bắt đầu sau hôm nay bị bỏ. Kỳ so sánh dời mỗi mốc về đúng khoảng lùi của kỳ so sánh."""
    has_cmp = period.compare != "none" and period.compare_from and period.compare_to
    offset = (period.date_from - period.compare_from).days if has_cmp else 0
    out = []
    for a in bucket_axis(period.date_from, period.date_to, "month"):
        y, m = int(a["key"][:4]), int(a["key"][5:])
        first = date(y, m, 1)
        if first > today:
            break
        nxt = date(y + (m == 12), m % 12 + 1, 1)
        t = min(nxt - timedelta(days=1), period.date_to, today)
        cmp_vals = None
        if has_cmp:
            ct = _same_day_last_year(t) if period.compare == "year" else t - timedelta(days=offset)
            cmp_vals = _values(rows_at(records, min(ct, today)))
        out.append({"key": a["key"], "label": a["label"], "current": _values(rows_at(records, t)),
                    "compare": cmp_vals})
    return out
