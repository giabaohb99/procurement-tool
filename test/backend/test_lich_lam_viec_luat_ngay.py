"""Lịch làm việc phase 02 — luật MỘT ngày (`day_rules`, thuần, không DB)."""
from datetime import time

import pytest

from app.core.work_schedule_codes import WorkDayKind
from app.modules.work_schedule.day_rules import (AM, FALLBACK_WEEK, PM, DaySpec,
                                                 day_capacity, day_hours, weekly_workdays,
                                                 work_mask, worked_hours)
from lich_lam_viec_factory import FULL, FULL_7H, OFF, SAT_AM, SAT_PM, week_t2_t6_sat_am

T = time


def test_work_mask_bon_loai_ngay():
    assert [work_mask(s) for s in (OFF, FULL, SAT_AM, SAT_PM)] == [0, AM | PM, AM, PM]


def test_cong_toi_da_cua_ngay():
    assert [day_capacity(s) for s in (OFF, FULL, SAT_AM, SAT_PM)] == [0.0, 1.0, 0.5, 0.5]


def test_fallback_la_t2_t7_08_17_cn_nghi():
    assert [s.kind for s in FALLBACK_WEEK] == [WorkDayKind.FULL] * 6 + [WorkDayKind.OFF]
    assert weekly_workdays(FALLBACK_WEEK) == 6.0
    assert day_hours(FALLBACK_WEEK[0]) == 8.0   # 9h trừ 1h trưa — nguồn của «giờ/8» cũ


def test_tuan_t2_t6_va_sang_t7_la_5_ruoi_con_toan_nghi_la_0():
    assert weekly_workdays(week_t2_t6_sat_am()) == 5.5
    assert weekly_workdays([OFF] * 7) == 0.0
    assert weekly_workdays([]) == 0.0


@pytest.mark.parametrize("start,end,expected", [
    (T(8, 0), T(17, 0), 8.0),      # cả ngày
    (T(11, 30), T(13, 30), 1.0),   # vắt trưa: chỉ 11:30–12:00 + 13:00–13:30
    (T(12, 0), T(13, 0), 0.0),     # đúng giờ trưa
    (T(19, 0), T(21, 0), 0.0),     # ngoài khung
    (T(6, 0), T(7, 59), 0.0),      # trước khung
    (T(10, 0), T(10, 0), 0.0),     # start == end
    (T(12, 0), T(9, 0), 0.0),      # ngược
    (T(0, 0), T(23, 59), 8.0),     # phủ cả khung → cắt về khung làm
])
def test_worked_hours_cat_theo_khung_va_tru_trua(start, end, expected):
    assert worked_hours(FULL, start, end) == expected


def test_ngay_off_hoac_thieu_gio_ra_0_khong_no():
    assert worked_hours(OFF, T(8, 0), T(17, 0)) == 0.0
    assert day_hours(OFF) == 0.0
    # Dữ liệu hỏng: ngày FULL mà thiếu giờ → 0 chứ không TypeError.
    broken = DaySpec(WorkDayKind.FULL)
    assert worked_hours(broken, T(8, 0), T(17, 0)) == 0.0
    assert day_hours(broken) == 0.0


def test_ngay_ngan_7_gio_va_nua_ngay():
    assert day_hours(FULL_7H) == 7.0
    assert day_hours(SAT_AM) == 4.0
    assert worked_hours(SAT_AM, T(10, 0), T(12, 0)) == 2.0
    assert worked_hours(SAT_AM, T(12, 0), T(17, 0)) == 0.0   # chiều T7 không làm


def test_ngay_khong_co_trua_thi_khong_tru():
    no_lunch = DaySpec(WorkDayKind.FULL, T(8, 0), T(16, 0))
    assert day_hours(no_lunch) == 8.0
