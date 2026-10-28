"""Tuổi nghỉ hưu theo lộ trình Nghị định 135/2020/NĐ-CP (điều kiện lao động BÌNH THƯỜNG) — hàm thuần.

Lộ trình (năm = NĂM NGHỈ HƯU):
  - Nam: 60 tuổi 3 tháng năm 2021, mỗi năm tăng 3 tháng, tới 62 tuổi từ năm 2028.
  - Nữ: 55 tuổi 4 tháng năm 2021, mỗi năm tăng 4 tháng, tới 60 tuổi từ năm 2035.
  - Trước 2021: nam 60, nữ 55 tuổi (luật cũ — người đủ tuổi trước 01/01/2021 đã tới tuổi).
Không biết giới tính (0 / khác) -> không có quy tắc, trả `None` (báo cáo bỏ qua người đó).
Không xét nghề nặng nhọc / độc hại / vùng khó khăn (được nghỉ sớm hơn) — báo cáo chỉ là CẢNH BÁO.
"""
from __future__ import annotations

import calendar
from datetime import date

GENDER_MALE, GENDER_FEMALE = 1, 2
ROADMAP_FIRST_YEAR = 2021
#  (tuổi gốc trước 2021, tháng cộng thêm ở năm 2021, tháng tăng mỗi năm, trần tuổi tính bằng tháng)
_RULES = {GENDER_MALE: (60 * 12, 3, 3, 62 * 12), GENDER_FEMALE: (55 * 12, 4, 4, 60 * 12)}


def retirement_age_months(year: int, gender: int) -> int | None:
    """Tuổi nghỉ hưu (tính bằng THÁNG) của người nghỉ hưu trong năm `year`. Giới tính lạ -> None."""
    rule = _RULES.get(gender)
    if rule is None:
        return None
    base, first_add, step, cap = rule
    if year < ROADMAP_FIRST_YEAR:
        return base
    return min(base + first_add + step * (year - ROADMAP_FIRST_YEAR), cap)


def add_months(d: date, months: int) -> date:
    """Cộng tháng, ngày vượt cuối tháng thì lùi về ngày cuối tháng (29/02 + 12 tháng -> 28/02)."""
    total = d.year * 12 + (d.month - 1) + months
    year, month = divmod(total, 12)
    return date(year, month + 1, min(d.day, calendar.monthrange(year, month + 1)[1]))


def end_of_month(d: date) -> date:
    return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


def retirement_date(dob: date, gender: int) -> date | None:
    """THỜI ĐIỂM nghỉ hưu của người sinh `dob` = CUỐI THÁNG mà người đó đủ tuổi nghỉ hưu (Nghị định 135/2020:
    người lao động nghỉ hưu vào cuối tháng đủ tuổi). Tháng đủ tuổi tính như sau.

    Năm nghỉ hưu Y là năm nhỏ nhất (từ 2021) mà `dob + tuổi(Y)` rơi vào năm <= Y; tuổi(Y) tăng
    đều theo năm nên không bao giờ bỏ qua năm khớp. Đã đủ tuổi theo luật cũ trước 2021 thì lấy
    `dob + tuổi cũ`. Quá năm trần của lộ trình thì dùng tuổi trần."""
    base = retirement_age_months(ROADMAP_FIRST_YEAR - 1, gender)
    if base is None:
        return None
    old = add_months(dob, base)
    if old.year < ROADMAP_FIRST_YEAR:
        return end_of_month(old)
    for year in range(ROADMAP_FIRST_YEAR, ROADMAP_FIRST_YEAR + 20):
        candidate = add_months(dob, retirement_age_months(year, gender))
        if candidate.year <= year:
            return end_of_month(candidate)
    return end_of_month(add_months(dob, retirement_age_months(ROADMAP_FIRST_YEAR + 19, gender)))
