"""Lịch làm việc phase 02 — bộ phân giải `load_day_plans` / `effective_for_employee`.

Đi tìm chỗ SAI: ranh ngày hiệu lực, đối tượng 0 rác, dòng chồng cài tay, mẫu hỏng, số truy vấn.
"""
from datetime import date, timedelta

from app.core.work_schedule_codes import WorkDayKind, WorkScheduleLevel as L
from app.modules.work_schedule import resolver
from app.modules.work_schedule.day_rules import FALLBACK_NAME, FALLBACK_WEEK
from app.modules.work_schedule.model import WorkScheduleDay
from lich_lam_viec_factory import (FULL, MON, OFF, SAT, SAT_AM, assign, count_queries,
                                   make_schedule, make_world, week_t2_t6_sat_am)


def _plan(db, emp, start=MON, end=None, **over):
    kw = dict(employee_id=emp.id, department_id=emp.department_id, company_id=emp.company_id)
    kw.update(over)
    return resolver.load_day_plans(db, from_date=start, to_date=end or start, **kw)


def test_khong_gan_gi_ra_fallback(db):
    _, _, emp = make_world(db)
    plan = _plan(db, emp, MON, MON + timedelta(days=6))
    assert [plan(MON + timedelta(days=i)) for i in range(7)] == list(FALLBACK_WEEK)


def test_chi_co_he_thong(db):
    _, _, emp = make_world(db)
    s = make_schedule(db, "HT", week_t2_t6_sat_am())
    assign(db, L.SYSTEM, 0, s.id, date(2026, 1, 1))
    assert _plan(db, emp, SAT)(SAT).kind is WorkDayKind.MORNING


def test_nhan_su_thang_phong_thang_phap_nhan_thang_he_thong(db):
    company, dept, emp = make_world(db)
    names = {}
    for key, spec in (("sys", FULL), ("co", OFF), ("dep", SAT_AM), ("emp", FULL)):
        names[key] = make_schedule(db, key, [spec] * 7)
    assign(db, L.SYSTEM, 0, names["sys"].id, date(2026, 1, 1))
    assign(db, L.COMPANY, company.id, names["co"].id, date(2026, 1, 1))
    assert _plan(db, emp)(MON).kind is WorkDayKind.OFF          # pháp nhân thắng hệ thống
    assign(db, L.DEPARTMENT, dept.id, names["dep"].id, date(2026, 1, 1))
    assert _plan(db, emp)(MON).kind is WorkDayKind.MORNING      # phòng thắng pháp nhân
    assign(db, L.EMPLOYEE, emp.id, names["emp"].id, date(2026, 1, 1))
    assert _plan(db, emp)(MON).kind is WorkDayKind.FULL         # nhân sự thắng phòng


def test_nv_chua_khai_phap_nhan_khong_dinh_dong_rac_company_0(db):
    """Dòng `(COMPANY, 0)` cài tay vào DB (dữ liệu hỏng) KHÔNG được áp cho NV `company_id=0`."""
    _, _, emp = make_world(db)
    junk = make_schedule(db, "Rác", [OFF] * 7)
    assign(db, L.COMPANY, 0, junk.id, date(2026, 1, 1))
    assign(db, L.DEPARTMENT, 0, junk.id, date(2026, 1, 1))
    assign(db, L.EMPLOYEE, 0, junk.id, date(2026, 1, 1))
    plan = _plan(db, emp, company_id=0, department_id=0, employee_id=0)
    assert plan(MON) == FALLBACK_WEEK[0]


def test_ranh_effective_to_hai_ngay_hai_mau(db):
    _, dept, emp = make_world(db)
    a = make_schedule(db, "A", [FULL] * 7)
    b = make_schedule(db, "B", [OFF] * 7)
    assign(db, L.DEPARTMENT, dept.id, a.id, date(2026, 1, 1), date(2026, 1, 31))
    assign(db, L.DEPARTMENT, dept.id, b.id, date(2026, 2, 1))
    plan = _plan(db, emp, date(2026, 1, 31), date(2026, 2, 1))
    assert plan(date(2026, 1, 31)).kind is WorkDayKind.FULL
    assert plan(date(2026, 2, 1)).kind is WorkDayKind.OFF


def test_effective_to_null_ap_mai_mai_va_dong_ket_thuc_hom_qua_khong_ap_hom_nay(db):
    _, dept, emp = make_world(db)
    a = make_schedule(db, "A", [OFF] * 7)
    assign(db, L.DEPARTMENT, dept.id, a.id, date(2026, 1, 1), MON - timedelta(days=1))
    assert _plan(db, emp)(MON) == FALLBACK_WEEK[0]            # kết thúc hôm qua
    assign(db, L.DEPARTMENT, dept.id, a.id, MON)              # không thời hạn
    assert _plan(db, emp, date(2099, 1, 1))(date(2099, 1, 1)).kind is WorkDayKind.OFF


def test_hai_dong_chong_cai_tay_effective_from_muon_thang(db):
    _, dept, emp = make_world(db)
    old = make_schedule(db, "Cũ", [FULL] * 7)
    new = make_schedule(db, "Mới", [OFF] * 7)
    assign(db, L.DEPARTMENT, dept.id, old.id, date(2026, 1, 1))
    assign(db, L.DEPARTMENT, dept.id, new.id, date(2026, 1, 3))
    assert _plan(db, emp)(MON).kind is WorkDayKind.OFF


def test_mau_thieu_thu_6_dung_fallback_ngay_do(db):
    _, _, emp = make_world(db)
    s = make_schedule(db, "Hỏng", [OFF] * 7)
    db.query(WorkScheduleDay).filter_by(schedule_id=s.id, weekday=5).delete()
    assign(db, L.SYSTEM, 0, s.id, date(2026, 1, 1))
    plan = _plan(db, emp, MON, SAT)
    assert plan(SAT) == FALLBACK_WEEK[5]
    assert plan(MON).kind is WorkDayKind.OFF


def test_mau_da_tat_van_ap_neu_con_gan(db):
    _, _, emp = make_world(db)
    s = make_schedule(db, "Tắt", [OFF] * 7, is_active=False)
    assign(db, L.SYSTEM, 0, s.id, date(2026, 1, 1))
    assert _plan(db, emp)(MON).kind is WorkDayKind.OFF


def test_day_kind_la_bi_coi_la_nghi_khong_no(db):
    _, _, emp = make_world(db)
    s = make_schedule(db, "Lạ", [FULL] * 7)
    db.query(WorkScheduleDay).filter_by(schedule_id=s.id, weekday=0).update({"day_kind": 99})
    assign(db, L.SYSTEM, 0, s.id, date(2026, 1, 1))
    assert _plan(db, emp)(MON).kind is WorkDayKind.OFF


def test_so_truy_van_co_dinh_1_ngay_va_400_ngay(db):
    company, dept, emp = make_world(db)
    for lv, tid in ((L.SYSTEM, 0), (L.COMPANY, company.id), (L.DEPARTMENT, dept.id), (L.EMPLOYEE, emp.id)):
        s = make_schedule(db, f"M{int(lv)}", week_t2_t6_sat_am())
        assign(db, lv, tid, s.id, date(2026, 1, 1))
    db.commit()
    db.refresh(emp)   # commit làm hết hạn thuộc tính — nạp lại để không tính vào số truy vấn
    counts = []
    for span in (1, 400):
        end = MON + timedelta(days=span - 1)
        plan, sql = count_queries(db, lambda: _plan(db, emp, MON, end))
        for i in range(span):          # gọi plan KHÔNG được chạm DB
            plan(MON + timedelta(days=i))
        _, more = count_queries(db, lambda: plan(MON))
        assert more == []
        counts.append(len(sql))
    assert counts == [2, 2]


def test_effective_fallback_va_co_gan(db):
    company, dept, emp = make_world(db)
    out = resolver.effective_for_employee(db, emp, MON)
    assert out["is_fallback"] and out["schedule_id"] == 0 and out["level"] == 0
    assert out["schedule_name"] == FALLBACK_NAME and len(out["days"]) == 7
    s = make_schedule(db, "Phòng KT", week_t2_t6_sat_am())
    row = assign(db, L.DEPARTMENT, dept.id, s.id, date(2026, 1, 1))
    out = resolver.effective_for_employee(db, emp, MON)
    assert not out["is_fallback"] and out["assignment_id"] == row.id
    assert out["level"] == 3 and out["level_label"] == "Phòng ban"
    assert out["target_name"] == dept.name and out["weekly_workdays"] == 5.5
    assert out["days"][5]["start_time"] == "08:00" and out["days"][6]["start_time"] is None


def test_schedule_name_on(db):
    _, dept, emp = make_world(db)
    assert resolver.schedule_name_on(db, emp, MON) == FALLBACK_NAME
    s = make_schedule(db, "Phòng KT", week_t2_t6_sat_am())
    assign(db, L.DEPARTMENT, dept.id, s.id, date(2026, 1, 1))
    assert resolver.schedule_name_on(db, emp, MON) == "Phòng KT"
