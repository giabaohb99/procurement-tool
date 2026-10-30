"""Thống kê thuần cho hồ sơ cách làm việc (duoc-CR-641).

`percentile` nội suy tuyến tính giữa hai giá trị kề (phương pháp "linear", như numpy mặc định):
rank = p·(n−1); giá trị = x[⌊rank⌋] + (rank−⌊rank⌋)·(x[⌈rank⌉] − x[⌊rank⌋]). Ví dụ 5 việc 2/4/6/8/30 giờ:
p50 = 6, p90 = 8 + 0,6·(30−8) = 21,2.
"""
import math


def percentile(values, p: float):
    xs = sorted(v for v in values if v is not None)
    if not xs:
        return None
    rank = p * (len(xs) - 1)
    lo, hi = math.floor(rank), math.ceil(rank)
    return xs[lo] + (rank - lo) * (xs[hi] - xs[lo])


def median(values):
    return percentile(values, 0.5)


def ratio(num: float, den: float):
    """num/den hoặc None khi mẫu số 0 (KHÔNG ghi 0 thay cho "không đo được")."""
    return (num / den) if den else None


def rnd(v, digits: int = 4):
    return None if v is None else round(float(v), digits)
