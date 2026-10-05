"""Lịch làm việc phase 07 — vá lỗi từ đợt rà soát mã «Ai làm / ai nghỉ».

Mốc: 05/01/2026 = thứ Hai. Mỗi bài nhắc lại lỗi đã bắt được để người sau không xóa nhầm.
"""
from datetime import date, time

import pytest

from app.modules.leave.constants import (LR_APPROVED, LR_PENDING, SESSION_AFTERNOON, SESSION_FULL,
                                         SESSION_HOURLY, SESSION_MORNING)
from test_lich_lam_viec_roster import _emp, _get, _leave, _row, api  # noqa: F401  (api = fixture)

D = [date(2026, 1, 5 + i) for i in range(7)]   # T2..CN


def _hourly(db, emp, d1, d2, t1, t2, **kw):
    return _leave(db, emp, d1, d2, fs=SESSION_HOURLY, ts=SESSION_HOURLY, from_time=t1, to_time=t2, **kw)


def _flags(api, emp, idx):
    leave = _row(_get(api), emp)["cells"][idx]["leave"]
    return None if leave is None else (leave["morning"], leave["afternoon"])


# ── H1: nghỉ theo giờ nhiều ngày + mốc nghỉ trưa + ngoài giờ ─────────────────

def test_multi_day_hourly_leave_paints_each_day_by_its_own_window(api, db):
    """Lỗi cũ: so from_time/to_time với mốc trưa ở MỌI ngày → ngày giữa/cuối sai."""
    _, _, emp = api.world
    _hourly(db, emp, D[0], D[2], time(14, 0), time(10, 0))
    assert [_flags(api, emp, i) for i in range(4)] == [(False, True), (True, True), (True, False), None]


@pytest.mark.parametrize("t1,t2,expected", [
    (time(12, 0), time(13, 0), None),               # đúng giờ nghỉ trưa → không tô
    (time(11, 0), time(12, 0), (True, False)),      # chạm mốc trưa phía sáng
    (time(13, 0), time(14, 0), (False, True)),
    (time(17, 30), time(19, 0), None),              # ngoài giờ làm
    (time(6, 0), time(7, 59), None),
    (time(11, 59), time(12, 1), (True, False)),     # lấn 1 phút vào trưa vẫn chỉ buổi sáng
    (time(12, 59), time(13, 1), (False, True)),
    (time(7, 0), time(18, 0), (True, True)),
    (time(10, 0), time(10, 0), None),               # khoảng rỗng
    (time(15, 0), time(9, 0), None),                # ngược chiều trong một ngày
])
def test_single_day_hourly_leave_edges(api, db, t1, t2, expected):
    _, _, emp = api.world
    _hourly(db, emp, D[0], D[0], t1, t2)
    assert _flags(api, emp, 0) == expected


def test_hourly_leave_on_half_day_schedule_only_paints_existing_half(api, db):
    """Thứ Bảy chỉ làm sáng: nghỉ 14:00 T6 → 10:00 T7 không được tô buổi chiều T7."""
    _, _, emp = api.world
    _hourly(db, emp, D[4], D[5], time(14, 0), time(10, 0))
    assert _flags(api, emp, 4) == (False, True)
    assert _flags(api, emp, 5) == (True, False)


# ── M1: nghỉ việc theo resign_date ───────────────────────────────────────────

def test_resign_date_beats_status_when_present(api, db):
    """Lỗi cũ: status=resigned loại ngay dù resign_date còn ở tương lai (HR đặt trạng thái sớm)."""
    company, dept, emp = api.world
    inside = _emp(db, company, dept, status="resigned", resign_date=date(2026, 1, 8))
    future = _emp(db, company, dept, status="resigned", resign_date=date(2026, 3, 1))
    before = _emp(db, company, dept, status="resigned", resign_date=date(2026, 1, 4))
    no_date = _emp(db, company, dept, status="resigned")
    inactive_dated = _emp(db, company, dept, resign_date=date(2026, 3, 1))
    inactive_dated.is_active = False
    db.flush()
    ids = {i["employee_id"] for i in _get(api).json()["data"]["items"]}
    assert {inside.id, future.id, inactive_dated.id} <= ids
    assert not ({before.id, no_date.id} & ids)


# ── L3: ngày vào làm ─────────────────────────────────────────────────────────

def test_hire_date_after_range_is_excluded(api, db):
    company, dept, emp = api.world
    later = _emp(db, company, dept, hire_date=date(2026, 1, 12))
    on_last_day = _emp(db, company, dept, hire_date=date(2026, 1, 11))
    unknown = _emp(db, company, dept)
    ids = {i["employee_id"] for i in _get(api).json()["data"]["items"]}
    assert later.id not in ids and {on_last_day.id, unknown.id} <= ids


# ── L1: nhiều đơn nửa buổi cùng ngày ─────────────────────────────────────────

def test_two_half_day_requests_same_day_union_masks(api, db):
    """Lỗi cũ: chỉ đơn thắng được tô → xin sáng một đơn + chiều một đơn chỉ thấy một nửa."""
    _, _, emp = api.world
    am = _leave(db, emp, D[0], D[0], LR_PENDING, SESSION_FULL, SESSION_MORNING)
    pm = _leave(db, emp, D[0], D[0], LR_APPROVED, SESSION_AFTERNOON, SESSION_FULL)
    leave = _row(_get(api), emp)["cells"][0]["leave"]
    assert (leave["morning"], leave["afternoon"]) == (True, True)
    assert leave["request_id"] == pm.id and leave["is_approved"] is True and am.id != pm.id


def test_displayed_request_prefers_approved_then_more_halves_then_lower_id(api, db):
    _, _, emp = api.world
    a = _leave(db, emp, D[0], D[0], LR_APPROVED, SESSION_FULL, SESSION_MORNING)
    b = _leave(db, emp, D[0], D[0], LR_APPROVED, SESSION_FULL, SESSION_FULL)    # che 2 nửa
    c = _leave(db, emp, D[0], D[0], LR_APPROVED, SESSION_FULL, SESSION_FULL)    # id lớn hơn
    assert _row(_get(api), emp)["cells"][0]["leave"]["request_id"] == b.id < c.id and a.id < b.id


def test_identical_duplicate_requests_stay_stable(api, db):
    _, _, emp = api.world
    first = _leave(db, emp, D[1], D[1], LR_PENDING)
    _leave(db, emp, D[1], D[1], LR_PENDING)
    assert _row(_get(api), emp)["cells"][1]["leave"]["request_id"] == first.id
