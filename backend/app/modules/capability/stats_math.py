"""Phần TÍNH THUẦN của thống kê năng lực (duoc-CR-657, D1d): trung vị / p90 / tỷ lệ làm lại — không đụng DB.

MySQL 8 không có hàm phân vị nên lấy cột cần thiết rồi tính ở đây (vài chục nghìn dòng / 180 ngày là chấp nhận được).
Đơn vị: THỜI GIAN tính bằng NGÀY LỊCH (giờ trôi qua / 24, làm tròn 2 số lẻ); tỷ lệ là số 0…1 (không phải %).
"""
from typing import NamedTuple

MIN_SAMPLES = 5          # dưới ngưỡng này KHÔNG hiện số (doc 22 §4): một hai phiếu không nói lên «người này làm nhanh/chậm»
BELOW_THRESHOLD = "BELOW_THRESHOLD"


class Sample(NamedTuple):
    """Một dòng `tab_work_cycle` đã xong, KHÔNG ước tính — đủ cột để tính."""

    cycle_hours: float | None
    rework_count: int
    is_late: bool | None
    estimate_hours: float | None
    actual_hours: float | None


def percentile(sorted_values: list[float], q: float) -> float:
    """Phân vị `q` (0…1) theo nội suy tuyến tính trên dãy ĐÃ SẮP XẾP, không rỗng."""
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = q * (len(sorted_values) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def _days(hours: float) -> float:
    return round(hours / 24.0, 2)


def summarize(samples: list[Sample], n_estimated: int = 0, min_samples: int = MIN_SAMPLES) -> dict:
    """Số liệu của MỘT nhóm. Dưới ngưỡng mẫu: các số là `None` + `below_threshold = True` (vẫn trả `n_done`)."""
    n = len(samples)
    out = {"n_done": n, "n_estimated": n_estimated, "below_threshold": n < min_samples,
           "mean_days": None, "p50_days": None, "p90_days": None, "max_days": None,
           "rework_rate": None, "first_pass_rate": None, "late_rate": None, "est_ratio_p50": None}
    if n < min_samples:
        return out
    hours = sorted(s.cycle_hours for s in samples if s.cycle_hours is not None)
    if hours:
        out.update(mean_days=_days(sum(hours) / len(hours)), p50_days=_days(percentile(hours, 0.5)),
                   p90_days=_days(percentile(hours, 0.9)), max_days=_days(hours[-1]))
    out["rework_rate"] = round(sum(s.rework_count for s in samples) / n, 4)
    out["first_pass_rate"] = round(sum(1 for s in samples if s.rework_count == 0) / n, 4)
    timed = [s.is_late for s in samples if s.is_late is not None]
    if timed:
        out["late_rate"] = round(sum(1 for x in timed if x) / len(timed), 4)
    ratios = sorted(s.actual_hours / s.estimate_hours for s in samples
                    if s.estimate_hours and s.actual_hours and s.estimate_hours > 0 and s.actual_hours > 0)
    if ratios:
        out["est_ratio_p50"] = round(percentile(ratios, 0.5), 2)
    return out
