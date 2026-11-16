"""duoc-CR-761 P1 — XẾP CA THEO TIẾNG cho từng người × từng ngày (backend).

Phủ: luật khung giờ + công trừ phép (Q3) · bộ phân giải (ca theo ngày thắng mọi cấp, số truy vấn cố định) · tính ngày nghỉ
(cả ngày / nửa ngày / theo giờ / ngày nghỉ do xếp ca / ngày lễ) · quyền (Nhân sự mọi ngày; Trưởng phòng trong phạm vi, không
tự xếp, từ hôm nay; hàng loạt tất-cả-hoặc-không) · chuông · "Ai làm / ai nghỉ" trả ca · trần đầu vào ở tầng schema.
Mốc ngày cố định `MON` = 05/01/2026 (thứ Hai); bài API dùng ngày theo `vn_today()` vì luật "từ hôm nay" đọc đồng hồ.
"""
import uuid
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.scoping import get_perm_profile
from app.core.vn_time import vn_today
from app.core.work_schedule_codes import WorkDayKind, WorkScheduleLevel as L
from app.main import app
from app.modules.assistant import tools as T
from app.modules.audit.model import AuditLog
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.leave.catalog_model import Holiday, LeaveType
from app.modules.leave.constants import (LR_APPROVED, LR_PENDING, SESSION_AFTERNOON, SESSION_FULL,
                                         SESSION_MORNING)
from app.modules.leave.request_model import LeaveRequest
from app.modules.leave import workday_service
from app.modules.notification.model import Notification
from app.modules.user.model import User
from app.modules.work_schedule import resolver
from app.modules.work_schedule.day_rules import (day_capacity, day_hours, leave_credit, shift_spec,
                                                 shift_window_mask, work_mask, worked_hours)
from app.modules.work_schedule.model import WorkShiftDay, WorkShiftSegment
from app.modules.work_schedule.resolver_many import load_day_plans_many
from app.modules.work_schedule.roster_service import build_roster
from app.modules.work_schedule.shift_rules import MAX_SEGMENTS, normalize_segments
from app.modules.work_schedule.shift_schema import ShiftBulk, ShiftCopyWeek, ShiftPut
from lich_lam_viec_factory import (FULL, MON, OFF, SAT, SAT_AM, SUN, assign, count_queries, make_schedule,
                                   make_world)

TUE, WED = MON + timedelta(days=1), MON + timedelta(days=2)
LIVESTREAM = [(8, 10), (14, 16), (20, 23)]   # 2 + 2 + 3 = 7 giờ, ba khung rời nhau


def put_shift(db, emp, day, segments, note=""):
    """Dựng thẳng một ngày xếp ca (không qua API) để bài tính ngày / phân giải không phụ thuộc quyền."""
    row = WorkShiftDay(employee_id=emp.id, work_date=day, note=note)
    db.add(row)
    db.flush()
    for order, (a, b) in enumerate(segments):
        db.add(WorkShiftSegment(shift_day_id=row.id, start_hour=a, end_hour=b, sort_order=order))
    db.flush()
    return row


def _days(db, emp, a, b, fs=SESSION_FULL, ts=SESSION_FULL, **kw):
    return workday_service.count_leave_days(db, a, b, fs, ts, employee=emp, **kw)


def _hours(db, emp, a, b, ft, tt):
    return workday_service.count_hourly_days(db, a, b, ft, tt, employee=emp)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Luật khung giờ + công trừ phép (thuần)
# ══════════════════════════════════════════════════════════════════════════════

def test_shift_spec_nua_buoi_theo_moc_12h():
    assert work_mask(shift_spec([(13, 17)])) == 2          # chỉ chiều
    assert work_mask(shift_spec([(6, 10)])) == 1           # chỉ sáng
    assert work_mask(shift_spec([(10, 14)])) == 3          # vắt qua 12:00 = cả hai nửa
    assert work_mask(shift_spec([(8, 12)])) == 1           # hết đúng 12:00 vẫn là sáng
    assert work_mask(shift_spec([(12, 17)])) == 2          # từ đúng 12:00 là chiều
    assert shift_spec(LIVESTREAM).kind is WorkDayKind.FULL
    assert shift_spec([]).kind is WorkDayKind.OFF and shift_spec([]).segments == ()


def test_gio_gio_tron_va_24h_khong_mat_phut():
    spec = shift_spec(LIVESTREAM)
    assert day_hours(spec) == 7.0 and day_capacity(spec) == 1.0
    assert worked_hours(spec, time(14), time(16)) == 2.0
    assert worked_hours(spec, time(10), time(14)) == 0.0   # khe giữa các khung không tính
    night = shift_spec([(20, 24)])
    assert night.end == time.max
    assert worked_hours(night, time(22), time.max) == 2.0  # time.max = 24:00, không rơi mất 1 phút
    assert day_hours(night) == 4.0
    assert day_capacity(shift_spec([])) == 0.0 and day_hours(shift_spec([])) == 0.0


def test_leave_credit_ngay_theo_mau_khong_doi():
    from app.modules.work_schedule.day_rules import FALLBACK_WEEK
    assert leave_credit(FALLBACK_WEEK[0], 3) == 1.0 and leave_credit(FALLBACK_WEEK[0], 1) == 0.5
    assert leave_credit(FALLBACK_WEEK[6], 3) == 0.0        # Chủ nhật nghỉ


@pytest.mark.parametrize("segments,mask,expected", [
    ([(13, 17)], 3, 1.0),      # nghỉ cả ngày trừ 1 dù ca chỉ ở buổi chiều
    ([(13, 17)], 1, 0.0),      # nghỉ buổi sáng mà không có ca sáng = 0
    ([(13, 17)], 2, 1.0),      # nửa chiều chứa TOÀN BỘ giờ ca → trừ 1 (nghỉ hết ca = nghỉ cả ngày công)
    ([(6, 10)], 1, 1.0),
    ([(6, 10)], 2, 0.0),       # ca sáng mà nghỉ chiều
    ([(10, 14)], 1, 0.5),      # ca nằm ở cả hai nửa → nửa ngày = 0.5
    ([(10, 14)], 2, 0.5),
    ([], 3, 0.0),              # ngày nghỉ do xếp ca
    (LIVESTREAM, 0, 0.0),
])
def test_leave_credit_ngay_xep_ca(segments, mask, expected):
    assert leave_credit(shift_spec(segments), mask) == expected


def test_shift_window_mask_cho_don_theo_gio():
    spec = shift_spec(LIVESTREAM)
    assert shift_window_mask(spec, 14 * 60, 16 * 60) == 2          # 14–16 chỉ chạm chiều
    assert shift_window_mask(spec, 9 * 60, 15 * 60) == 3           # 9–15 chạm cả sáng lẫn chiều
    assert shift_window_mask(spec, 10 * 60, 14 * 60) == 0          # đúng khe giữa
    assert shift_window_mask(shift_spec([]), 0, 1440) == 0


def test_normalize_segments_sap_va_chan_sai():
    assert normalize_segments([(14, 16), (8, 10)]) == [(8, 10), (14, 16)]
    assert normalize_segments([(8, 10), (10, 12)]) == [(8, 10), (10, 12)]   # chạm nhau không chồng
    assert normalize_segments([]) == []
    for bad in ([(8, 8)], [(10, 8)], [(8, 11), (10, 12)], [(-1, 5)], [(0, 25)], [(24, 24)]):
        with pytest.raises(ValueError):
            normalize_segments(bad)
    with pytest.raises(ValueError):
        normalize_segments([(i, i + 1) for i in range(MAX_SEGMENTS + 1)])
    assert len(normalize_segments([(i * 2, i * 2 + 1) for i in range(MAX_SEGMENTS)])) == MAX_SEGMENTS


# ══════════════════════════════════════════════════════════════════════════════
# 2. Bộ phân giải: ca theo ngày thắng mọi cấp
# ══════════════════════════════════════════════════════════════════════════════

def test_ca_theo_ngay_thang_moi_cap_gan(db):
    company, dept, emp = make_world(db)
    other = Employee(code="NV002", full_name="Người khác", company_id=company.id, department_id=dept.id,
                     is_active=True)
    db.add(other)
    db.flush()
    sched = make_schedule(db, "Nhân sự T2-T6, T7 sáng", [FULL] * 5 + [SAT_AM, OFF])
    assign(db, L.EMPLOYEE, emp.id, sched.id, date(2026, 1, 1))
    assign(db, L.DEPARTMENT, dept.id, make_schedule(db, "Phòng", [OFF] * 7).id, date(2026, 1, 1))
    put_shift(db, emp, SUN, [(8, 10)])               # Chủ nhật: mẫu nghỉ, ca xếp vẫn thắng
    put_shift(db, emp, TUE, [])                       # ngày nghỉ do xếp ca
    put_shift(db, other, WED, [(14, 16)])             # ca của NGƯỜI KHÁC không lọt sang
    db.commit()
    plan = resolver.load_day_plans(db, employee_id=emp.id, department_id=dept.id,
                                   company_id=company.id, from_date=MON, to_date=SUN)
    assert plan(SUN).segments == ((8, 10),) and work_mask(plan(SUN)) == 1
    assert plan(TUE).segments == () and plan(TUE).kind is WorkDayKind.OFF
    assert plan(MON).segments is None and plan(MON).kind is WorkDayKind.FULL      # ngày không xếp: theo mẫu
    assert plan(WED).segments is None and plan(SAT).kind is WorkDayKind.MORNING
    many = load_day_plans_many(db, [emp, other], MON, SUN)
    assert many.at(emp.id, SUN)[0].segments == ((8, 10),) and many.shift_at(emp.id, SUN).segments == ((8, 10),)
    assert many.at(other.id, WED)[0].segments == ((14, 16),)
    assert many.shift_at(other.id, TUE) is None and many.at(other.id, TUE)[0].segments is None


def test_phan_giai_so_truy_van_co_dinh_khi_co_ca(db):
    company, dept, emp = make_world(db)
    for i in range(30):
        put_shift(db, emp, MON + timedelta(days=i), [(8, 10), (14, 16)])
    ids = (emp.id, dept.id, company.id)   # lấy trước commit: thuộc tính hết hạn sẽ tự nạp lại và tính vào số truy vấn
    db.commit()
    counts = []
    for span in (1, 30):
        end = MON + timedelta(days=span - 1)
        plan, sql = count_queries(db, lambda: resolver.load_day_plans(
            db, employee_id=ids[0], department_id=ids[1], company_id=ids[2], from_date=MON, to_date=end))
        _, more = count_queries(db, lambda: [plan(MON + timedelta(days=i)) for i in range(span)])
        assert more == []
        counts.append(len(sql))
    assert counts[0] == counts[1] <= 3
    who = [SimpleNamespace(id=ids[0], department_id=ids[1], company_id=ids[2])]
    _, many_small = count_queries(db, lambda: load_day_plans_many(db, who, MON, MON))
    _, many_big = count_queries(db, lambda: load_day_plans_many(db, who, MON, MON + timedelta(days=29)))
    assert len(many_small) == len(many_big) <= 4


# ══════════════════════════════════════════════════════════════════════════════
# 3. Tính ngày nghỉ (Q3)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def emp(db):
    return make_world(db)[2]


def test_nghi_ca_ngay_tren_ngay_xep_ca_tru_mot(db, emp):
    put_shift(db, emp, MON, LIVESTREAM)
    put_shift(db, emp, TUE, [(13, 17)])               # ca chỉ buổi chiều
    db.commit()
    assert _days(db, emp, MON, MON) == 1.0
    assert _days(db, emp, TUE, TUE) == 1.0            # vẫn là một ngày công
    assert _days(db, emp, MON, WED) == 3.0            # MON + TUE ca xếp, WED theo mẫu: 1 + 1 + 1


def test_nghi_nua_ngay_chi_tinh_nua_co_gio_ca(db, emp):
    put_shift(db, emp, MON, [(13, 17)])                # chỉ chiều
    put_shift(db, emp, TUE, [(6, 10)])                 # chỉ sáng
    put_shift(db, emp, WED, [(10, 14)])                # vắt qua 12:00
    db.commit()
    #  Một ngày: SESSION_FULL→SESSION_MORNING = chỉ buổi sáng; SESSION_AFTERNOON→SESSION_FULL = chỉ buổi chiều.
    assert _days(db, emp, MON, MON, SESSION_FULL, SESSION_MORNING) == 0.0        # ca chiều + nghỉ sáng = 0
    assert _days(db, emp, MON, MON, SESSION_AFTERNOON, SESSION_FULL) == 1.0      # ca chiều + nghỉ chiều = hết ca → 1.0
    assert _days(db, emp, TUE, TUE, SESSION_AFTERNOON, SESSION_FULL) == 0.0      # ca sáng + nghỉ chiều = 0
    assert _days(db, emp, TUE, TUE, SESSION_FULL, SESSION_MORNING) == 1.0        # ca sáng + nghỉ sáng = hết ca → 1.0
    assert _days(db, emp, WED, WED, SESSION_FULL, SESSION_MORNING) == 0.5
    assert _days(db, emp, WED, WED, SESSION_AFTERNOON, SESSION_FULL) == 0.5


def test_ngay_nghi_do_xep_ca_khong_tru_phep(db, emp):
    put_shift(db, emp, MON, [])
    db.commit()
    assert _days(db, emp, MON, MON) == 0.0
    assert _days(db, emp, MON, TUE) == 1.0             # chỉ TUE (theo mẫu) tính
    assert _hours(db, emp, MON, MON, time(9), time(10)) == 0.0


def test_ca_xep_thang_mau_nghi_chu_nhat(db, emp):
    assert _days(db, emp, SUN, SUN) == 0.0             # đối chứng: CN theo mẫu là nghỉ
    put_shift(db, emp, SUN, [(8, 12)])
    db.commit()
    assert _days(db, emp, SUN, SUN) == 1.0


def test_nghi_theo_gio_chia_cho_tong_gio_ca_livestream(db, emp):
    put_shift(db, emp, MON, LIVESTREAM)
    db.commit()
    assert _hours(db, emp, MON, MON, time(14), time(16)) == pytest.approx(round(2 / 7, 2))   # 0.29
    assert _hours(db, emp, MON, MON, time(9), time(15)) == pytest.approx(round(2 / 7, 2))    # 9–10 + 14–15
    assert _hours(db, emp, MON, MON, time(10), time(14)) == 0.0                              # đúng khe giữa
    assert _hours(db, emp, MON, MON, time(0), time(23, 59)) == 1.0                           # trọn ca = 1 ngày
    assert _hours(db, emp, MON, MON, time(8), time(10)) == pytest.approx(round(2 / 7, 2))


def test_nghi_theo_gio_nhieu_ngay_tron_ca_va_ngay_mau(db, emp):
    put_shift(db, emp, MON, LIVESTREAM)
    db.commit()
    #  MON từ 14:00 hết ngày = 2 + 3 = 5 giờ / 7; TUE (mẫu 8h) tới 10:00 = 2 / 8.
    got = _hours(db, emp, MON, TUE, time(14), time(10))
    assert got == pytest.approx(round(5 / 7 + 2 / 8, 2))


def test_ngay_le_van_bi_bo_qua_tren_ngay_xep_ca(db, emp):
    db.add(Holiday(company_id=0, date=MON, name="Lễ", is_recurring=False, is_active=True))
    put_shift(db, emp, MON, LIVESTREAM)
    db.commit()
    assert _days(db, emp, MON, MON) == 0.0
    assert _hours(db, emp, MON, MON, time(14), time(16)) == 0.0
    assert _days(db, emp, MON, TUE) == 1.0


def test_loai_nghi_khong_bo_qua_lich_thi_khong_doc_ca(db, emp):
    put_shift(db, emp, MON, [])
    db.commit()
    assert _days(db, emp, MON, MON, exclude_holiday=False) == 1.0   # thai sản: đếm theo lịch dương như cũ


def test_ngay_khong_xep_ca_giu_nguyen_ket_qua_cu(db, emp):
    other_day = MON + timedelta(days=7)
    put_shift(db, emp, other_day, [])                  # ca ở một tuần khác không làm đổi tuần này
    db.commit()
    assert _days(db, emp, MON, SUN) == 6.0
    assert _days(db, emp, SAT, SUN, SESSION_AFTERNOON, SESSION_FULL) == 0.5


# ══════════════════════════════════════════════════════════════════════════════
# 4. Roster trả ca
# ══════════════════════════════════════════════════════════════════════════════

def _admin(db, cap_quyen, tag):
    user = User(email=f"{tag}@dego.vn", employee_id=0, is_active=True)
    db.add(user)
    db.commit()
    cap_quyen(user.id, "employee", scope="all", read=True)
    cap_quyen(user.id, "work_schedule", scope="all", read=True, write=True)   # Nhân sự: thấy mọi người trong phạm vi employee (duoc-CR-761)
    cap_quyen(user.id, "leave_request", scope="all", read=True)
    return user


def _roster(db, user, profile=None, **kw):
    p = {"from_date": MON, "to_date": MON + timedelta(days=6), "company_id": 0, "department_id": 0, "q": "",
         "page": 1, "page_size": 50, **kw}
    return build_roster(db, user, profile or get_perm_profile(db, user), p)


def test_roster_tra_thong_tin_ca(db, cap_quyen):
    user = _admin(db, cap_quyen, "rs758")
    company, dept, emp = make_world(db, "RS1")
    put_shift(db, emp, MON, LIVESTREAM, note="Phát trực tiếp")
    put_shift(db, emp, TUE, [])
    put_shift(db, emp, WED, [(20, 24)])
    db.commit()
    cells = _roster(db, user)["items"][0]["cells"]
    mon, tue, wed, thu = cells[0], cells[1], cells[2], cells[3]
    assert mon["is_shift"] and mon["work_kind"] == int(WorkDayKind.FULL)
    assert mon["shift"] == {"segments": ["08:00–10:00", "14:00–16:00", "20:00–23:00"],
                            "ranges": [[8, 10], [14, 16], [20, 23]], "hours": 7.0, "note": "Phát trực tiếp",
                            "is_day_off": False}
    assert (mon["start_time"], mon["end_time"], mon["schedule_name"]) == ("08:00", "23:00", "Xếp ca theo ngày")
    assert tue["is_shift"] and tue["shift"]["is_day_off"] and tue["work_kind"] == int(WorkDayKind.OFF)
    assert tue["start_time"] is None and tue["shift"]["segments"] == []
    assert wed["shift"]["segments"] == ["20:00–24:00"] and wed["end_time"] == "24:00"
    assert not thu["is_shift"] and thu["shift"] is None and thu["work_kind"] == int(WorkDayKind.FULL)


def test_roster_lop_nghi_phep_tren_ngay_xep_ca(db, cap_quyen):
    user = _admin(db, cap_quyen, "rs758b")
    company, dept, emp = make_world(db, "RS2")
    db.add(LeaveType(code="PN", name="Phép năm", is_active=True))
    db.flush()
    put_shift(db, emp, MON, [(13, 17)])
    db.add(LeaveRequest(code="NP-758-1", company_id=company.id, department_id=dept.id, employee_id=emp.id,
                        leave_type_id=0, from_date=MON, to_date=MON, from_session=SESSION_FULL,
                        to_session=SESSION_FULL, status=LR_APPROVED))
    db.commit()
    leave = _roster(db, user)["items"][0]["cells"][0]["leave"]
    assert leave is not None and leave["afternoon"] and not leave["morning"]   # ca chỉ buổi chiều → tô nửa chiều


def test_roster_so_truy_van_co_dinh_khi_co_ca(db, cap_quyen):
    user = _admin(db, cap_quyen, "rs758c")
    company, dept, _ = make_world(db, "RS3")
    for i in range(30):
        e = Employee(code=f"RQ{i:03d}", full_name=f"Người RQ{i:03d}", company_id=company.id,
                     department_id=dept.id, is_active=True)
        db.add(e)
        db.flush()
        for d in range(0, 42, 3):
            put_shift(db, e, MON + timedelta(days=d), [(8, 10), (14, 16)])
    db.commit()
    profile = get_perm_profile(db, user)   # ngoài phần đếm: hồ sơ quyền không thuộc số truy vấn của lưới
    small, q_small = count_queries(db, lambda: _roster(db, user, profile, page_size=3, to_date=MON + timedelta(days=6)))
    big, q_big = count_queries(db, lambda: _roster(db, user, profile, page_size=30, to_date=MON + timedelta(days=41)))
    assert len(small["items"]) == 3 and len(big["items"]) == 30
    assert sum(1 for c in big["items"][0]["cells"] if c["is_shift"]) == 14
    assert len(q_small) == len(q_big) <= 11, [s[:60] for s in q_big]   # 8 + 2 truy vấn của cờ `leave_hold` + 1 nếu có đơn chưa có dòng khoảng


# ══════════════════════════════════════════════════════════════════════════════
# 5. API: quyền, ghi, hàng loạt, chép tuần, chuông, ca của tôi
# ══════════════════════════════════════════════════════════════════════════════

URL = "/api/work-shifts"
NOT_FOUND = "Nhân sự được xếp ca không tồn tại hoặc ngoài phạm vi của bạn"


class World:
    """Một công ty, hai phòng: A của trưởng phòng `mgr` (a1, a2), B phòng khác (b1); `hr` là Nhân sự (phòng B)."""


def _emp(db, code, company, dept_id):
    e = Employee(code=code, full_name=f"Người {code}", company_id=company.id, department_id=dept_id, is_active=True)
    db.add(e)
    db.flush()
    return e


def _user(db, emp, email):
    u = User(email=email, employee_id=emp.id, password_hash="x", is_active=True)
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def w(db, cap_quyen):
    world = World()
    world.company = Company(name="Cty 758", code="C758", is_active=True)
    db.add(world.company)
    db.flush()
    world.dept_a = Department(code="D758A", name="Phòng A", company_id=world.company.id, is_active=True)
    world.dept_b = Department(code="D758B", name="Phòng B", company_id=world.company.id, is_active=True)
    db.add_all([world.dept_a, world.dept_b])
    db.flush()
    world.mgr = _emp(db, "TP758", world.company, world.dept_a.id)
    world.a1 = _emp(db, "A1758", world.company, world.dept_a.id)
    world.a2 = _emp(db, "A2758", world.company, world.dept_a.id)
    world.b1 = _emp(db, "B1758", world.company, world.dept_b.id)
    world.hr = _emp(db, "HR758", world.company, world.dept_b.id)
    world.mgr_user = _user(db, world.mgr, "tp758@dego.vn")
    world.a1_user = _user(db, world.a1, "a1758@dego.vn")
    world.a2_user = _user(db, world.a2, "a2758@dego.vn")
    world.b1_user = _user(db, world.b1, "b1758@dego.vn")
    world.hr_user = _user(db, world.hr, "hr758@dego.vn")
    #  Trưởng phòng: khóa riêng bậc phòng + đọc hồ sơ bậc phòng. Nhân sự: khóa cũ mọi phạm vi.
    cap_quyen(world.mgr_user.id, "work_schedule_personal", scope="dept", read=True, create=True, write=True,
              delete=True)
    cap_quyen(world.mgr_user.id, "employee", scope="dept", read=True)
    cap_quyen(world.hr_user.id, "work_schedule", scope="all", read=True, create=True, write=True, delete=True)
    cap_quyen(world.hr_user.id, "employee", scope="all", read=True)
    #  Đọc đơn nghỉ: Nhân sự thấy mọi đơn, Trưởng phòng thấy đơn của phòng mình (quyết định mã đơn có được lộ không).
    cap_quyen(world.hr_user.id, "leave_request", scope="all", read=True)
    cap_quyen(world.mgr_user.id, "leave_request", scope="dept", read=True)
    cap_quyen(world.a1_user.id, "employee", scope="own", read=True)
    db.commit()
    return world


class _Actor:
    """Máy khách gắn với MỘT tài khoản. Phụ thuộc `get_current_user` là một ô chung của `app`, nên mỗi lời gọi gắn lại
    tài khoản của mình — nhờ vậy một bài dùng được nhiều người (`hr` rồi `mgr`) mà không dẫm lên nhau."""

    def __init__(self, client, user):
        self._client, self._user = client, user

    def _call(self, method, *args, **kwargs):
        app.dependency_overrides[get_current_user] = lambda: self._user
        return getattr(self._client, method)(*args, **kwargs)

    def get(self, *a, **kw):
        return self._call("get", *a, **kw)

    def put(self, *a, **kw):
        return self._call("put", *a, **kw)

    def post(self, *a, **kw):
        return self._call("post", *a, **kw)

    def delete(self, *a, **kw):
        return self._call("delete", *a, **kw)


@pytest.fixture
def client_as(db):
    def _make(user):
        app.dependency_overrides[get_db] = lambda: db
        return _Actor(TestClient(app, headers={"Authorization": f"Bearer t-{uuid.uuid4().hex}"}), user)

    yield _make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _future_monday():
    today = vn_today()
    return today + timedelta(days=7 - today.weekday())


def _seg(*pairs):
    return [{"start_hour": a, "end_hour": b} for a, b in pairs]


def _rows(db, emp=None):
    q = db.query(WorkShiftDay)
    return q.filter(WorkShiftDay.employee_id == emp.id).all() if emp else q.all()


def _segments_of(db, emp, day):
    row = db.query(WorkShiftDay).filter_by(employee_id=emp.id, work_date=day).one()
    return [(s.start_hour, s.end_hour) for s in db.query(WorkShiftSegment)
            .filter_by(shift_day_id=row.id).order_by(WorkShiftSegment.sort_order)]


def _put(client, emp, day, segments, note=""):
    return client.put(f"{URL}/{emp.id}/{day.isoformat()}", json={"segments": _seg(*segments), "note": note})


def test_nhan_su_xep_ca_moi_ngay_ke_ca_qua_khu_nhung_khong_cho_chinh_minh(db, w, client_as):
    hr = client_as(w.hr_user)
    past = vn_today() - timedelta(days=10)
    res = _put(hr, w.b1, past, [(14, 16), (8, 10)], "Livestream")      # gửi lộn xộn, lưu theo thứ tự giờ
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["segments"] == [{"start_hour": 8, "end_hour": 10, "label": "08:00–10:00"},
                                {"start_hour": 14, "end_hour": 16, "label": "14:00–16:00"}]
    assert data["hours"] == 4.0 and data["note"] == "Livestream" and not data["is_day_off"]
    assert data["employee_id"] == w.b1.id and data["work_date"] == past.isoformat()
    assert _segments_of(db, w.b1, past) == [(8, 10), (14, 16)]
    assert _put(hr, w.a1, vn_today(), [(8, 12)]).status_code == 200          # người phòng khác với Nhân sự
    assert _put(hr, w.hr, vn_today(), [(8, 12)]).status_code == 403          # nhưng KHÔNG tự xếp cho chính mình


def test_dat_lai_thay_ca_khung_va_nghi_ca_ngay(db, w, client_as):
    hr = client_as(w.hr_user)
    day = _future_monday()
    assert _put(hr, w.a1, day, [(8, 10), (14, 16)]).status_code == 200
    res = _put(hr, w.a1, day, [(9, 11)])
    assert res.status_code == 200 and _segments_of(db, w.a1, day) == [(9, 11)]
    assert len(_rows(db, w.a1)) == 1                                             # cập nhật tại chỗ, không nhân đôi
    off = _put(hr, w.a1, day, [])
    assert off.status_code == 200 and off.json()["data"]["is_day_off"] and _segments_of(db, w.a1, day) == []


def test_truong_phong_xep_ca_phong_minh_tu_hom_nay(db, w, client_as):
    mgr = client_as(w.mgr_user)
    today, future = vn_today(), _future_monday()
    assert _put(mgr, w.a1, today, [(8, 12)]).status_code == 200
    assert _put(mgr, w.a2, future, LIVESTREAM).status_code == 200
    past = _put(mgr, w.a1, today - timedelta(days=1), [(8, 12)])
    assert past.status_code == 422 and past.json()["error"]["message"] == "Chỉ xếp ca từ hôm nay trở đi"
    other = _put(mgr, w.b1, future, [(8, 12)])
    assert other.status_code == 400 and other.json()["error"]["message"] == NOT_FOUND
    self_ = _put(mgr, w.mgr, future, [(8, 12)])
    assert self_.status_code == 403 and "tự xếp ca" in self_.json()["error"]["message"]
    assert [r.employee_id for r in _rows(db)] == [w.a1.id, w.a2.id]             # chỉ hai ô hợp lệ được ghi


def test_khong_ton_tai_va_ngoai_pham_vi_cung_mot_cau(db, w, client_as):
    mgr = client_as(w.mgr_user)
    ghost = mgr.put(f"{URL}/999999/{_future_monday().isoformat()}", json={"segments": _seg((8, 12))})
    assert ghost.status_code == 400 and ghost.json()["error"]["message"] == NOT_FOUND


def test_khong_co_khoa_xep_ca_bi_403(db, w, client_as):
    nv = client_as(w.a1_user)                                                    # chỉ đọc hồ sơ của mình
    assert _put(nv, w.a2, _future_monday(), [(8, 12)]).status_code == 403
    assert nv.delete(f"{URL}/{w.a2.id}/{_future_monday().isoformat()}").status_code == 403
    assert nv.post(f"{URL}/bulk", json={"employee_ids": [w.a2.id], "dates": [_future_monday().isoformat()],
                                        "segments": _seg((8, 12))}).status_code == 403


def test_go_ca_ve_mau_tuan(db, w, client_as):
    hr, mgr = client_as(w.hr_user), client_as(w.mgr_user)
    day = _future_monday()
    _put(hr, w.a1, day, [(8, 12)])
    res = mgr.delete(f"{URL}/{w.a1.id}/{day.isoformat()}")
    assert res.status_code == 200 and res.json()["data"] == {"deleted": True} and _rows(db, w.a1) == []
    assert db.query(WorkShiftSegment).count() == 0                               # khung cũng dọn sạch
    again = mgr.delete(f"{URL}/{w.a1.id}/{day.isoformat()}")
    assert again.status_code == 200 and again.json()["data"] == {"deleted": False}
    assert mgr.delete(f"{URL}/{w.b1.id}/{day.isoformat()}").status_code == 400      # ngoài phạm vi
    assert mgr.delete(f"{URL}/{w.mgr.id}/{day.isoformat()}").status_code == 403      # chính mình


def test_khong_ai_go_duoc_ca_cua_hom_nay_va_ngay_da_qua(db, w, client_as):
    """Gỡ ca về mẫu tuần chỉ cho ngày TƯƠNG LAI, kể cả Nhân sự — sửa ngày đã / đang diễn ra thì đặt lại khung (PUT)."""
    hr, mgr = client_as(w.hr_user), client_as(w.mgr_user)
    message = "Ngày đã qua (hoặc hôm nay) không về mẫu tuần được — sửa khung giờ thay vì xóa"
    for day in (vn_today() - timedelta(days=2), vn_today()):
        _put(hr, w.a1, day, [])                                                   # ngày nghỉ do xếp ca
        for who in (hr, mgr):
            res = who.delete(f"{URL}/{w.a1.id}/{day.isoformat()}")
            assert res.status_code == 422 and res.json()["error"]["message"] == message
        assert _segments_of(db, w.a1, day) == []                                  # còn nguyên
        assert _put(hr, w.a1, day, [(8, 12)]).status_code == 200                  # sửa khung vẫn được (Nhân sự)
    tomorrow = vn_today() + timedelta(days=1)
    _put(hr, w.a1, tomorrow, [(8, 12)])
    assert hr.delete(f"{URL}/{w.a1.id}/{tomorrow.isoformat()}").json()["data"] == {"deleted": True}


def test_ap_hang_loat_tat_ca_hoac_khong(db, w, client_as):
    mgr = client_as(w.mgr_user)
    mon = _future_monday()
    dates = [(mon + timedelta(days=i)).isoformat() for i in range(3)]
    ok = mgr.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id, w.a2.id], "dates": dates,
                                       "segments": _seg((8, 10), (14, 16)), "note": "Đợt sale"})
    assert ok.status_code == 200 and ok.json()["data"] == {"created": 6, "updated": 0, "changed": 6}
    assert len(_rows(db)) == 6 and _segments_of(db, w.a2, mon + timedelta(days=2)) == [(8, 10), (14, 16)]
    assert mgr.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id], "dates": dates[:1],
                                         "segments": _seg((9, 11))}).json()["data"]["updated"] == 1
    #  Một người ngoài phạm vi trong danh sách → không ghi ô nào, kể cả ô hợp lệ của người khác.
    before = len(_rows(db))
    bad = mgr.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id, w.b1.id], "dates": [dates[0]],
                                        "segments": _seg((7, 9))})
    body = bad.json()
    assert bad.status_code == 400 and body["error"]["code"] == "shift_rejected"
    assert body["error"]["details"]["rejected"] == [{"employee_id": w.b1.id, "work_date": None,
                                                     "code": "not_found", "message": NOT_FOUND}]
    assert len(_rows(db)) == before and _segments_of(db, w.a1, mon) == [(9, 11)]    # ô a1 không bị đổi thành 7–9
    #  Ô quá khứ → 422 + liệt kê từng ô, không ghi gì.
    yesterday = (vn_today() - timedelta(days=1)).isoformat()
    past = mgr.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id, w.a2.id], "dates": [yesterday, dates[0]],
                                         "segments": _seg((7, 9))})
    assert past.status_code == 422
    assert {(r["employee_id"], r["work_date"], r["code"]) for r in past.json()["error"]["details"]["rejected"]} == {
        (w.a1.id, yesterday, "past_date"), (w.a2.id, yesterday, "past_date")}
    assert len(_rows(db)) == before
    #  Có chính mình trong danh sách → 403, danh sách nêu đúng người đó.
    self_ = mgr.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id, w.mgr.id], "dates": [dates[0]],
                                          "segments": _seg((7, 9))})
    assert self_.status_code == 403
    assert [r["code"] for r in self_.json()["error"]["details"]["rejected"]] == ["self"]
    assert len(_rows(db)) == before


def test_nhan_su_ap_hang_loat_ca_phong_khac_va_ngay_qua_khu(db, w, client_as):
    hr = client_as(w.hr_user)
    day = (vn_today() - timedelta(days=5)).isoformat()
    res = hr.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id, w.b1.id], "dates": [day],
                                       "segments": _seg((8, 17))})
    assert res.status_code == 200 and res.json()["data"]["created"] == 2
    own = hr.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id, w.hr.id], "dates": [day], "segments": _seg((9, 12))})
    assert own.status_code == 403 and own.json()["error"]["details"]["rejected"][0]["code"] == "self"
    assert _segments_of(db, w.a1, date.fromisoformat(day)) == [(8, 17)]          # không ghi ô nào


def test_tran_so_o_hang_loat(w, client_as):
    mgr = client_as(w.mgr_user)
    ids = list(range(1, 52))
    assert mgr.post(f"{URL}/bulk", json={"employee_ids": ids, "dates": ["2026-12-01"],
                                         "segments": []}).status_code == 422     # 51 người
    dates = [(date(2027, 1, 1) + timedelta(days=i)).isoformat() for i in range(11)]
    assert mgr.post(f"{URL}/bulk", json={"employee_ids": ids[:50], "dates": dates,
                                         "segments": []}).status_code == 422     # 550 ô


def test_chep_tuan_chi_chep_ngay_da_xep_ca(db, w, client_as):
    hr, mgr = client_as(w.hr_user), client_as(w.mgr_user)
    src, dst = _future_monday(), _future_monday() + timedelta(days=7)
    _put(hr, w.a1, src, [(8, 10), (14, 16)], "Sale")
    _put(hr, w.a1, src + timedelta(days=2), [])                    # ngày nghỉ do xếp ca cũng được chép
    _put(hr, w.a2, src + timedelta(days=4), [(9, 12)])
    body = {"employee_ids": [w.a1.id, w.a2.id], "source_week_start": src.isoformat(),
            "target_week_start": dst.isoformat()}
    res = mgr.post(f"{URL}/copy-week", json=body)
    assert res.status_code == 200 and res.json()["data"] == {"created": 3, "updated": 0, "skipped": 0, "skipped_past": 0,
                                             "skipped_leave": 0, "leave_conflicts": [], "changed": 3}
    assert _segments_of(db, w.a1, dst) == [(8, 10), (14, 16)] and _segments_of(db, w.a1, dst + timedelta(days=2)) == []
    assert _segments_of(db, w.a2, dst + timedelta(days=4)) == [(9, 12)]
    assert db.query(WorkShiftDay).filter_by(employee_id=w.a1.id, work_date=dst + timedelta(days=1)).count() == 0
    _put(hr, w.a1, dst, [(10, 11)])                                # đích đã được chỉnh tay
    again = mgr.post(f"{URL}/copy-week", json=body).json()["data"]
    assert again == {"created": 0, "updated": 0, "skipped": 3, "skipped_past": 0, "skipped_leave": 0,
                     "leave_conflicts": [], "changed": 0}   # không ghi đè
    assert _segments_of(db, w.a1, dst) == [(10, 11)]
    over = mgr.post(f"{URL}/copy-week", json={**body, "overwrite": True}).json()["data"]
    assert over == {"created": 0, "updated": 3, "skipped": 0, "skipped_past": 0, "skipped_leave": 0,
                    "leave_conflicts": [], "changed": 3}
    assert _segments_of(db, w.a1, dst) == [(8, 10), (14, 16)]


def test_chep_tuan_chan_nguoi_ngoai_pham_vi_va_ngay_qua_khu_khong_ghi_gi(db, w, client_as):
    hr, mgr = client_as(w.hr_user), client_as(w.mgr_user)
    this_monday = vn_today() - timedelta(days=vn_today().weekday())
    last = this_monday - timedelta(days=7)
    _put(hr, w.a1, last + timedelta(days=1), [(8, 12)])
    _put(hr, w.b1, last + timedelta(days=1), [(8, 12)])
    base = {"source_week_start": last.isoformat(), "target_week_start": (this_monday + timedelta(days=7)).isoformat()}
    out = mgr.post(f"{URL}/copy-week", json={**base, "employee_ids": [w.a1.id, w.b1.id]})
    assert out.status_code == 400 and out.json()["error"]["details"]["rejected"][0]["employee_id"] == w.b1.id
    assert db.query(WorkShiftDay).filter(WorkShiftDay.work_date > this_monday).count() == 0
    #  Chép về một tuần đã qua: Trưởng phòng bị BỎ QUA hết ngày đích (không lỗi, không ghi); Nhân sự thì chép được.
    past_week = {**base, "target_week_start": (last - timedelta(days=7)).isoformat(), "employee_ids": [w.a1.id]}
    res = mgr.post(f"{URL}/copy-week", json=past_week)
    assert res.status_code == 200 and res.json()["data"]["skipped_past"] == 1 and res.json()["data"]["changed"] == 0
    assert "bỏ qua 1 ngày đã qua" in res.json()["message"]
    assert db.query(WorkShiftDay).filter(WorkShiftDay.work_date < last).count() == 0
    assert hr.post(f"{URL}/copy-week", json=past_week).json()["data"]["created"] == 1
    nothing = mgr.post(f"{URL}/copy-week", json={**base, "source_week_start": (last - timedelta(days=14)).isoformat(),
                                                 "employee_ids": [w.a1.id]})
    assert nothing.status_code == 200 and nothing.json()["data"]["changed"] == 0


def test_chep_tuan_truong_phong_bo_qua_ngay_da_qua_nhung_van_chan_ly_do_khac(db, w, client_as):
    hr, mgr = client_as(w.hr_user), client_as(w.mgr_user)
    this_monday = vn_today() - timedelta(days=vn_today().weekday())
    last = this_monday - timedelta(days=7)
    for offset in range(7):                                            # đủ 7 ngày có ca ở tuần nguồn
        _put(hr, w.a1, last + timedelta(days=offset), [(8, 12)])
    past_days = vn_today().weekday()                                    # số ngày của tuần này đã qua (T2 = 0)
    body = {"employee_ids": [w.a1.id], "source_week_start": last.isoformat(),
            "target_week_start": this_monday.isoformat()}
    res = mgr.post(f"{URL}/copy-week", json=body)
    assert res.status_code == 200
    assert res.json()["data"] == {"created": 7 - past_days, "updated": 0, "skipped": 0, "skipped_past": past_days,
                                  "skipped_leave": 0, "leave_conflicts": [], "changed": 7 - past_days}
    assert (" (bỏ qua" in res.json()["message"]) == (past_days > 0)
    assert db.query(WorkShiftDay).filter(WorkShiftDay.work_date >= this_monday).count() == 7 - past_days
    assert all(r.work_date >= vn_today() for r in db.query(WorkShiftDay).filter(WorkShiftDay.work_date >= this_monday))
    #  Nhân sự chép cả ngày đã qua (ghi đè): tuần đích đủ 7 ô.
    full = hr.post(f"{URL}/copy-week", json={**body, "overwrite": True}).json()["data"]
    assert full["skipped_past"] == 0 and full["created"] + full["updated"] == 7
    #  Lý do khác vẫn từ chối cả lượt, kể cả khi có ngày bị bỏ qua: người ngoài phạm vi + tự xếp cho mình.
    _put(hr, w.b1, last, [(8, 12)])
    out = mgr.post(f"{URL}/copy-week", json={**body, "employee_ids": [w.a1.id, w.b1.id, w.mgr.id],
                                             "target_week_start": (this_monday + timedelta(days=7)).isoformat()})
    assert out.status_code == 403
    assert {(r["employee_id"], r["code"]) for r in out.json()["error"]["details"]["rejected"]} == {
        (w.b1.id, "not_found"), (w.mgr.id, "self")}


def test_chep_tuan_phai_la_thu_hai_va_khac_tuan():
    with pytest.raises(ValidationError):
        ShiftCopyWeek(employee_ids=[1], source_week_start=date(2026, 1, 6), target_week_start=date(2026, 1, 12))
    with pytest.raises(ValidationError):
        ShiftCopyWeek(employee_ids=[1], source_week_start=MON, target_week_start=MON)
    assert ShiftCopyWeek(employee_ids=[1, 1], source_week_start=MON, target_week_start=MON + timedelta(days=7)
                         ).employee_ids == [1]


# ── Chuông ────────────────────────────────────────────────────────────────────

def _bells(db):
    return db.query(Notification).filter(Notification.title == "Ca làm việc của bạn vừa được cập nhật").all()


def test_mot_chuong_cho_moi_nhan_su_moi_luot_khong_bao_chinh_minh(db, w, client_as):
    hr = client_as(w.hr_user)
    mon = _future_monday()
    dates = [(mon + timedelta(days=i)).isoformat() for i in range(3)]
    res = hr.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id, w.a2.id], "dates": dates,
                                       "segments": _seg((8, 12))})
    assert res.status_code == 200
    bells = _bells(db)
    assert sorted(b.user_id for b in bells) == sorted([w.a1_user.id, w.a2_user.id])      # 3 ngày × 2 người = 2 chuông
    assert all(b.link == "/me" and b.created_by == w.hr_user.id and not b.is_read for b in bells)
    body = next(b.body for b in bells if b.user_id == w.a1_user.id)
    assert f"ngày {mon:%d/%m}–{mon + timedelta(days=2):%d/%m}" in body and "vừa được cập nhật" in body
    assert w.hr_user.id not in {b.user_id for b in bells}                          # không chuông cho người bấm


def test_chuong_mot_ngay_va_khi_go_ca_va_khong_chuong_khi_bi_tu_choi(db, w, client_as):
    mgr = client_as(w.mgr_user)
    day = _future_monday()
    _put(mgr, w.a1, day, [(8, 12)])
    assert f"ngày {day:%d/%m} vừa" in _bells(db)[0].body
    mgr.delete(f"{URL}/{w.a1.id}/{day.isoformat()}")
    assert len(_bells(db)) == 2                                                   # gỡ ca cũng báo
    mgr.delete(f"{URL}/{w.a1.id}/{day.isoformat()}")                              # gỡ lần hai: không đổi gì
    assert len(_bells(db)) == 2
    _put(mgr, w.b1, day, [(8, 12)])                                               # bị từ chối
    mgr.post(f"{URL}/bulk", json={"employee_ids": [w.a2.id, w.b1.id], "dates": [day.isoformat()],
                                  "segments": _seg((8, 12))})                     # bị từ chối cả lượt
    assert len(_bells(db)) == 2 and not [b for b in _bells(db) if b.user_id in (w.b1_user.id, w.a2_user.id)]


def test_mot_dong_nhat_ky_moi_luot_ghi(db, w, client_as):
    hr = client_as(w.hr_user)
    mon = _future_monday()
    hr.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id, w.a2.id], "dates": [mon.isoformat()],
                                 "segments": _seg((8, 12))})
    logs = db.query(AuditLog).filter(AuditLog.entity == "work_shift").all()
    assert len(logs) == 1 and logs[0].action == "update" and logs[0].created_by == w.hr_user.id
    assert "2 ô" in logs[0].message and "2 nhân sự" in logs[0].message
    hr.delete(f"{URL}/{w.a1.id}/{mon.isoformat()}")
    assert [log.action for log in db.query(AuditLog).filter(AuditLog.entity == "work_shift").order_by(AuditLog.id)
            ] == ["update", "delete"]
    hr.delete(f"{URL}/{w.a1.id}/{mon.isoformat()}")                               # không đổi gì → không nhật ký
    assert db.query(AuditLog).filter(AuditLog.entity == "work_shift").count() == 2


# ── Đọc ───────────────────────────────────────────────────────────────────────

def test_doc_theo_pham_vi_ho_so_va_luon_thay_chinh_minh(db, w, client_as):
    hr = client_as(w.hr_user)
    day = _future_monday()
    for emp in (w.a1, w.b1, w.mgr):
        _put(hr, emp, day, [(8, 12)])
    params = {"from_date": day.isoformat(), "to_date": day.isoformat()}
    seen = lambda who: sorted(i["employee_id"] for i in client_as(who).get(URL, params=params).json()["data"]["items"])  # noqa: E731
    assert seen(w.hr_user) == sorted([w.a1.id, w.b1.id, w.mgr.id])
    assert seen(w.mgr_user) == sorted([w.a1.id, w.mgr.id])                         # phòng A + chính mình, không có b1
    assert seen(w.a1_user) == [w.a1.id]                                            # chỉ xem hồ sơ của mình
    only_b = client_as(w.hr_user).get(URL, params={**params, "department_id": w.dept_b.id}).json()["data"]["items"]
    assert [i["employee_id"] for i in only_b] == [w.b1.id]
    one = client_as(w.hr_user).get(URL, params={**params, "employee_id": w.a1.id}).json()["data"]["items"]
    assert len(one) == 1 and one[0]["segments"][0]["label"] == "08:00–12:00"
    assert client_as(w.b1_user).get(URL, params=params).status_code == 403          # không có employee.read


def test_doc_gioi_han_khoang_ngay(w, client_as):
    hr = client_as(w.hr_user)
    #  01/01 → 12/02 là 43 ngày (quá trần); 42 ngày là 01/01 → 11/02.
    assert hr.get(URL, params={"from_date": "2026-01-01", "to_date": "2026-02-12"}).status_code == 422
    ok = hr.get(URL, params={"from_date": "2026-01-01", "to_date": "2026-02-11"})
    assert ok.status_code == 200
    assert hr.get(URL, params={"from_date": "2026-01-02", "to_date": "2026-01-01"}).status_code == 422


def test_ca_cua_toi_gop_mau_tuan_va_ca_xep(db, w, client_as):
    hr, me = client_as(w.hr_user), client_as(w.a1_user)
    mon = _future_monday()
    _put(hr, w.a1, mon, LIVESTREAM, "Livestream")
    _put(hr, w.a1, mon + timedelta(days=1), [])
    res = me.get(f"{URL}/me", params={"from_date": mon.isoformat(), "to_date": (mon + timedelta(days=6)).isoformat()})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["employee_id"] == w.a1.id and len(data["days"]) == 7
    d0, d1, d2, d6 = data["days"][0], data["days"][1], data["days"][2], data["days"][6]
    assert d0["is_shift"] and d0["segments"] == ["08:00–10:00", "14:00–16:00", "20:00–23:00"]
    assert d0["hours"] == 7.0 and d0["note"] == "Livestream" and d0["ranges"] == [[8, 10], [14, 16], [20, 23]]
    assert d1["is_shift"] and d1["is_day_off"] and d1["segments"] == []
    assert not d2["is_shift"] and d2["segments"] == ["08:00–12:00", "13:00–17:00"] and d2["hours"] == 8.0
    assert d2["start_time"] == "08:00" and d2["end_time"] == "17:00" and d2["ranges"] == []
    assert d6["is_day_off"] and not d6["is_shift"]                                   # Chủ nhật theo mẫu mặc định
    assert d0["schedule_name"] == "Xếp ca theo ngày" and d2["schedule_name"] != "Xếp ca theo ngày"
    assert me.get(f"{URL}/me", params={"from_date": mon.isoformat(),
                                       "to_date": (mon + timedelta(days=60)).isoformat()}).status_code == 422


def test_ca_cua_toi_tai_khoan_chua_gan_ho_so(db, w, client_as):
    orphan = User(email="orphan758@dego.vn", employee_id=0, password_hash="x", is_active=True)
    db.add(orphan)
    db.commit()
    res = client_as(orphan).get(f"{URL}/me", params={"from_date": "2026-01-05", "to_date": "2026-01-06"})
    assert res.status_code == 200 and res.json()["data"]["employee_id"] == 0 and res.json()["data"]["days"] == []


def test_nghi_phep_tinh_theo_ca_sau_khi_xep_qua_api(db, w, client_as):
    day = _future_monday()
    assert _put(client_as(w.mgr_user), w.a1, day, LIVESTREAM).status_code == 200
    assert _days(db, w.a1, day, day) == 1.0
    assert _hours(db, w.a1, day, day, time(14), time(16)) == pytest.approx(round(2 / 7, 2))
    client_as(w.mgr_user).delete(f"{URL}/{w.a1.id}/{day.isoformat()}")
    assert _hours(db, w.a1, day, day, time(14), time(16)) == pytest.approx(round(2 / 8, 2))   # về mẫu: ngày 8 giờ


# ══════════════════════════════════════════════════════════════════════════════
# 6. Trần đầu vào ở tầng schema (SQLite không ép VARCHAR)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("segments", [
    _seg(*[(i, i + 1) for i in range(13)]),                     # 13 khung
    [{"start_hour": 8, "end_hour": 8}],                          # start == end
    [{"start_hour": 10, "end_hour": 8}],                         # ngược
    [{"start_hour": 24, "end_hour": 24}],                        # start ngoài 0..23
    [{"start_hour": -1, "end_hour": 5}],
    [{"start_hour": 0, "end_hour": 25}],                         # end ngoài 1..24
    [{"start_hour": 0, "end_hour": 0}],
    _seg((8, 11), (10, 12)),                                     # chồng nhau
    _seg((8, 12), (9, 10)),                                      # lồng nhau
])
def test_schema_chan_khung_sai(segments):
    with pytest.raises(ValidationError):
        ShiftPut(segments=segments)


def test_schema_nhan_khung_hop_le_va_sap_theo_gio():
    body = ShiftPut(segments=_seg((14, 16), (0, 8), (16, 24)), note="  ghi chú  ")
    assert body.pairs() == [(0, 8), (14, 16), (16, 24)] and body.note == "ghi chú"
    assert ShiftPut(segments=[]).pairs() == []
    assert len(ShiftPut(segments=_seg(*[(i * 2, i * 2 + 1) for i in range(12)])).segments) == 12


def test_schema_ghi_chu_toi_da_255():
    assert len(ShiftPut(segments=[], note="x" * 255).note) == 255
    with pytest.raises(ValidationError):
        ShiftPut(segments=[], note="x" * 256)
    with pytest.raises(ValidationError):
        ShiftBulk(employee_ids=[1], dates=[MON], segments=[], note="x" * 256)


def test_schema_hang_loat_tran_nguoi_ngay_o():
    ok = ShiftBulk(employee_ids=[2, 1, 2], dates=[TUE, MON, MON], segments=_seg((8, 12)))
    assert ok.employee_ids == [2, 1] and ok.dates == [MON, TUE]                   # bỏ trùng, ngày sắp tăng
    day = lambda i: MON + timedelta(days=i)  # noqa: E731
    with pytest.raises(ValidationError):
        ShiftBulk(employee_ids=[], dates=[MON])
    with pytest.raises(ValidationError):
        ShiftBulk(employee_ids=[1], dates=[])
    with pytest.raises(ValidationError):
        ShiftBulk(employee_ids=list(range(1, 52)), dates=[MON])                  # 51 người
    with pytest.raises(ValidationError):
        ShiftBulk(employee_ids=[1], dates=[day(i) for i in range(43)])           # 43 ngày
    with pytest.raises(ValidationError):
        ShiftBulk(employee_ids=list(range(1, 51)), dates=[day(i) for i in range(11)])   # 550 ô
    assert len(ShiftBulk(employee_ids=list(range(1, 51)), dates=[day(i) for i in range(10)]).dates) == 10
    with pytest.raises(ValidationError):
        ShiftBulk(employee_ids=[0], dates=[MON])
    with pytest.raises(ValidationError):
        ShiftBulk(employee_ids=[1], dates=[date(1999, 12, 31)])                  # ngoài dải năm


# ══════════════════════════════════════════════════════════════════════════════
# 7. Các nơi đếm ngày nghỉ khác dùng chung `leave_credit` (báo cáo có mặt, tách ngày báo cáo nghỉ phép, hồ sơ làm việc)
# ══════════════════════════════════════════════════════════════════════════════

def test_bao_cao_co_mat_tinh_nghi_theo_ngay_xep_ca():
    from app.modules.work_schedule.attendance_report_data import _on_leave
    pm_only, live = shift_spec([(13, 17)]), shift_spec(LIVESTREAM)
    assert _on_leave([(1, 3, None)], pm_only)[0] == 1.0                    # nghỉ cả ngày trừ 1 công
    assert _on_leave([(1, 1, None)], pm_only)[0] == 0.0                    # nghỉ sáng mà ca chiều
    assert _on_leave([(1, 2, None)], pm_only)[0] == 1.0                    # nửa chiều chứa toàn bộ giờ ca
    assert _on_leave([(1, 2, None)], shift_spec([(10, 14)]))[0] == 0.5     # ca ở cả hai nửa
    assert _on_leave([(1, 0, (time(14), time(16), time(14), time(16)))], live)[0] == pytest.approx(2 / 7)
    assert _on_leave([(1, 3, None), (2, 0, (time(14), time(16), time(14), time(16)))], live)[0] == 1.0   # không vượt công tối đa
    assert _on_leave([(1, 3, None)], shift_spec([]))[0] == 0.0


def test_tach_ngay_bao_cao_nghi_phep_dung_trong_so_ngay_xep_ca():
    from app.modules.leave.report_day_split import _day_weights
    period = SimpleNamespace(from_date=MON, to_date=WED, from_session=SESSION_FULL, to_session=SESSION_FULL)
    specs = {MON: shift_spec([(13, 17)]), TUE: shift_spec([]), WED: shift_spec(LIVESTREAM)}
    weights = _day_weights(period, lambda d: specs[d], set())
    assert weights == {MON: 0.5, TUE: 0.0, WED: 0.5}                      # ngày nghỉ do xếp ca không gánh phép


def test_ho_so_lam_viec_lich_ngay_xep_ca():
    from app.modules.usage_profile.daily_workday import build_calendar

    class Plans:
        def at(self, employee_id, day):
            return shift_spec([(13, 17)]), 0

    leave = SimpleNamespace(from_date=MON, to_date=MON, from_session=SESSION_FULL, to_session=SESSION_FULL,
                            from_time=None, to_time=None)
    cal = build_calendar(Plans(), {}, {7: [leave]}, 7, 1, MON)
    assert cal.is_workday and cal.work_capacity == 1.0 and cal.leave_days == 1.0


# ══════════════════════════════════════════════════════════════════════════════
# 8. Rà mã lượt 2: ghi đồng thời, giờ nghỉ nhiều ngày, id trần, tên lịch
# ══════════════════════════════════════════════════════════════════════════════

def test_hai_luot_cung_tao_mot_o_thua_cuoc_nhan_409(db, w, client_as, monkeypatch):
    """Mô phỏng đọc cũ: lượt thứ hai không thấy hàng lượt thứ nhất vừa tạo → INSERT chạm UNIQUE → 409, không phải 500."""
    hr = client_as(w.hr_user)
    day = _future_monday()
    assert _put(hr, w.a1, day, [(8, 12)]).status_code == 200
    from app.modules.work_schedule import shift_service
    monkeypatch.setattr(shift_service, "_existing_days", lambda *a, **kw: {})     # "đọc cũ": không thấy hàng đã có
    res = _put(hr, w.a1, day, [(14, 16)])
    assert res.status_code == 409 and res.json()["error"]["message"] == "Ô này vừa được người khác xếp ca, tải lại rồi thử lại"
    monkeypatch.undo()
    assert _segments_of(db, w.a1, day) == [(8, 12)] and len(_rows(db, w.a1)) == 1   # lượt thua đã hoàn tác sạch
    bulk = hr.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id], "dates": [day.isoformat()], "segments": []})
    assert bulk.status_code == 200                                                  # phiên vẫn dùng được sau lỗi


def test_sua_ca_luon_dat_lai_updated_at_de_giu_khoa_hang(db, w, client_as):
    hr = client_as(w.hr_user)
    day = _future_monday()
    _put(hr, w.a1, day, [(8, 12)], "a")
    row = db.query(WorkShiftDay).filter_by(employee_id=w.a1.id, work_date=day).one()
    old_stamp = row.updated_at - timedelta(days=3)
    db.query(WorkShiftDay).filter_by(id=row.id).update({"updated_at": old_stamp, "created_at": old_stamp})
    db.commit()
    _put(hr, w.a1, day, [(8, 12)], "a")                                             # y hệt: vẫn phải UPDATE
    db.expire_all()
    assert db.query(WorkShiftDay).filter_by(id=row.id).one().updated_at > old_stamp + timedelta(days=2)


def test_id_nhan_su_qua_lon_bi_chan_422(w, client_as):
    hr = client_as(w.hr_user)
    big = 2 ** 53 + 1
    assert hr.put(f"{URL}/{big}/2026-12-01", json={"segments": []}).status_code == 422
    assert hr.delete(f"{URL}/{big}/2026-12-01").status_code == 422
    params = {"from_date": "2026-12-01", "to_date": "2026-12-02"}
    assert hr.get(URL, params={**params, "department_id": big}).status_code == 422
    assert hr.get(URL, params={**params, "employee_id": big}).status_code == 422


def test_don_nghi_theo_gio_nhieu_ngay_bao_cao_co_mat_dung_cua_tung_ngay(db, cap_quyen):
    """Ca 20–24 ngày D, nghỉ THEO GIỜ từ 20:00 D tới 00:00 D+1: đúng 1 công như quỹ phép, và ngày D+1 không bị tính nghỉ."""
    from app.modules.leave.constants import SESSION_HOURLY
    from app.modules.work_schedule.attendance_report_data import load_day_rows
    company, dept, emp = make_world(db, "AT1")
    emp.hire_date = date(2020, 1, 1)                                   # báo cáo bỏ qua ngày trước ngày vào làm
    put_shift(db, emp, MON, [(20, 24)])
    db.add(LeaveRequest(code="NP-758-AT", company_id=company.id, department_id=dept.id, employee_id=emp.id,
                        leave_type_id=0, from_date=MON, to_date=TUE, from_session=SESSION_HOURLY,
                        to_session=SESSION_HOURLY, from_time=time(20, 0), to_time=time(0, 0), status=LR_APPROVED))
    db.commit()
    assert _hours(db, emp, MON, TUE, time(20, 0), time(0, 0)) == 1.0                       # quỹ phép
    rows = {r.day: r for r in load_day_rows(db, db.query(Employee), db.query(LeaveRequest), MON, TUE)}
    assert rows[MON].on_leave == 1.0 and rows[MON].present == 0.0
    assert rows[TUE].on_leave == 0.0 and rows[TUE].present == 1.0                          # ngày mẫu: không dính cặp giờ cũ
    assert rows[MON].leaves[0][1] == "Theo giờ 20:00–00:00"                                  # nhãn vẫn là giờ của đơn


def test_ten_lich_cua_ngay_xep_ca(db, emp):
    assert "Mặc định" in resolver.schedule_name_on(db, emp, MON)
    put_shift(db, emp, MON, [(8, 12)])
    db.commit()
    assert resolver.schedule_name_on(db, emp, MON) == "Xếp ca theo ngày"
    assert resolver.schedule_name_on(db, emp, TUE) != "Xếp ca theo ngày"
    assert workday_service.schedule_name_on(db, emp, MON) == "Xếp ca theo ngày"        # form nghỉ phép đọc đường này


def test_build_my_days_la_ban_mot_nguoi_cua_build_days_many(db, emp):
    from app.modules.work_schedule.shift_view import build_days_many, build_my_days
    put_shift(db, emp, MON, LIVESTREAM, "x")
    db.commit()
    assert build_my_days(db, emp, MON, SUN) == build_days_many(db, [emp], MON, SUN)[emp.id]
    assert build_my_days(db, None, MON, SUN) == []


# ══════════════════════════════════════════════════════════════════════════════
# 9. Không ai tự xếp ca cho mình (trừ quản trị hệ thống)
# ══════════════════════════════════════════════════════════════════════════════

def test_nhan_su_khong_tu_xep_ca_cho_chinh_minh_o_moi_duong(db, w, client_as):
    hr = client_as(w.hr_user)
    day = _future_monday()
    own = f"{URL}/{w.hr.id}/{day.isoformat()}"
    for res in (hr.put(own, json={"segments": _seg((8, 12))}), hr.delete(own)):
        assert res.status_code == 403 and "tự xếp ca" in res.json()["error"]["message"]
    bulk = hr.post(f"{URL}/bulk", json={"employee_ids": [w.hr.id], "dates": [day.isoformat()], "segments": []})
    assert bulk.status_code == 403
    copy = hr.post(f"{URL}/copy-week", json={"employee_ids": [w.hr.id], "source_week_start": day.isoformat(),
                                            "target_week_start": (day + timedelta(days=7)).isoformat()})
    assert copy.status_code == 403 and _rows(db) == []


def test_quan_tri_he_thong_duoc_tu_xep_ca_va_khong_tu_nhan_chuong(db, w, client_as, cap_quyen):
    from app.modules.role.model import Role
    from app.modules.user.model import UserRole
    role = Role(code="admin", name="Quản trị hệ thống")
    db.add(role)
    db.flush()
    db.add(UserRole(user_id=w.hr_user.id, role_id=role.id))
    db.commit()
    hr = client_as(w.hr_user)
    day = _future_monday()
    res = hr.post(f"{URL}/bulk", json={"employee_ids": [w.hr.id, w.a1.id], "dates": [day.isoformat()],
                                       "segments": _seg((8, 12))})
    assert res.status_code == 200 and res.json()["data"]["created"] == 2
    assert [b.user_id for b in _bells(db)] == [w.a1_user.id]                       # không chuông cho chính người bấm


# ══════════════════════════════════════════════════════════════════════════════
# 10. Ngày đã có đơn nghỉ chờ duyệt / đã duyệt thì không đổi ca
# ══════════════════════════════════════════════════════════════════════════════

def _leave_req(db, emp, a, b, status=LR_APPROVED, code="NP758", periods=None, **kw):
    from app.modules.leave.request_model import LeaveRequestPeriod
    req = LeaveRequest(code=code, company_id=emp.company_id, department_id=emp.department_id, employee_id=emp.id,
                       leave_type_id=0, from_date=a, to_date=b, from_session=SESSION_FULL, to_session=SESSION_FULL,
                       status=status, **kw)
    db.add(req)
    db.flush()
    for order, (pa, pb) in enumerate(periods or []):
        db.add(LeaveRequestPeriod(request_id=req.id, from_date=pa, to_date=pb, from_session=SESSION_FULL,
                                  to_session=SESSION_FULL, days=1, sort_order=order))
    db.commit()
    return req


def test_dat_va_go_ca_ngay_co_don_nghi_bi_409_kem_ma_don(db, w, client_as):
    hr, mgr = client_as(w.hr_user), client_as(w.mgr_user)
    day = _future_monday()
    _put(hr, w.a1, day, [(8, 12)])
    _leave_req(db, w.a1, day, day, LR_APPROVED, "NP758A")
    for who in (hr, mgr):                                             # cả Nhân sự lẫn Trưởng phòng
        res = _put(who, w.a1, day, [(14, 16)])
        assert res.status_code == 409
        assert res.json()["error"]["message"] == (
            f"Ngày {day:%d/%m} đã có đơn nghỉ NP758A (đã duyệt) — sửa / hủy đơn trước rồi xếp ca.")
        assert who.delete(f"{URL}/{w.a1.id}/{day.isoformat()}").status_code == 409
    assert _segments_of(db, w.a1, day) == [(8, 12)]                     # chưa đổi gì
    pending_day = day + timedelta(days=1)
    _leave_req(db, w.a2, pending_day, pending_day, LR_PENDING, "NP758P")
    res = _put(mgr, w.a2, pending_day, [(14, 16)])
    assert res.status_code == 409 and "NP758P (chờ duyệt)" in res.json()["error"]["message"]


def test_don_nhap_tu_choi_huy_khong_giu_ngay_va_xoa_ca_khong_co_khong_loi(db, w, client_as):
    from app.modules.leave.constants import LR_CANCELLED, LR_DRAFT, LR_REJECTED
    mgr = client_as(w.mgr_user)
    day = _future_monday()
    for i, status in enumerate((LR_DRAFT, LR_REJECTED, LR_CANCELLED)):
        _leave_req(db, w.a1, day, day, status, f"NP758X{i}")
    assert _put(mgr, w.a1, day, [(8, 12)]).status_code == 200
    other = day + timedelta(days=1)
    _leave_req(db, w.a2, other, other, LR_APPROVED, "NP758D")
    gone = mgr.delete(f"{URL}/{w.a2.id}/{other.isoformat()}")                # ngày có đơn nhưng KHÔNG có ca riêng: không đổi gì
    assert gone.status_code == 200 and gone.json()["data"] == {"deleted": False}


def test_don_nhieu_khoang_chi_giu_ngay_cua_tung_khoang(db, w, client_as):
    mgr = client_as(w.mgr_user)
    mon = _future_monday()
    #  Đầu đơn bao 3 ngày nhưng chỉ nghỉ hai khoảng (T2 và T4): thứ Ba là khe, vẫn xếp ca được.
    _leave_req(db, w.a1, mon, mon + timedelta(days=2), LR_APPROVED, "NP758M",
               periods=[(mon, mon), (mon + timedelta(days=2), mon + timedelta(days=2))])
    assert _put(mgr, w.a1, mon, [(8, 12)]).status_code == 409
    assert _put(mgr, w.a1, mon + timedelta(days=1), [(8, 12)]).status_code == 200
    assert _put(mgr, w.a1, mon + timedelta(days=2), [(8, 12)]).status_code == 409


def test_don_nghi_theo_gio_cung_giu_ngay(db, w, client_as):
    from app.modules.leave.constants import SESSION_HOURLY
    hr = client_as(w.hr_user)
    day = _future_monday()
    req = _leave_req(db, w.a1, day, day, LR_APPROVED, "NP758H")
    db.query(LeaveRequest).filter_by(id=req.id).update({"from_session": SESSION_HOURLY, "from_time": time(9),
                                                          "to_time": time(10)})
    db.commit()
    assert _put(hr, w.a1, day, [(8, 12)]).status_code == 409


def test_hang_loat_gap_don_nghi_khong_ghi_o_nao_va_liet_ke_ma_don(db, w, client_as):
    mgr = client_as(w.mgr_user)
    mon = _future_monday()
    dates = [(mon + timedelta(days=i)).isoformat() for i in range(3)]
    _leave_req(db, w.a2, mon + timedelta(days=1), mon + timedelta(days=1), LR_APPROVED, "NP758B")
    res = mgr.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id, w.a2.id], "dates": dates, "segments": _seg((8, 12))})
    assert res.status_code == 409 and res.json()["error"]["code"] == "shift_rejected"
    rejected = res.json()["error"]["details"]["rejected"]
    assert [(r["employee_id"], r["work_date"], r["code"], r["request_code"]) for r in rejected] == [
        (w.a2.id, dates[1], "leave_conflict", "NP758B")]
    assert "NP758B" in rejected[0]["message"] and _rows(db) == []
    #  Ngoài phạm vi thì chỉ báo ngoài phạm vi, không lộ đơn nghỉ của người đó.
    _leave_req(db, w.b1, mon, mon, LR_APPROVED, "NP758C")
    out = mgr.post(f"{URL}/bulk", json={"employee_ids": [w.b1.id], "dates": [dates[0]], "segments": []})
    assert out.status_code == 400 and [r["code"] for r in out.json()["error"]["details"]["rejected"]] == ["not_found"]


def test_chep_tuan_bo_qua_ngay_co_don_nghi_va_bao_cao_danh_sach(db, w, client_as):
    hr = client_as(w.hr_user)
    src, dst = _future_monday(), _future_monday() + timedelta(days=7)
    for offset in (0, 1, 2):
        _put(hr, w.a1, src + timedelta(days=offset), [(8, 12)])
    _put(hr, w.a2, src, [(9, 12)])
    _leave_req(db, w.a1, dst + timedelta(days=1), dst + timedelta(days=1), LR_PENDING, "NP758W")
    res = hr.post(f"{URL}/copy-week", json={"employee_ids": [w.a1.id, w.a2.id], "source_week_start": src.isoformat(),
                                           "target_week_start": dst.isoformat()})
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["created"] == 3 and data["skipped_leave"] == 1 and data["changed"] == 3
    assert data["leave_conflicts"] == [{"employee_id": w.a1.id, "work_date": (dst + timedelta(days=1)).isoformat(),
                                        "request_code": "NP758W"}]
    assert "bỏ qua 1 ngày đã có đơn nghỉ" in res.json()["message"]
    assert db.query(WorkShiftDay).filter_by(employee_id=w.a1.id, work_date=dst + timedelta(days=1)).count() == 0


def test_chot_don_nghi_so_truy_van_co_dinh(db, w):
    from app.modules.work_schedule.shift_leave_conflicts import find_leave_conflicts
    mon = _future_monday()
    for i, emp in enumerate((w.a1, w.a2, w.b1, w.mgr)):
        _leave_req(db, emp, mon, mon + timedelta(days=i), LR_APPROVED, f"NP758Q{i}")
    small = [(w.a1.id, mon)]
    big = [(e.id, mon + timedelta(days=d)) for e in (w.a1, w.a2, w.b1, w.mgr) for d in range(10)]
    profile = get_perm_profile(db, w.hr_user)
    found_small, q_small = count_queries(db, lambda: find_leave_conflicts(db, small, w.hr_user, profile))
    found_big, q_big = count_queries(db, lambda: find_leave_conflicts(db, big, w.hr_user, profile))
    assert len(found_small) == 1 and len(found_big) == 1 + 2 + 3 + 4            # số ngày bị giữ của bốn đơn
    assert len(q_big) == len(q_small)


# ══════════════════════════════════════════════════════════════════════════════
# 11. Nghỉ bù: ngày nghỉ chỉ vì ca xếp nghỉ lùi ngày không dùng để xin
# ══════════════════════════════════════════════════════════════════════════════

def _working_day_ago(n=10):
    day = vn_today() - timedelta(days=n)
    return day - timedelta(days=1) if day.weekday() == 6 else day              # tránh Chủ nhật (mẫu mặc định đã nghỉ)


def _stamp(db, emp, day, when):
    db.query(WorkShiftDay).filter_by(employee_id=emp.id, work_date=day).update({"created_at": when, "updated_at": when})
    db.commit()


def test_nghi_bu_ngay_xep_nghi_sau_khi_da_qua_khong_hop_le(db, emp):
    from fastapi import HTTPException
    from app.modules.leave import comp_request_service as comp
    day = _working_day_ago()
    put_shift(db, emp, day, [])                                                # xếp nghỉ NGAY BÂY GIỜ cho ngày đã qua
    db.commit()
    with pytest.raises(HTTPException) as exc:
        comp.check_work_date(db, emp, day)
    assert exc.value.status_code == 422 and exc.value.detail == "Ngày này được xếp nghỉ sau khi đã qua, không dùng để xin nghỉ bù"
    _stamp(db, emp, day, datetime.combine(day, time(12)) - timedelta(days=2))     # ca được xếp từ TRƯỚC ngày đó
    comp.check_work_date(db, emp, day)                                        # hợp lệ: nghỉ do xếp ca có kế hoạch
    _stamp(db, emp, day, datetime.combine(day, time(3)))                          # 10:00 VN cùng ngày → vẫn là "đã qua / cùng ngày"
    with pytest.raises(HTTPException):
        comp.check_work_date(db, emp, day)


def test_nghi_bu_ngay_le_va_mau_nghi_khong_doi(db, emp):
    from fastapi import HTTPException
    from app.modules.leave import comp_request_service as comp
    day = _working_day_ago(20)
    db.add(Holiday(company_id=0, date=day, name="Lễ", is_recurring=False, is_active=True))
    put_shift(db, emp, day, [])                                                # ca nghỉ xếp hôm nay NHƯNG ngày là lễ
    db.commit()
    comp.check_work_date(db, emp, day)                                        # ngày lễ vẫn dùng được như cũ
    sunday = vn_today() - timedelta(days=(vn_today().weekday() + 1) % 7 + 7)  # một Chủ nhật đã qua (mẫu nghỉ)
    comp.check_work_date(db, emp, sunday)
    other = _working_day_ago(30)
    put_shift(db, emp, other, [(8, 12)])                                       # ca CÓ khung → ngày làm việc, vẫn bị chặn như cũ
    db.commit()
    with pytest.raises(HTTPException) as exc:
        comp.check_work_date(db, emp, other)
    assert "ngày làm việc bình thường" in exc.value.detail


def test_ma_don_nghi_chi_lo_cho_nguoi_xem_duoc_don(db, w, client_as, cap_quyen):
    """Người xếp ca KHÔNG có `leave_request.read` phủ đơn đó chỉ biết ngày đã có đơn, không thấy mã / trạng thái."""
    day = _future_monday()
    hidden_msg = f"Ngày {day:%d/%m} đã có đơn nghỉ của nhân viên này — liên hệ Nhân sự để sửa đơn trước."
    blind = User(email="tp758b@dego.vn", employee_id=w.mgr.id, password_hash="x", is_active=True)   # cùng phòng A
    db.add(blind)
    db.flush()
    cap_quyen(blind.id, "work_schedule_personal", scope="dept", read=True, create=True, write=True, delete=True)
    cap_quyen(blind.id, "employee", scope="dept", read=True)
    cap_quyen(blind.id, "leave_request", scope="own", read=True)                  # chỉ thấy đơn của chính mình
    _put(client_as(w.hr_user), w.a1, day, [(8, 12)])
    _leave_req(db, w.a1, day, day, LR_APPROVED, "NP758S")
    #  Một lượt: người xem được đơn (Trưởng phòng có leave_request bậc phòng) vs người không xem được.
    seen = _put(client_as(w.mgr_user), w.a1, day, [(14, 16)])
    assert seen.status_code == 409 and "NP758S (đã duyệt)" in seen.json()["error"]["message"]
    blind_client = client_as(blind)
    res = _put(blind_client, w.a1, day, [(14, 16)])
    assert res.status_code == 409 and res.json()["error"]["message"] == hidden_msg
    assert blind_client.delete(f"{URL}/{w.a1.id}/{day.isoformat()}").json()["error"]["message"] == hidden_msg
    #  Hàng loạt: mục bị từ chối có `request_code` rỗng, và thông điệp ẩn.
    bulk = blind_client.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id], "dates": [day.isoformat()],
                                                  "segments": _seg((8, 9))})
    item = bulk.json()["error"]["details"]["rejected"][0]
    assert bulk.status_code == 409 and item["code"] == "leave_conflict"
    assert item["request_code"] == "" and item["message"] == hidden_msg and "NP758S" not in bulk.text
    assert _segments_of(db, w.a1, day) == [(8, 12)]
    #  Chép tuần: ô bị bỏ qua vẫn được liệt kê, mã đơn rỗng với người không xem được và đầy đủ với người xem được.
    src, dst = day - timedelta(days=7), day
    _put(client_as(w.hr_user), w.a2, src, [(9, 12)])
    other = _leave_req(db, w.a2, dst, dst, LR_PENDING, "NP758T")
    body = {"employee_ids": [w.a2.id], "source_week_start": src.isoformat(), "target_week_start": dst.isoformat()}
    blind_copy = blind_client.post(f"{URL}/copy-week", json=body).json()["data"]
    assert blind_copy["skipped_leave"] == 1 and blind_copy["leave_conflicts"][0]["request_code"] == ""
    assert other.code not in str(blind_copy)
    seen_copy = client_as(w.hr_user).post(f"{URL}/copy-week", json=body).json()["data"]
    assert seen_copy["leave_conflicts"][0]["request_code"] == "NP758T"


def _lock_error(code):
    from sqlalchemy.exc import OperationalError
    return OperationalError("INSERT", {}, Exception(code, "mô phỏng MySQL"))


@pytest.mark.parametrize("code", [1213, 1205])
def test_deadlock_va_het_cho_khoa_cung_la_409(db, w, client_as, monkeypatch, code):
    from app.modules.work_schedule import shift_service
    hr = client_as(w.hr_user)
    day = _future_monday()

    def boom(*args, **kwargs):
        raise _lock_error(code)

    monkeypatch.setattr(shift_service, "upsert_items", boom)
    res = _put(hr, w.a1, day, [(8, 12)])
    assert res.status_code == 409 and res.json()["error"]["message"] == "Ô này vừa được người khác xếp ca, tải lại rồi thử lại"
    bulk = hr.post(f"{URL}/bulk", json={"employee_ids": [w.a1.id], "dates": [day.isoformat()], "segments": []})
    assert bulk.status_code == 409
    monkeypatch.undo()
    assert _put(hr, w.a1, day, [(8, 12)]).status_code == 200                    # phiên dùng lại được sau lỗi


def test_loi_co_so_du_lieu_khac_van_la_loi_he_thong(db, w, client_as, monkeypatch):
    from app.modules.work_schedule import shift_service
    hr = client_as(w.hr_user)

    def boom(*args, **kwargs):
        raise _lock_error(2006)                                                  # mất kết nối: không được giấu thành 409

    monkeypatch.setattr(shift_service, "upsert_items", boom)
    with pytest.raises(Exception) as exc:
        _put(hr, w.a1, _future_monday(), [(8, 12)])
    assert "OperationalError" in type(exc.value).__name__


def test_khoa_chi_cho_hang_da_co_theo_khoa_chinh(db, w):
    """Ô chưa có hàng không bị `FOR UPDATE` theo khoảng (gap lock → deadlock); hàng đã có được khóa theo `id`.
    (SQLite không phát `FOR UPDATE`; bản chạy thật trên MySQL kiểm bằng kịch bản hai luồng, xem báo cáo CR-761.)"""
    from app.modules.work_schedule import shift_service
    day = _future_monday()
    put_shift(db, w.a1, day, [(8, 12)])
    ids = (w.a1.id, w.a2.id)                  # lấy trước commit: thuộc tính hết hạn tự nạp lại sẽ lẫn vào số truy vấn
    db.commit()
    _, sql = count_queries(db, lambda: shift_service._existing_days(db, list(ids), [day]))
    assert len(sql) == 2                      # đọc theo khoảng (không khóa) + nạp lại theo `id` (FOR UPDATE trên MySQL)
    assert "tab_work_shift_day.id IN" in sql[1]
    _, none_sql = count_queries(db, lambda: shift_service._existing_days(db, [ids[1]], [day]))
    assert len(none_sql) == 1                                                    # không có hàng nào → không cần truy vấn khóa


# ══════════════════════════════════════════════════════════════════════════════
# 12. Lưới Xem lịch: cờ `leave_hold` (ô không xếp ca được vì đã có đơn nghỉ)
# ══════════════════════════════════════════════════════════════════════════════

def test_roster_leave_hold_gom_ngay_le_ngay_nghi_va_khong_giu_ngay_khe(db, cap_quyen):
    user = _admin(db, cap_quyen, "rs758h")
    company, dept, emp = make_world(db, "RH1")
    db.add(Holiday(company_id=0, date=TUE, name="Lễ", is_recurring=False, is_active=True))
    db.commit()
    #  Đơn đã duyệt 3 khoảng: T2, T3 (ngày lễ), CN (ngày nghỉ theo mẫu) — T4 là khe; đơn nháp ở T5 không giữ ngày.
    from app.modules.leave.constants import LR_DRAFT
    req = _leave_req(db, emp, MON, SUN, LR_APPROVED, "NP758R", periods=[(MON, TUE), (SUN, SUN)])
    _leave_req(db, emp, MON + timedelta(days=3), MON + timedelta(days=3), LR_DRAFT, "NP758Z")
    cells = _roster(db, user)["items"][0]["cells"]
    hold = [c["leave_hold"] for c in cells]
    assert hold == [True, True, False, False, False, False, True]
    assert cells[1]["is_holiday"] and cells[1]["leave"] is None              # ngày lễ: không tô nghỉ nhưng vẫn giữ ngày
    assert cells[6]["leave"] is None and cells[6]["leave_hold"]               # ngày nghỉ theo mẫu: cũng giữ
    assert cells[0]["leave"] is not None and cells[0]["leave_hold"] is True   # cờ chỉ là bool (mã đơn vẫn chỉ ở `leave`)
    assert req.id


def test_roster_leave_hold_khong_phu_thuoc_pham_vi_don_nghi_cua_nguoi_xem(db, cap_quyen):
    company, dept, emp = make_world(db, "RH2")
    viewer = User(email="blind758@dego.vn", employee_id=0, is_active=True)
    db.add(viewer)
    db.commit()
    cap_quyen(viewer.id, "employee", scope="all", read=True)               # thấy người, KHÔNG có leave_request.read
    cap_quyen(viewer.id, "work_schedule", scope="all", read=True, write=True)   # Nhân sự: thấy mọi người trong phạm vi employee (duoc-CR-761)
    _leave_req(db, emp, MON, MON, LR_APPROVED, "NP758V")
    cell = _roster(db, viewer)["items"][0]["cells"][0]
    assert cell["leave"] is None and cell["leave_hold"] is True             # không thấy đơn nhưng ô vẫn báo "đã giữ ngày"


def test_roster_leave_hold_nua_ngay_va_theo_gio_van_giu_ca_ngay(db, cap_quyen):
    from app.modules.leave.constants import SESSION_HOURLY
    user = _admin(db, cap_quyen, "rs758i")
    company, dept, emp = make_world(db, "RH3")
    db.commit()
    half = _leave_req(db, emp, MON, MON, LR_PENDING, "NP758N")
    db.query(LeaveRequest).filter_by(id=half.id).update({"from_session": SESSION_AFTERNOON})
    hourly = _leave_req(db, emp, TUE, TUE, LR_APPROVED, "NP758O")
    db.query(LeaveRequest).filter_by(id=hourly.id).update({"from_session": SESSION_HOURLY, "from_time": time(9),
                                                             "to_time": time(10)})
    db.commit()
    hold = [c["leave_hold"] for c in _roster(db, user)["items"][0]["cells"]]
    assert hold[:3] == [True, True, False]


# ══════════════════════════════════════════════════════════════════════════════
# 13. Ai thấy ai trên Lịch làm việc (`roster_visibility`): Nhân sự / Trưởng phòng / còn lại chỉ mình
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def seen(db, w, cap_quyen):
    """Dựng thêm: `head` (Trưởng phòng A, đọc hồ sơ MỌI người nhưng khóa lịch riêng chỉ bậc phòng), `staff` (nhân viên
    phòng A, đọc hồ sơ mọi người, không khóa lịch nào), `orphan` (tài khoản chưa gắn hồ sơ). Mỗi người có một ca thứ Hai."""
    head = User(email="head758@dego.vn", employee_id=w.mgr.id, password_hash="x", is_active=True)
    staff = User(email="staff758@dego.vn", employee_id=w.a2.id, password_hash="x", is_active=True)
    orphan = User(email="orphan758b@dego.vn", employee_id=0, password_hash="x", is_active=True)
    db.add_all([head, staff, orphan])
    db.flush()
    cap_quyen(head.id, "employee", scope="all", read=True)
    cap_quyen(head.id, "work_schedule_personal", scope="dept", read=True)
    cap_quyen(staff.id, "employee", scope="all", read=True)
    cap_quyen(orphan.id, "employee", scope="all", read=True)
    for emp in (w.mgr, w.a1, w.a2, w.b1, w.hr):
        put_shift(db, emp, MON, [(8, 12)])
    db.commit()
    return SimpleNamespace(head=head, staff=staff, orphan=orphan)


def _roster_codes(db, user, **kw):
    out = _roster(db, user, **kw)
    return sorted(i["code"] for i in out["items"]), out["total"]


def _shift_list_codes(db, w, client_as, user, **params):
    res = client_as(user).get(URL, params={"from_date": MON.isoformat(), "to_date": MON.isoformat(), **params})
    assert res.status_code == 200, res.text
    by_id = {e.id: e.code for e in (w.mgr, w.a1, w.a2, w.b1, w.hr)}
    return sorted(by_id[i["employee_id"]] for i in res.json()["data"]["items"])


def _ai_codes(db, user, **args):
    out = T.run_tool(db, db.get(User, user.id), "employee_work_shifts",
                     {"from_date": MON.isoformat(), "to_date": MON.isoformat(), **args})
    return sorted(e["code"] for e in out.get("employees", [])), out


def test_truong_phong_chi_thay_phong_minh_du_doc_ho_so_moi_nguoi(db, w, seen, client_as):
    own = sorted([w.mgr.code, w.a1.code, w.a2.code])
    assert _roster_codes(db, seen.head) == (own, 3)                                  # lưới + tổng
    assert _shift_list_codes(db, w, client_as, seen.head) == own                    # danh sách ca
    codes, _ = _ai_codes(db, seen.head, department=str(w.dept_a.id))
    assert codes == own and _ai_codes(db, seen.head, department=str(w.dept_b.id))[0] == []   # phòng B: ngoài tầm
    #  Lọc ngoài tập: rỗng, không lộ người đó có thật không.
    assert _roster_codes(db, seen.head, department_id=w.dept_b.id) == ([], 0)
    assert _shift_list_codes(db, w, client_as, seen.head, employee_id=w.b1.id) == []
    assert _shift_list_codes(db, w, client_as, seen.head, department_id=w.dept_b.id) == []
    assert _ai_codes(db, seen.head, employee=w.b1.code)[1]["employees"] == []
    #  Bộ lọc phòng / người vẫn AND bên trong tập thấy được.
    assert _roster_codes(db, seen.head, department_id=w.dept_a.id, q="A1") == ([w.a1.code], 1)


def test_nhan_vien_chi_thay_chinh_minh_o_ca_ba_duong(db, w, seen, client_as):
    assert _roster_codes(db, seen.staff) == ([w.a2.code], 1)
    assert _shift_list_codes(db, w, client_as, seen.staff) == [w.a2.code]
    assert _ai_codes(db, seen.staff, department=str(w.dept_a.id))[0] == [w.a2.code]       # cùng phòng nhưng chỉ mình
    assert _shift_list_codes(db, w, client_as, seen.staff, employee_id=w.a1.id) == []
    assert _roster_codes(db, seen.staff, q="A1") == ([], 0)


def test_tai_khoan_chua_gan_ho_so_khong_thay_ai(db, w, seen, client_as):
    assert _roster_codes(db, seen.orphan) == ([], 0)
    assert _shift_list_codes(db, w, client_as, seen.orphan) == []
    assert _ai_codes(db, seen.orphan, department=str(w.dept_a.id))[0] == []


def test_nhan_su_va_quan_tri_thay_het(db, w, seen, client_as, cap_quyen):
    everyone = sorted(e.code for e in (w.mgr, w.a1, w.a2, w.b1, w.hr))
    assert _roster_codes(db, w.hr_user) == (everyone, 5)
    assert _shift_list_codes(db, w, client_as, w.hr_user) == everyone
    from app.modules.role.model import Role
    from app.modules.user.model import UserRole
    role = Role(code="admin", name="Quản trị hệ thống")
    db.add(role)
    db.flush()
    db.add(UserRole(user_id=seen.staff.id, role_id=role.id))     # quản trị nhưng KHÔNG có khóa work_schedule
    db.commit()
    assert _roster_codes(db, seen.staff) == (everyone, 5)


def test_truong_phong_thay_ca_phong_kiem_nhiem(db, w, seen, client_as):
    from app.core.auth import perm_cache_clear
    from app.modules.employee.concurrent_model import EmployeeConcurrent
    db.add(EmployeeConcurrent(employee_id=w.mgr.id, kind=1, company_id=w.company.id, department_id=w.dept_b.id,
                              from_date=date(2020, 1, 1), to_date=None, counts_scope=True))
    db.commit()
    perm_cache_clear(seen.head.id)
    assert _roster_codes(db, seen.head) == (sorted(e.code for e in (w.mgr, w.a1, w.a2, w.b1, w.hr)), 5)   # + phòng B
    assert _shift_list_codes(db, w, client_as, seen.head, department_id=w.dept_b.id) == sorted([w.b1.code, w.hr.code])
    assert sorted(_ai_codes(db, seen.head, department=str(w.dept_b.id))[0]) == sorted([w.b1.code, w.hr.code])


def test_roster_theo_quyen_so_truy_van_co_dinh(db, w, seen):
    for i in range(20):
        e = _emp(db, f"VQ{i:02d}", w.company, w.dept_a.id)
        put_shift(db, e, MON, [(8, 12)])
    db.commit()
    for user in (seen.head, seen.staff, w.hr_user):
        profile = get_perm_profile(db, user)
        _roster(db, user, profile)                                                  # nạp sẵn
        small, q_small = count_queries(db, lambda: _roster(db, user, profile, page_size=2))
        big, q_big = count_queries(db, lambda: _roster(db, user, profile, page_size=50))
        assert len(q_small) == len(q_big) <= 13, (user.email, len(q_small), len(q_big))
    assert _roster_codes(db, seen.head)[1] == 23 and _roster_codes(db, seen.staff)[1] == 1


def test_quan_ly_cong_ty_xem_ca_ca_cong_ty_khong_ghi_duoc(db, w, seen, client_as, cap_quyen):
    """Vai trò seed `company_head`: `work_schedule_personal` CHỈ ĐỌC bậc công ty → thấy cả công ty mình, không công ty khác,
    và không xếp được ca (thiếu `write`)."""
    from app.seed import STD_ROLES
    perms, scope = STD_ROLES["company_head"]["perms"]["work_schedule_personal"]
    assert perms == ["read"] and scope == "company"
    other_co = Company(name="Cty khác 758", code="C758X", is_active=True)
    db.add(other_co)
    db.flush()
    foreign = _emp(db, "KH758", other_co, 0)
    put_shift(db, foreign, MON, [(8, 12)])
    director = User(email="gd758@dego.vn", employee_id=w.mgr.id, password_hash="x", is_active=True)
    db.add(director)
    db.flush()
    cap_quyen(director.id, "employee", scope="company", read=True)               # như seed company_head
    cap_quyen(director.id, "work_schedule_personal", scope="company", read=True)
    db.commit()
    own = sorted(e.code for e in (w.mgr, w.a1, w.a2, w.b1, w.hr))
    assert _roster_codes(db, director) == (own, 5)
    assert "KH758" not in _roster_codes(db, director, q="KH758")[0]
    assert _shift_list_codes(db, w, client_as, director) == own
    assert _ai_codes(db, director, department=str(w.dept_b.id))[0] == sorted([w.b1.code, w.hr.code])
    assert _ai_codes(db, director, employee="KH758")[1]["employees"] == []
    res = _put(client_as(director), w.a1, _future_monday(), [(8, 12)])               # đọc được nhưng KHÔNG ghi
    assert res.status_code == 403
    assert client_as(director).post(f"{URL}/bulk", json={"employee_ids": [w.a1.id], "dates": [_future_monday().isoformat()],
                                                        "segments": []}).status_code == 403
    assert db.query(WorkShiftDay).filter_by(employee_id=w.a1.id, work_date=_future_monday()).count() == 0
