"""Lịch làm việc phase 03 — nối lịch vào tính ngày nghỉ phép (`workday_service`).

⚠️ Bài QUAN TRỌNG NHẤT là nhóm «tương đương»: khi KHÔNG gán lịch nào, mọi con số phải ra
ĐÚNG như luật cứng cũ (T2–T7 làm, CN nghỉ, 08–17 trừ trưa 12–13). Công thức cũ được CHÉP
đóng băng vào đây (`_old_*`) — đừng sửa nó theo mã mới, nó là bản tham chiếu.
"""
from datetime import date, time, timedelta

import pytest
from fastapi import HTTPException

from app.core.work_schedule_codes import WorkScheduleLevel as L
from app.modules.leave import request_service, workday_service
from app.modules.leave.catalog_model import Holiday, LeaveType
from app.modules.leave.constants import (SESSION_AFTERNOON, SESSION_FULL, SESSION_HOURLY,
                                         SESSION_MORNING)
from lich_lam_viec_factory import (FULL, FULL_7H, MON, OFF, SAT, SAT_AM, SUN, assign,
                                   count_queries, make_schedule, make_world,
                                   week_t2_t6_sat_am)

# ── Bản tham chiếu ĐÓNG BĂNG của luật cũ (chép từ workday_service trước 05/10/2026) ──
_START = {SESSION_FULL: 1.0, SESSION_MORNING: 1.0, SESSION_AFTERNOON: 0.5}
_END = {SESSION_FULL: 1.0, SESSION_MORNING: 0.5, SESSION_AFTERNOON: 1.0}


def _old_same_day(fs, ts):
    start = 1 if fs == SESSION_AFTERNOON else 0
    end = 0 if ts == SESSION_MORNING else 1
    return max(0.0, (end - start + 1) * 0.5)


def _old_credit(day, a, b, fs, ts):
    if a == b:
        return _old_same_day(fs, ts)
    if day == a:
        return _START.get(fs, 1.0)
    if day == b:
        return _END.get(ts, 1.0)
    return 1.0


def _old_days(a, b, fs, ts, holidays=frozenset(), exclude=True):
    total, day = 0.0, a
    while day <= b:
        if not (exclude and (day.weekday() == 6 or day in holidays)):
            total += _old_credit(day, a, b, fs, ts)
        day += timedelta(days=1)
    return round(total, 2)


def _m(t: time) -> int:
    return t.hour * 60 + t.minute


def _old_worked(s, e):
    lo, hi = max(_m(s), 8 * 60), min(_m(e), 17 * 60)
    if hi <= lo:
        return 0.0
    return (hi - lo - max(0, min(hi, 13 * 60) - max(lo, 12 * 60))) / 60.0


def _old_hourly(a, b, ft, tt, holidays=frozenset(), exclude=True):
    def ok(d):
        return not exclude or not (d.weekday() == 6 or d in holidays)
    if a == b:
        return round(_old_worked(ft, tt) / 8.0, 2) if ok(a) else 0.0
    hours, day = 0.0, a
    while day <= b:
        if ok(day):
            hours += (_old_worked(ft, time(17, 0)) if day == a
                      else _old_worked(time(8, 0), tt) if day == b else 8.0)
        day += timedelta(days=1)
    return round(hours / 8.0, 2)


SESSIONS = (SESSION_FULL, SESSION_MORNING, SESSION_AFTERNOON)
HOLIDAYS = frozenset({date(2026, 1, 7), date(2026, 1, 10)})   # thứ Tư + thứ Bảy


@pytest.fixture
def world_with_holidays(db):
    company, dept, emp = make_world(db)
    for d in HOLIDAYS:
        db.add(Holiday(company_id=0, date=d, name="Lễ", is_recurring=False, is_active=True))
    db.flush()
    return company, dept, emp


# ── Tương đương khi chưa gán lịch ─────────────────────────────────────────────

@pytest.mark.parametrize("length", [1, 2, 8])
@pytest.mark.parametrize("weekday", range(7))
@pytest.mark.parametrize("fs", SESSIONS)
@pytest.mark.parametrize("ts", SESSIONS)
@pytest.mark.parametrize("with_employee", [False, True])
def test_chua_gan_lich_ra_dung_so_cu_moi_to_hop_buoi(db, world_with_holidays, fs, ts, weekday,
                                                     length, with_employee):
    _, _, emp = world_with_holidays
    a = MON + timedelta(days=weekday)
    b = a + timedelta(days=length - 1)
    for exclude in (True, False):
        got = workday_service.count_leave_days(
            db, a, b, fs, ts, exclude_holiday=exclude,
            employee=emp if with_employee else None)
        #  Lễ chung (company_id=0) áp cho cả hai cách gọi.
        want = _old_days(a, b, fs, ts, HOLIDAYS, exclude)
        assert got == want, (a, b, fs, ts, exclude)


@pytest.mark.parametrize("start_hour,end_hour", [
    (time(8, 0), time(17, 0)), (time(9, 30), time(11, 30)), (time(11, 30), time(13, 30)),
    (time(12, 0), time(13, 0)), (time(14, 0), time(16, 59)), (time(6, 0), time(7, 0)),
    (time(19, 0), time(21, 0)), (time(0, 0), time(23, 59)), (time(15, 0), time(9, 0)),
])
@pytest.mark.parametrize("length", [1, 2, 3])
@pytest.mark.parametrize("weekday", range(7))
def test_chua_gan_lich_theo_gio_ra_dung_so_cu(db, world_with_holidays, start_hour, end_hour,
                                              length, weekday):
    _, _, emp = world_with_holidays
    a = MON + timedelta(days=weekday)
    b = a + timedelta(days=length - 1)
    for exclude in (True, False):
        got = workday_service.count_hourly_days(db, a, b, start_hour, end_hour,
                                                exclude_holiday=exclude, employee=emp)
        assert got == _old_hourly(a, b, start_hour, end_hour, HOLIDAYS, exclude)


# ── Có lịch ───────────────────────────────────────────────────────────────────

@pytest.fixture
def sat_half(db):
    """Nhân sự thuộc phòng gán lịch T2–T6 cả ngày + T7 sáng + CN nghỉ."""
    company, dept, emp = make_world(db, "SH1")
    sched = make_schedule(db, "T7 nửa ngày", week_t2_t6_sat_am())
    assign(db, L.DEPARTMENT, dept.id, sched.id, date(2026, 1, 1))
    return company, dept, emp, sched


def _days(db, emp, a, b, fs=SESSION_FULL, ts=SESSION_FULL, **kw):
    return workday_service.count_leave_days(db, a, b, fs, ts, employee=emp, **kw)


def test_nghi_tron_t7_nua_ngay_la_0_5(db, sat_half):
    _, _, emp, _ = sat_half
    assert _days(db, emp, SAT, SAT) == 0.5


def test_nghi_t6_den_t2_la_2_5(db, sat_half):
    _, _, emp, _ = sat_half
    friday = SAT - timedelta(days=1)
    assert _days(db, emp, friday, MON + timedelta(days=7)) == 2.5   # 1 + 0.5 + 0 (CN) + 1


def test_bat_dau_t7_buoi_chieu_gop_0_va_t7_chieu_chieu_la_0(db, sat_half):
    _, _, emp, _ = sat_half
    assert _days(db, emp, SAT, SAT, SESSION_AFTERNOON, SESSION_AFTERNOON) == 0.0
    # T7 buổi chiều → T2: T7 góp 0 (chỉ làm sáng), CN 0, T2 1.0
    assert _days(db, emp, SAT, SAT + timedelta(days=2), SESSION_AFTERNOON, SESSION_FULL) == 1.0
    assert _days(db, emp, SAT, SAT, SESSION_MORNING, SESSION_MORNING) == 0.5


def test_compute_days_t7_chieu_la_400_co_ten_nhan_su(db, sat_half):
    _, _, emp, _ = sat_half
    lt = LeaveType(code="annual", name="Phép năm", counts_balance=True, annual_quota_days=12.0)
    db.add(lt)
    db.flush()
    with pytest.raises(HTTPException) as exc:
        request_service.compute_days(db, lt, emp, SAT, SAT, SESSION_AFTERNOON, SESSION_AFTERNOON)
    assert exc.value.status_code == 400 and emp.full_name in exc.value.detail
    # Sửa đè vẫn thắng.
    assert request_service.compute_days(db, lt, emp, SAT, SAT, SESSION_AFTERNOON,
                                        SESSION_AFTERNOON, requested=2) == 2.0


def test_lich_doi_giua_khoang(db):
    _, dept, emp = make_world(db, "DG1")
    a = make_schedule(db, "A", [FULL] * 7)
    b = make_schedule(db, "B", [OFF] * 7)
    assign(db, L.DEPARTMENT, dept.id, a.id, date(2026, 1, 1), date(2026, 1, 7))
    assign(db, L.DEPARTMENT, dept.id, b.id, date(2026, 1, 8))
    # 05→09/01: 05,06,07 theo A (3 ngày), 08,09 theo B (0).
    assert _days(db, emp, MON, MON + timedelta(days=4)) == 3.0


def test_gan_nhan_su_thang_gan_phong(db, sat_half):
    _, _, emp, _ = sat_half
    only_mon = make_schedule(db, "Chỉ T2", [FULL] + [OFF] * 6)
    assign(db, L.EMPLOYEE, emp.id, only_mon.id, date(2026, 1, 1))
    assert _days(db, emp, MON, SAT) == 1.0


def test_theo_gio_t7_sang(db, sat_half):
    _, _, emp, _ = sat_half
    assert workday_service.count_hourly_days(db, SAT, SAT, time(10, 0), time(12, 0), employee=emp) == 0.25
    assert workday_service.count_hourly_days(db, SAT, SAT, time(8, 0), time(17, 0), employee=emp) == 0.5
    assert workday_service.count_hourly_days(db, SAT, SAT, time(13, 0), time(17, 0), employee=emp) == 0.0


def test_theo_gio_ngay_7h_nghi_tron_van_la_1(db):
    _, dept, emp = make_world(db, "H7")
    s = make_schedule(db, "7h", [FULL_7H] * 7)
    assign(db, L.DEPARTMENT, dept.id, s.id, date(2026, 1, 1))
    assert workday_service.count_hourly_days(db, MON, MON, time(8, 0), time(16, 0), employee=emp) == 1.0
    assert workday_service.count_hourly_days(db, MON, MON, time(8, 0), time(12, 0), employee=emp) == 0.57


def test_theo_gio_ngay_off_ngoai_khung_gio_trua_ra_0(db, sat_half):
    _, _, emp, _ = sat_half
    assert workday_service.count_hourly_days(db, SUN, SUN, time(8, 0), time(17, 0), employee=emp) == 0.0
    assert workday_service.count_hourly_days(db, MON, MON, time(18, 0), time(20, 0), employee=emp) == 0.0
    assert workday_service.count_hourly_days(db, MON, MON, time(12, 0), time(13, 0), employee=emp) == 0.0


def test_exclude_holiday_false_bo_qua_lich_dem_lich_duong(db):
    _, dept, emp = make_world(db, "TS1")
    s = make_schedule(db, "Toàn nghỉ", [OFF] * 7)
    assign(db, L.DEPARTMENT, dept.id, s.id, date(2026, 1, 1))
    assert _days(db, emp, MON, MON + timedelta(days=6), exclude_holiday=False) == 7.0
    assert workday_service.count_hourly_days(db, MON, MON, time(8, 0), time(17, 0),
                                             employee=emp, exclude_holiday=False) == 1.0
    assert _days(db, emp, MON, MON + timedelta(days=6)) == 0.0


def test_ngay_le_van_bi_tru_tren_ngay_lam(db, sat_half):
    _, _, emp, _ = sat_half
    db.add(Holiday(company_id=0, date=SAT, name="Lễ", is_recurring=False, is_active=True))
    db.flush()
    assert _days(db, emp, SAT, SAT) == 0.0


def test_mau_toan_off_compute_days_sua_de_thang_va_so_0_la_400(db):
    _, dept, emp = make_world(db, "OF1")
    s = make_schedule(db, "Nghỉ hết", [OFF] * 7)
    assign(db, L.DEPARTMENT, dept.id, s.id, date(2026, 1, 1))
    lt = LeaveType(code="annual", name="Phép năm", counts_balance=True, annual_quota_days=12.0)
    db.add(lt)
    db.flush()
    assert request_service.compute_days(db, lt, emp, MON, MON, 1, 1, requested=2) == 2.0
    with pytest.raises(HTTPException) as exc:
        request_service.compute_days(db, lt, emp, MON, MON, 1, 1, requested=0)
    assert exc.value.status_code == 400


def test_khoang_nguoc_la_0_khong_no(db, sat_half):
    _, _, emp, _ = sat_half
    assert _days(db, emp, MON + timedelta(days=3), MON) == 0.0
    assert workday_service.count_hourly_days(db, MON + timedelta(days=3), MON, time(8), time(9),
                                             employee=emp) == 0.0


def test_so_truy_van_count_leave_days_400_ngay_toi_da_3(db, sat_half):
    _, _, emp, _ = sat_half
    db.commit()
    db.refresh(emp)
    got, sql = count_queries(db, lambda: _days(db, emp, MON, MON + timedelta(days=399)))
    assert got > 0 and len(sql) <= 3
    _, sql_h = count_queries(db, lambda: workday_service.count_hourly_days(
        db, MON, MON + timedelta(days=399), time(9), time(10), employee=emp))
    assert len(sql_h) <= 3


def test_schedule_name_on_cho_estimate_days(db, sat_half):
    _, _, emp, sched = sat_half
    assert workday_service.schedule_name_on(db, emp, MON) == "T7 nửa ngày"
    _, _, other = make_world(db, "KH2")
    assert "Mặc định" in workday_service.schedule_name_on(db, other, MON)


def test_draft_tool_khop_count_leave_days_voi_nhan_su_co_lich_t7_nua_ngay(db, seed, monkeypatch):
    from app.modules.assistant.tools.base import ToolContext
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    user = db.get(User, seed.u_req_id)
    emp = db.get(Employee, user.employee_id)
    sched = make_schedule(db, "T7 nửa ngày", week_t2_t6_sat_am())
    assign(db, L.DEPARTMENT, emp.department_id, sched.id, date(2026, 1, 1))
    db.add(LeaveType(code="unpaid", name="Nghỉ không lương", counts_balance=False))
    db.commit()
    monkeypatch.setattr(ToolContext, "can", lambda self, entity, action="read": True)
    ctx = ToolContext(db=db, user=user)
    out = _run_leave(ctx, {"from_date": "2026-09-05", "to_date": "2026-09-05",   # thứ Bảy
                           "reason": "Việc riêng", "leave_type": "unpaid"})
    assert out["status"] == "ready"
    want = workday_service.count_leave_days(db, date(2026, 9, 5), date(2026, 9, 5), employee=emp)
    assert want == 0.5 and out["draft"]["lines"][0]["days"] == 0.5
