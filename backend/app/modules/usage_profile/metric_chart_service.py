"""Số liệu vẽ biểu đồ cho "Bộ chỉ số đánh giá" (duoc-CR-651): phân phối của tuần mới nhất + xu hướng trung vị 8 tuần.

Hàm THUẦN, không chạm DB (truy vấn nằm ở `metric_catalog_service`). Chỉ trả SỐ — nhãn tiếng Việt ở giao diện (luật R2).
Mỗi cột phân phối là khoảng NỬA MỞ `[lo, hi)`; cột tràn có `hi = None` (nghĩa "≥ lo").
"""
import math

from .metric_stats import median, percentile, rnd

TREND_WEEKS = 8
_MAX_BUCKETS = 10
_P95 = 0.95


def _nice_step(raw: float) -> float:
    """Bước "đẹp" (1/2/5 × 10^k) không nhỏ hơn `raw`."""
    if raw <= 0:
        return 1.0
    exp = math.floor(math.log10(raw))
    for mult in (1, 2, 5, 10):
        step = mult * 10 ** exp
        if step >= raw * (1 - 1e-9):
            return step
    return 10.0 ** (exp + 1)  # pragma: no cover - mult 10 luôn đủ


def _bucket(lo: float, hi: float | None, count: int) -> dict:
    return {"lo": rnd(lo), "hi": rnd(hi) if hi is not None else None, "count": count}


def build_histogram(unit: str, values: list[float]) -> list[dict]:
    """Phân phối giá trị đã đo của MỘT chỉ số; danh sách rỗng khi không ai đo được."""
    if not values:
        return []
    if unit == "minute_of_day":  # 24 cột theo giờ
        counts = [0] * 24
        for v in values:
            counts[min(max(int(v // 60), 0), 23)] += 1
        return [_bucket(h * 60, h * 60 + 60, c) for h, c in enumerate(counts)]
    if unit == "ratio":  # 0–10% … 90–100%, giá trị 100% (hoặc hơn) vào cột cuối
        counts = [0] * 10
        for v in values:
            counts[min(max(int(v * 10), 0), 9)] += 1
        return [_bucket(i / 10, (i + 1) / 10, c) for i, c in enumerate(counts)]
    if unit == "flag":  # 0 = không, 1 = có
        yes = sum(1 for v in values if v >= 0.5)
        return [_bucket(0, 1, len(values) - yes), _bucket(1, 2, yes)]
    #  count / min / h / ms / per100: cột đều theo bước "đẹp" tới p95, cộng một cột tràn.
    p95 = percentile(values, _P95) or 0.0
    step = _nice_step(p95 / _MAX_BUCKETS)
    if unit == "count":
        step = max(step, 1.0)
    n = max(1, math.ceil(p95 / step - 1e-9)) if p95 > 0 else 1
    counts = [0] * n
    overflow = 0
    for v in values:
        idx = int(max(v, 0) // step)
        if idx >= n:
            overflow += 1
        else:
            counts[idx] += 1
    out = [_bucket(i * step, (i + 1) * step, c) for i, c in enumerate(counts)]
    if overflow:
        out.append(_bucket(n * step, None, overflow))
    return out


def build_trend(weekly_values: list[tuple[str, list[float]]]) -> list[dict]:
    """`weekly_values` = [(tuần ISO, giá trị đã đo)] đã sắp tăng dần → [{week, median, measured}]. Tuần không ai đo: median None."""
    return [{"week": week, "median": rnd(median(vals)) if vals else None, "measured": len(vals)}
            for week, vals in weekly_values[-TREND_WEEKS:]]
