"""LUẬT KHUNG GIỜ CỦA NGÀY XẾP CA (duoc-CR-761) — thuần, không đụng DB; schema và service cùng gọi một chỗ.

Khung là `(start_hour, end_hour)` TRÒN, bán mở `[start, end)`: 0 ≤ start < end ≤ 24 (24 = hết ngày). Hai khung chạm nhau
(8–10 và 10–12) hợp lệ — không chồng. Tối đa `MAX_SEGMENTS` khung / ngày; KHÔNG khung = ngày nghỉ do xếp ca.
"""
from typing import Iterable

MAX_SEGMENTS = 12
HOUR_MIN, HOUR_MAX = 0, 24


def normalize_segments(pairs: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    """Kiểm + sắp các khung theo giờ bắt đầu; ném `ValueError` (câu tiếng Việt) nếu sai. Trả danh sách đã sắp."""
    segs = sorted((int(a), int(b)) for a, b in pairs)
    if len(segs) > MAX_SEGMENTS:
        raise ValueError(f"Mỗi ngày tối đa {MAX_SEGMENTS} khung giờ")
    prev_end = HOUR_MIN
    for start, end in segs:
        if not (HOUR_MIN <= start < HOUR_MAX and HOUR_MIN < end <= HOUR_MAX):
            raise ValueError("Khung giờ phải nằm trong 00:00–24:00 (giờ tròn)")
        if start >= end:
            raise ValueError("Giờ bắt đầu của khung phải nhỏ hơn giờ kết thúc")
        if start < prev_end:
            raise ValueError("Các khung giờ trong một ngày không được chồng nhau")
        prev_end = end
    return segs
