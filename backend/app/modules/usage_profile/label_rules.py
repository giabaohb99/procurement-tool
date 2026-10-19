"""Luật nhận «kiểu làm việc» (thuần) — duoc-CR-641, phase 04. Ngưỡng ở `label_thresholds.py`.

Mỗi luật trả `(score 0..1, [khóa chỉ số đã kích hoạt])` hoặc None. Thiếu dữ liệu tối thiểu hoặc chỉ số cần
mà `unmeasured` → None (KHÔNG gắn nhãn; khác với «không phải kiểu này»). `score` = mức vượt ngưỡng chuẩn hóa để sắp thứ tự.
Nhãn chỉ MÔ TẢ cách làm việc có bằng chứng; hồ sơ mặc định đọc theo KẾT QUẢ công việc (§8 thiết kế).
"""
from dataclasses import dataclass, field

from app.core.usage_codes import UsageStyle

from . import label_thresholds as T


@dataclass
class LabelContext:
    v: dict = field(default_factory=dict)       # khóa → giá trị người này (chỉ khóa đo được)
    med: dict = field(default_factory=dict)     # khóa → trung vị nhóm
    p75: dict = field(default_factory=dict)
    counts: dict = field(default_factory=dict)  # số đếm thô
    tenure_days: int | None = None


def _over(value, threshold) -> float:
    return max(0.0, min(1.0, value / threshold - 1.0)) if threshold else 0.0


def _x_med(c: LabelContext, key: str, factor: float, floor: float = 0.0) -> bool:
    """v ≥ factor × med và v ≥ floor và v > 0 (med = 0 → chỉ cần v > 0 và ≥ floor)."""
    v, m = c.v.get(key), c.med.get(key)
    return v is not None and v > 0 and v >= floor and (m is None or v >= factor * m)


def _batch(c):
    hits = []
    if c.counts.get("docs_created", 0) >= T.MIN_DOCS_MONTH_END and c.v.get("month_end_create_share", 0) >= T.BATCH_MONTH_END_SHARE:
        hits.append(("month_end_create_share", _over(c.v["month_end_create_share"], T.BATCH_MONTH_END_SHARE)))
    if c.counts.get("decisions_logged", 0) >= T.MIN_DECISIONS and c.v.get("batch_approval_share", 0) >= T.BATCH_APPROVAL_SHARE:
        hits.append(("batch_approval_share", _over(c.v["batch_approval_share"], T.BATCH_APPROVAL_SHARE)))
    if c.counts.get("api_calls", 0) >= T.MIN_API_CALLS and c.v.get("heatmap_top3_share", 0) >= T.BATCH_HEATMAP_TOP3:
        hits.append(("heatmap_top3_share", _over(c.v["heatmap_top3_share"], T.BATCH_HEATMAP_TOP3)))
    return hits


def _bottleneck(c):
    hits = []
    if c.counts.get("tasks_decided", 0) >= T.MIN_TASKS_DECIDED and _x_med(
            c, "approval_wait_p50_h", T.BOTTLENECK_X_MEDIAN, T.BOTTLENECK_MIN_HOURS):
        hits.append(("approval_wait_p50_h", _over(c.v["approval_wait_p50_h"], T.BOTTLENECK_MIN_HOURS)))
    if c.v.get("pending_now", 0) >= T.BOTTLENECK_PENDING:
        hits.append(("pending_now", _over(c.v["pending_now"], T.BOTTLENECK_PENDING)))
    return hits


def _excel(c):
    if c.v.get("exports", 0) < T.MIN_EXPORTS or c.v.get("exports", 0) / 4 < T.EXCEL_PER_WEEK:
        return []
    hits = [("exports", _over(c.v["exports"] / 4, T.EXCEL_PER_WEEK))]
    alt = []
    if c.v.get("export_per_list_view", 0) >= T.EXCEL_PER_LIST_VIEW:
        alt.append(("export_per_list_view", _over(c.v["export_per_list_view"], T.EXCEL_PER_LIST_VIEW)))
    if c.v.get("export_entity_weeks_max", 0) >= T.EXCEL_ENTITY_WEEKS:
        alt.append(("export_entity_weeks_max", _over(c.v["export_entity_weeks_max"], T.EXCEL_ENTITY_WEEKS)))
    return hits + alt if alt else []


def _newcomer(c):
    if c.tenure_days is None or c.tenure_days > T.NEWCOMER_TENURE_DAYS or c.v.get("workdays_net", 0) < T.MIN_WORKDAYS_NEWCOMER:
        return []
    sig = []
    if _x_med(c, "http_422_per_100_writes", T.NEWCOMER_X_MEDIAN):
        sig.append("http_422_per_100_writes")
    if _x_med(c, "form_abandon_rate", T.NEWCOMER_X_MEDIAN):
        sig.append("form_abandon_rate")
    if c.v.get("http_403", 0) >= T.NEWCOMER_403:
        sig.append("http_403")
    if c.v.get("help_views", 0) >= T.NEWCOMER_HELP_VIEWS:
        sig.append("help_views")
    if c.v.get("active_ratio", 1) < T.NEWCOMER_ACTIVE_RATIO:
        sig.append("active_ratio")
    return [(k, 0.0) for k in sig] if len(sig) >= T.NEWCOMER_SIGNALS_NEEDED else []


def _power(c):
    v, m = c.v, c.med
    if c.counts.get("active_days", 0) < T.MIN_ACTIVE_DAYS_POWER:
        return []
    need = ("saved_prefs", "http_422_per_100_writes", "distinct_screens_30d")
    if any(k not in v for k in need) or v["saved_prefs"] < T.POWER_MIN_PREFS:
        return []
    if v["http_422_per_100_writes"] > m.get("http_422_per_100_writes", v["http_422_per_100_writes"]):
        return []
    if v["distinct_screens_30d"] < c.p75.get("distinct_screens_30d", float("inf")):
        return []
    if "form_submit_p50_ms" in v and v["form_submit_p50_ms"] > m.get("form_submit_p50_ms", v["form_submit_p50_ms"]):
        return []
    return [(k, 0.0) for k in (*need, *(["form_submit_p50_ms"] if "form_submit_p50_ms" in v else []))]


def _wanderer(c):
    if c.counts.get("views", 0) < T.MIN_VIEWS_WANDERER and c.counts.get("forbidden", 0) < T.WANDERER_403:
        return []
    hits = []
    if c.v.get("http_403", 0) >= T.WANDERER_403 and _x_med(c, "http_403", T.WANDERER_X_MEDIAN):
        hits.append(("http_403", _over(c.v["http_403"], T.WANDERER_403)))
    if c.v.get("loop_share", 0) >= T.WANDERER_LOOP_SHARE:
        hits.append(("loop_share", _over(c.v["loop_share"], T.WANDERER_LOOP_SHARE)))
    return hits


def _mobile(c):
    if c.counts.get("api_writes", 0) >= T.MIN_WRITES_MOBILE and c.v.get("mobile_write_share", 0) >= T.MOBILE_WRITE_SHARE:
        return [("mobile_write_share", _over(c.v["mobile_write_share"], T.MOBILE_WRITE_SHARE))]
    return []


def _quality(c):
    if c.counts.get("submitted_chain", 0) < T.MIN_SUBMITTED:
        return []
    hits = []
    if c.v.get("returned_rate", 0) >= T.RETURNED_RATE and _x_med(c, "returned_rate", T.RETURNED_X_MEDIAN):
        hits.append(("returned_rate", _over(c.v["returned_rate"], T.RETURNED_RATE)))
    if c.v.get("edits_after_submit_share", 0) >= T.EDITS_AFTER_SUBMIT:
        hits.append(("edits_after_submit_share", _over(c.v["edits_after_submit_share"], T.EDITS_AFTER_SUBMIT)))
    return hits


def _proxy(c):
    if c.counts.get("proxy_docs", 0) >= T.MIN_PROXY_DOCS and c.v.get("proxy_share", 0) >= T.PROXY_SHARE:
        return [("proxy_share", _over(c.v["proxy_share"], T.PROXY_SHARE))]
    return []


def _low(c):
    if c.v.get("workdays_net", 0) < T.MIN_WORKDAYS_LOW or "active_ratio" not in c.v:
        return []
    effective = c.v["active_ratio"] + c.v.get("proxied_days_ratio", 0.0)   # ngày được bấm hộ tính là có làm
    if effective < T.LOW_ACTIVE_RATIO and c.med.get("active_ratio", 0) >= T.COHORT_ACTIVE_RATIO:
        return [("active_ratio", max(0.0, min(1.0, (T.LOW_ACTIVE_RATIO - effective) / T.LOW_ACTIVE_RATIO)))]
    return []


RULES = {
    UsageStyle.BATCH_WORKER: _batch, UsageStyle.APPROVAL_BOTTLENECK: _bottleneck,
    UsageStyle.EXCEL_PARALLEL: _excel, UsageStyle.NEWCOMER_STUCK: _newcomer, UsageStyle.POWER_USER: _power,
    UsageStyle.WANDERER: _wanderer, UsageStyle.MOBILE_FIRST: _mobile, UsageStyle.LOW_QUALITY_DOCS: _quality,
    UsageStyle.PROXY_DEPENDENT: _proxy, UsageStyle.LOW_USAGE: _low,
}


def evaluate_labels(ctx: LabelContext) -> list[dict]:
    """`[{"code", "score", "evidence": [khóa]}]` sắp theo score giảm dần."""
    out = []
    for style, rule in RULES.items():
        hits = rule(ctx)
        if hits:
            out.append({"code": int(style), "score": round(max(s for _, s in hits), 3),
                        "evidence": [k for k, _ in hits][:10]})
    return sorted(out, key=lambda x: (-x["score"], x["code"]))
