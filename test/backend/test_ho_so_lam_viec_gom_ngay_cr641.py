"""duoc-CR-641 phase 02 — gom ngày `tab_usage_daily` từ bảng sẵn có: lịch, ngoài giờ, nghỉ phép, phiên làm việc, thiết bị,
phiếu, bấm hộ, sự kiện giao diện, nghỉ việc, idempotent, và SỐ TRUY VẤN không đổi theo số người."""
from datetime import date, timedelta

import pytest

from app.core.usage_codes import UiEventType
from app.core.work_schedule_codes import WorkScheduleLevel
from app.modules.leave.catalog_model import Holiday
from app.modules.leave.constants import LR_APPROVED, LR_DRAFT, LR_PENDING, SESSION_MORNING
from app.modules.leave.request_model import LeaveRequest
from app.modules.usage_profile.daily_builder import aggregate_day, build_rows
from app.modules.usage_profile.daily_sources import load_day_sources
from app.modules.usage_profile.daily_window import referer_to_pattern, vn_day_bounds
from app.modules.usage_profile.model import UsageDaily
from app.modules.work_schedule.day_rules import DaySpec

from ho_so_lam_viec_factory import (MON, SAT, SUN, TUE, add_audit, add_request, add_ui, make_company,
                                    make_dept, make_person, make_session, vn)
from lich_lam_viec_factory import FULL, OFF, assign, count_queries, make_schedule

from datetime import time
from app.core.work_schedule_codes import WorkDayKind

CUSTOM = DaySpec(WorkDayKind.FULL, time(7, 30), time(16, 30), time(12, 0), time(13, 0))


@pytest.fixture(autouse=True)
def dong_ho_gan_ngay_kiem(monkeypatch):
    """H3: gom lại ngày cũ hơn ~89 ngày bị từ chối — đặt «hôm nay» sát các ngày mốc (tháng 1/2026) của bài kiểm này."""
    monkeypatch.setattr("app.modules.usage_profile.daily_builder.vn_today", lambda: date(2026, 1, 20))


@pytest.fixture
def org(db):
    company = make_company(db)
    dept = make_dept(db, company)
    return company, dept


def row_of(db, user, day=MON):
    aggregate_day(db, day)
    return db.query(UsageDaily).filter_by(user_id=user.id, day=day).one()


# ── cửa sổ ngày VN ────────────────────────────────────────────────────────────

def test_bien_ngay_vn():
    lo, hi = vn_day_bounds(MON)
    assert vn(MON, "00:00") == lo and vn(MON, "23:59") < hi
    assert vn(MON + timedelta(days=1), "00:00") == hi


def test_23h30_vn_thuoc_ngay_d_06h30_hom_sau_khong(db, org):
    user, _ = make_person(db, "G1", *org)
    add_request(db, user, vn(MON, "23:30"), "POST", "/api/a")
    add_request(db, user, vn(TUE, "06:30"), "POST", "/api/a")
    db.commit()
    assert row_of(db, user, MON).api_writes == 1
    assert row_of(db, user, TUE).api_writes == 1


@pytest.mark.parametrize("referer,expected", [
    ("https://erp.x.vn/procurement/purchase-orders/129?x=1", "/procurement/purchase-orders/:id"),
    ("/hr/employees?q=nguyen", "/hr/employees"), ("", None), (None, None), ("https://erp.x.vn/", None)])
def test_referer_chi_lay_path_bo_query(referer, expected):
    assert referer_to_pattern(referer) == expected


# ── ngoài giờ theo Lịch làm việc ─────────────────────────────────────────────

def test_mac_dinh_17h_ngoai_gio_16h59_trong_gio_chu_nhat_ngoai_gio(db, org):
    user, _ = make_person(db, "G2", *org)
    add_request(db, user, vn(MON, "16:59"), "POST", "/api/a")
    add_request(db, user, vn(MON, "17:00"), "PATCH", "/api/a")
    add_request(db, user, vn(MON, "12:30"), "POST", "/api/a")       # giờ trưa tính trong giờ
    add_request(db, user, vn(MON, "09:00"), "POST", "/api/auth/refresh")   # bỏ /api/auth/*
    add_request(db, user, vn(SUN, "10:00"), "POST", "/api/a")
    db.commit()
    mon = row_of(db, user, MON)
    assert (mon.api_writes, mon.writes_offhours) == (3, 1)
    sun = row_of(db, user, SUN)
    assert (sun.is_workday, sun.api_writes, sun.writes_offhours) == (False, 1, 1)


def test_lich_rieng_07h30_16h30_16h45_la_ngoai_gio(db, org):
    user, emp = make_person(db, "G3", *org)
    sched = make_schedule(db, "Ca sớm", [CUSTOM] * 5 + [OFF, OFF])
    assign(db, WorkScheduleLevel.EMPLOYEE, emp.id, sched.id, date(2020, 1, 1))
    add_request(db, user, vn(MON, "07:45"), "POST", "/api/a")       # mặc định 08:00 thì ngoài giờ, lịch riêng thì trong
    add_request(db, user, vn(MON, "16:45"), "POST", "/api/a")       # mặc định trong giờ, lịch riêng ngoài giờ
    add_request(db, user, vn(SAT, "09:00"), "POST", "/api/a")       # lịch riêng nghỉ T7
    db.commit()
    assert row_of(db, user, MON).writes_offhours == 1
    sat = row_of(db, user, SAT)
    assert (sat.is_workday, sat.writes_offhours) == (False, 1)


# ── nghỉ phép, ngày lễ ───────────────────────────────────────────────────────

def _leave(db, emp, status, session=SESSION_MORNING, day=MON):
    r = LeaveRequest(code=f"NP{status}{emp.id}", company_id=emp.company_id, department_id=emp.department_id,
                     employee_id=emp.id, leave_type_id=0, from_date=day, to_date=day, from_session=session,
                     to_session=session, status=status)
    db.add(r)
    db.commit()


def test_nghi_phep_nua_buoi_da_duyet_tinh_0_5_cho_duyet_va_nhap_bang_0(db, org):
    approved, emp_a = make_person(db, "G4", *org)
    pending, emp_p = make_person(db, "G5", *org)
    draft, emp_d = make_person(db, "G6", *org)
    _leave(db, emp_a, LR_APPROVED)
    _leave(db, emp_p, LR_PENDING)
    _leave(db, emp_d, LR_DRAFT)
    aggregate_day(db, MON)
    got = {r.user_id: r for r in db.query(UsageDaily)}
    assert got[approved.id].leave_days == 0.5 and got[approved.id].work_capacity == 1.0
    assert got[pending.id].leave_days == 0 and got[draft.id].leave_days == 0


def test_ngay_le_khong_phai_ngay_lam_viec(db, org):
    company, _ = org
    user, _ = make_person(db, "G7", *org)
    db.add(Holiday(company_id=0, date=MON, name="Lễ", is_active=True))
    db.commit()
    r = row_of(db, user)
    assert (r.is_holiday, r.is_workday, r.work_capacity) == (True, False, 0.0)


# ── có dòng cho cả người không vào; chạy lại không nhân đôi ─────────────────

def test_nguoi_khong_vao_van_co_dong_active_false_va_chay_lai_khong_nhan_doi(db, org):
    user, _ = make_person(db, "G8", *org)
    inactive, _ = make_person(db, "G9", *org, active=False)
    aggregate_day(db, MON)
    assert aggregate_day(db, MON) == 1
    rows = db.query(UsageDaily).all()
    assert [(r.user_id, r.active, r.is_workday) for r in rows] == [(user.id, False, True)]


# ── phiên làm việc, thiết bị, mã lỗi ────────────────────────────────────────

def test_ba_luot_cach_10_phut_va_mot_luot_sau_45_phut_la_hai_phien(db, org):
    user, _ = make_person(db, "G10", *org)
    for t in ("09:00", "09:10", "09:20", "10:05"):
        add_request(db, user, vn(MON, t), "GET", "/api/a")
    db.commit()
    r = row_of(db, user)
    assert r.work_bursts == 2 and r.api_reads == 4 and r.active
    assert (r.first_seen_min, r.last_action_min) == (9 * 60, 10 * 60 + 5)
    assert r.hourly[9] == 3 and r.hourly[10] == 1


def test_luot_ghi_qua_phien_dien_thoai_va_duyet_qua_dien_thoai(db, org):
    user, _ = make_person(db, "G11", *org)
    mobile = make_session(db, user, vn(MON, "08:00"), device_type=2)
    desktop = make_session(db, user, vn(MON, "08:01"), device_type=1)
    add_request(db, user, vn(MON, "09:00"), "POST", "/api/a", session=mobile)
    add_request(db, user, vn(MON, "09:01"), "POST", "/api/a", session=desktop)
    add_audit(db, user, vn(MON, "09:02"), "leave_request", 5, "approve", group=3, session=mobile)
    add_audit(db, user, vn(MON, "09:03"), "leave_request", 6, "approve", group=3, session=desktop)
    db.commit()
    r = row_of(db, user)
    assert (r.writes_mobile, r.approvals, r.approvals_mobile, r.logins) == (1, 2, 1, 2)


def test_ma_loi_403_422_5xx_va_bao_cao_hay_mo(db, org):
    user, _ = make_person(db, "G12", *org)
    add_request(db, user, vn(MON, "09:00"), "GET", "/api/secret", status=403)
    add_request(db, user, vn(MON, "09:01"), "GET", "/api/secret", status=403)
    add_request(db, user, vn(MON, "09:02"), "POST", "/api/a", status=422)
    add_request(db, user, vn(MON, "09:03"), "POST", "/api/a", status=500)
    add_request(db, user, vn(MON, "09:04"), "GET", "/api/work/summary", status=200)
    db.commit()
    r = row_of(db, user)
    assert (r.http_403, r.http_422, r.http_5xx) == (2, 1, 1)
    assert r.forbidden_routes == {"/api/secret": 2}
    assert r.reports == {"13": 1}      # /api/work/summary gác ReportKey.WORK = 13


def test_nhieu_ip_cung_luc_trong_10_phut(db, org):
    user, _ = make_person(db, "G13", *org)
    for t, ip in (("09:00", "1.1.1.1"), ("09:05", "2.2.2.2"), ("09:08", "3.3.3.3"), ("11:00", "4.4.4.4")):
        add_request(db, user, vn(MON, t), "GET", "/api/a", ip=ip)
    db.commit()
    assert row_of(db, user).max_parallel_ips == 3


def test_ip_va_thiet_bi_chua_tung_thay(db, org):
    user, _ = make_person(db, "G14", *org)
    make_session(db, user, vn(MON - timedelta(days=10), "08:00"), ip="1.1.1.1", os_="Windows", browser="Chrome")
    make_session(db, user, vn(MON, "08:00"), ip="9.9.9.9", os_="iOS", browser="Safari", device_type=2)
    newbie, _ = make_person(db, "G15", *org)
    make_session(db, newbie, vn(MON, "08:00"), ip="5.5.5.5")      # không có lịch sử → không thể kết luận
    db.commit()
    aggregate_day(db, MON)
    got = {r.user_id: r for r in db.query(UsageDaily)}
    assert (got[user.id].new_ip_logins, got[user.id].new_device_logins) == (1, 1)
    assert (got[newbie.id].new_ip_logins, got[newbie.id].new_device_logins) == (0, 0)


# ── phiếu, xuất, xóa, bấm hộ ────────────────────────────────────────────────

def test_dem_phieu_theo_dong_tu_va_bo_entity_ngoai_danh_sach(db, org):
    user, _ = make_person(db, "G16", *org)
    for action in ("create", "update", "submit", "approved", "returned", "reject"):
        add_audit(db, user, vn(MON, "10:00"), "purchase_order", 1, action, group=3 if action != "create" else 2)
    add_audit(db, user, vn(MON, "10:01"), "supplier", 9, "create")          # ngoài whitelist
    db.commit()
    r = row_of(db, user)
    assert r.docs == {"purchase_order": {"c": 1, "u": 1, "s": 1, "a": 1, "t": 1, "r": 1}}
    assert r.docs_created == 1 and r.approvals == 3


def test_xoa_hang_loat_cua_so_truot_10_phut(db, org):
    user, _ = make_person(db, "G17", *org)
    for i, t in enumerate(("10:00", "10:02", "10:04", "11:00")):
        add_audit(db, user, vn(MON, t), "supplier", i, "delete", group=4)
    db.commit()
    r = row_of(db, user)
    assert (r.deletes, r.max_deletes_10min) == (4, 3)


def test_bam_ho_don_nghi_cua_nguoi_khac(db, org):
    creator, _ = make_person(db, "G18", *org)
    owner, emp_owner = make_person(db, "G19", *org)
    r = LeaveRequest(code="NPHO1", company_id=emp_owner.company_id, department_id=emp_owner.department_id,
                     employee_id=emp_owner.id, leave_type_id=0, from_date=TUE, to_date=TUE, status=LR_DRAFT,
                     created_by=creator.id, created_at=vn(MON, "10:00"))
    db.add(r)
    db.commit()
    aggregate_day(db, MON)
    got = {x.user_id: x for x in db.query(UsageDaily)}
    assert got[creator.id].on_behalf_done == 1 and got[owner.id].on_behalf_received == 1


# ── sự kiện giao diện ───────────────────────────────────────────────────────

def test_su_kien_giao_dien_view_dwell_form_search_va_man_dau_ngay(db, org):
    user, _ = make_person(db, "G20", *org)
    add_ui(db, user, vn(MON, "08:30"), UiEventType.PAGE_VIEW, "/a")
    add_ui(db, user, vn(MON, "08:31"), UiEventType.PAGE_LEAVE, "/a", duration=60000)
    add_ui(db, user, vn(MON, "08:32"), UiEventType.PAGE_VIEW, "/b")
    add_ui(db, user, vn(MON, "08:33"), UiEventType.FORM_OPEN, "/b", form=3)
    add_ui(db, user, vn(MON, "08:34"), UiEventType.FORM_SUBMIT, "/b", form=3, duration=90000)
    add_ui(db, user, vn(MON, "08:35"), UiEventType.FORM_OPEN, "/b", form=3)
    add_ui(db, user, vn(MON, "08:36"), UiEventType.FORM_ABANDON, "/b", form=3)
    add_ui(db, user, vn(MON, "08:37"), UiEventType.SEARCH, "/b", result=0)
    add_ui(db, user, vn(MON, "08:38"), UiEventType.SEARCH, "/b", result=4)
    add_ui(db, user, vn(MON, "08:39"), UiEventType.CLIENT_ERROR, "/b")
    db.commit()
    r = row_of(db, user)
    assert (r.page_views, r.dwell_ms, r.searches, r.searches_empty, r.client_errors) == (2, 60000, 2, 1, 1)
    assert r.first_route == "/a"
    assert r.forms == {"3": [2, 1, 1, 90000]}
    assert r.screens["/a"] == [1, 60000, 0] and r.screens["/b"][0] == 1
    assert (r.first_seen_min, r.active) == (8 * 60 + 30, True)


def test_nghi_viec_ma_van_co_request_thi_danh_dau(db, org):
    user, _ = make_person(db, "G21", *org, status="resigned", resign=MON - timedelta(days=3))
    add_request(db, user, vn(MON, "10:00"), "GET", "/api/a")
    db.commit()
    assert row_of(db, user).active_after_resign is True


def test_tran_json_16kb(db, org):
    user, _ = make_person(db, "G22", *org)
    for i in range(300):
        add_ui(db, user, vn(MON, "09:00"), UiEventType.PAGE_VIEW, f"/screen-{i}-" + "x" * 90)
    db.commit()
    r = row_of(db, user)
    import json
    assert len(json.dumps(r.screens)) <= 16 * 1024 and len(r.screens) <= 40


# ── số truy vấn cố định ────────────────────────────────────────────────────

def _populate(db, org, n, tag):
    for i in range(n):
        u, _ = make_person(db, f"{tag}{i}", *org)
        s = make_session(db, u, vn(MON, "08:00"))
        for j in range(20):
            add_request(db, u, vn(MON, f"09:{j:02d}"), "POST" if j % 3 == 0 else "GET", "/api/a", session=s,
                        referer="https://x.vn/p/1")
        for j in range(5):
            add_audit(db, u, vn(MON, "10:00"), "leave_request", i * 10 + j, "create", session=s)
        add_ui(db, u, vn(MON, "09:00"), UiEventType.PAGE_VIEW, "/a")
    db.commit()


def test_so_truy_van_khong_doi_theo_so_nguoi(db):
    org = make_company(db), None
    org = (org[0], make_dept(db, org[0]))
    _populate(db, org, 2, "A")
    _, few = count_queries(db, lambda: aggregate_day(db, MON))
    db.query(UsageDaily).delete()
    _populate(db, org, 12, "B")
    _, many = count_queries(db, lambda: aggregate_day(db, MON))
    reads = lambda sql: [s for s in sql if s.lstrip().upper().startswith("SELECT")]
    assert len(reads(few)) == len(reads(many)) and len(reads(many)) <= 20
    assert db.query(UsageDaily).filter_by(day=MON).count() == 14
