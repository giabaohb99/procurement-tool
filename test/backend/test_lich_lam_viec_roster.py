"""Lịch làm việc phase 07 — API «Ai làm / ai nghỉ» `/api/work-schedules/tools/roster`.

Mốc ngày cố định: 05/01/2026 là thứ Hai (không phụ thuộc "hôm nay"). Chạy qua HTTP thật
(TestClient + SQLite) để phạm vi, validate tham số và đếm truy vấn đều là hành vi thấy được.
"""
import uuid
from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.scoping import get_perm_profile
from app.core.work_schedule_codes import WorkScheduleLevel
from app.main import app
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.leave.catalog_model import Holiday, LeaveType
from app.modules.leave.constants import (LR_APPROVED, LR_CANCELLED, LR_DRAFT, LR_PENDING,
                                         LR_REJECTED, SESSION_AFTERNOON, SESSION_FULL,
                                         SESSION_HOURLY, SESSION_MORNING)
from app.modules.leave.request_model import LeaveRequest
from app.modules.user.model import User
from app.modules.work_schedule.roster_service import build_roster
from lich_lam_viec_factory import (FULL, OFF, MON, assign, count_queries, make_schedule,
                                   make_world)

URL = "/api/work-schedules/tools/roster"
WEEK = {"from_date": "2026-01-05", "to_date": "2026-01-11"}
_seq = {"n": 0}


def _emp(db, company, dept, name=None, **kw):
    _seq["n"] += 1
    code = kw.pop("code", f"E{_seq['n']:04d}")
    e = Employee(code=code, full_name=name or f"Người {code}", company_id=company.id,
                 department_id=dept.id, is_active=True, **kw)
    db.add(e)
    db.flush()
    return e


def _leave(db, emp, from_d, to_d, status=LR_APPROVED, fs=SESSION_FULL, ts=SESSION_FULL,
           created_by=0, **kw):
    _seq["n"] += 1
    r = LeaveRequest(code=f"NP-T-{_seq['n']:05d}", company_id=emp.company_id,
                     department_id=emp.department_id, employee_id=emp.id,
                     leave_type_id=kw.pop("leave_type_id", 0), from_date=from_d, to_date=to_d,
                     from_session=fs, to_session=ts, status=status, created_by=created_by, **kw)
    db.add(r)
    db.flush()
    return r


def _use(user):
    app.dependency_overrides[get_current_user] = lambda: user


@pytest.fixture
def api(db, cap_quyen):
    company, dept, emp = make_world(db, "R01")
    user = User(email="hr-roster@dego.vn", employee_id=emp.id, is_active=True)
    db.add(user)
    db.commit()
    cap_quyen(user.id, "employee", scope="all", read=True)
    cap_quyen(user.id, "leave_request", scope="all", read=True)
    app.dependency_overrides[get_db] = lambda: db
    _use(user)
    client = TestClient(app, headers={"Authorization": f"Bearer t-{uuid.uuid4().hex}"})
    client.world, client.user = (company, dept, emp), user
    yield client
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _get(api, **kw):
    res = api.get(URL, params={**WEEK, **kw})
    return res


def _row(res, emp):
    return next(i for i in res.json()["data"]["items"] if i["employee_id"] == emp.id)


# ── Hình dạng hợp đồng + lịch hiệu lực ────────────────────────────────────────

def test_hinh_dang_hop_dong_va_lich_mac_dinh(api):
    _, _, emp = api.world
    data = _get(api).json()["data"]
    assert data["from_date"] == "2026-01-05" and data["to_date"] == "2026-01-11" and data["total"] == 1
    assert [d["weekday"] for d in data["days"]] == list(range(7))
    row = data["items"][0]
    assert (row["employee_id"], row["code"]) == (emp.id, "R01") and row["department_name"]
    mon, sun = row["cells"][0], row["cells"][6]
    assert mon == {"date": "2026-01-05", "work_kind": 2, "start_time": "08:00", "end_time": "17:00",
                   "schedule_name": mon["schedule_name"], "is_holiday": False, "holiday_name": "",
                   "leave": None}
    assert sun["work_kind"] == 1 and sun["start_time"] is None and sun["leave"] is None


def test_ranh_hieu_luc_gan_giua_ky(api, db):
    _, _, emp = api.world
    sched = make_schedule(db, "Nghỉ thứ Tư", [FULL, FULL, OFF, FULL, FULL, FULL, OFF])
    assign(db, WorkScheduleLevel.EMPLOYEE, emp.id, sched.id, date(2026, 1, 7), date(2026, 1, 8))
    cells = _row(_get(api), emp)["cells"]
    assert [c["work_kind"] for c in cells[:5]] == [2, 2, 1, 2, 2]      # T4 theo mẫu, T5 đã hết hiệu lực… 
    assert cells[2]["schedule_name"] == "Nghỉ thứ Tư"
    assert cells[1]["schedule_name"] != "Nghỉ thứ Tư" and cells[4]["schedule_name"] != "Nghỉ thứ Tư"


# ── Nghỉ phép ─────────────────────────────────────────────────────────────────

def test_chua_duyet_va_da_duyet_nua_buoi(api, db):
    company, dept, emp = api.world
    lt = LeaveType(code="PN", name="Phép năm", is_active=True)
    db.add(lt)
    db.flush()
    _leave(db, emp, date(2026, 1, 5), date(2026, 1, 5), LR_APPROVED, SESSION_AFTERNOON, SESSION_FULL,
           leave_type_id=lt.id)                                          # chỉ chiều T2
    _leave(db, emp, date(2026, 1, 6), date(2026, 1, 6), LR_PENDING, SESSION_FULL, SESSION_MORNING)
    _leave(db, emp, date(2026, 1, 7), date(2026, 1, 8))                  # cả ngày T4–T5
    cells = _row(_get(api), emp)["cells"]
    mon, tue, wed = cells[0]["leave"], cells[1]["leave"], cells[2]["leave"]
    assert (mon["morning"], mon["afternoon"], mon["is_approved"]) == (False, True, True)
    assert mon["leave_type_name"] == "Phép năm" and mon["status_label"] == "Đã duyệt"
    assert (tue["morning"], tue["afternoon"], tue["is_approved"], tue["status"]) == (True, False, False, LR_PENDING)
    assert (wed["morning"], wed["afternoon"]) == (True, True) and cells[3]["leave"]["request_id"] == wed["request_id"]
    assert cells[4]["leave"] is None


def test_nghi_theo_gio_chi_to_nua_buoi_co_gio(api, db):
    _, _, emp = api.world
    _leave(db, emp, MON, MON, fs=SESSION_HOURLY, ts=SESSION_HOURLY,
           from_time=time(9, 0), to_time=time(10, 0))
    leave = _row(_get(api), emp)["cells"][0]["leave"]
    assert (leave["morning"], leave["afternoon"]) == (True, False)


@pytest.mark.parametrize("status", [LR_DRAFT, LR_REJECTED, LR_CANCELLED, 5])
def test_don_nhap_tu_choi_huy_tra_ve_khong_hien(api, db, status):
    _, _, emp = api.world
    _leave(db, emp, MON, MON, status)
    assert _row(_get(api), emp)["cells"][0]["leave"] is None


def test_don_xoa_mem_khong_hien(api, db):
    _, _, emp = api.world
    _leave(db, emp, MON, MON, is_deleted=True)
    assert _row(_get(api), emp)["cells"][0]["leave"] is None


def test_chong_don_uu_tien_da_duyet(api, db):
    _, _, emp = api.world
    pend = _leave(db, emp, MON, MON, LR_PENDING)
    appr = _leave(db, emp, MON, MON, LR_APPROVED)
    assert pend.id < appr.id
    assert _row(_get(api), emp)["cells"][0]["leave"]["request_id"] == appr.id


def test_nghi_giua_ky_cat_theo_khoang_va_khong_to_ngay_khong_lam(api, db):
    _, _, emp = api.world
    _leave(db, emp, date(2025, 12, 1), date(2026, 3, 1))   # đơn dài bao trùm cả tuần
    cells = _row(_get(api), emp)["cells"]
    assert all(c["leave"] for c in cells[:6])
    assert cells[6]["leave"] is None                        # Chủ nhật vốn nghỉ — không tô thêm


def test_ngay_le_theo_phap_nhan_va_dau_trang(api, db):
    company, dept, emp = api.world
    other_co = Company(name="Cty khác", code="CKHAC", is_active=True)
    db.add(other_co)
    db.flush()
    other_dept = Department(code="DK", name="Phòng khác", company_id=other_co.id, is_active=True)
    db.add(other_dept)
    db.flush()
    emp2 = _emp(db, other_co, other_dept)
    db.add(Holiday(company_id=0, date=date(2026, 1, 6), name="Lễ chung", is_active=True))
    db.add(Holiday(company_id=company.id, date=date(2026, 1, 7), name="Lễ riêng R01", is_active=True))
    db.add(Holiday(company_id=0, date=date(2020, 1, 8), name="Lễ lặp", is_recurring=True, is_active=True))
    _leave(db, emp, date(2026, 1, 6), date(2026, 1, 6))     # nghỉ đúng ngày lễ → không tô
    res = _get(api)
    days = res.json()["data"]["days"]
    #  tiêu đề cột chỉ mang lễ CHUNG — lễ riêng R01 không được dán lên cả lưới của pháp nhân khác
    assert [d["holiday_name"] for d in days][:4] == ["", "Lễ chung", "", "Lễ lặp"]
    mine, theirs = _row(res, emp)["cells"], _row(res, emp2)["cells"]
    assert [c["is_holiday"] for c in mine[:4]] == [False, True, True, True]
    assert [c["is_holiday"] for c in theirs[:4]] == [False, True, False, True]   # lễ riêng không rò sang pháp nhân khác
    assert mine[1]["leave"] is None
    assert [c["holiday_name"] for c in mine[:4]] == ["", "Lễ chung", "Lễ riêng R01", "Lễ lặp"]
    assert [c["holiday_name"] for c in theirs[:4]] == ["", "Lễ chung", "", "Lễ lặp"]


# ── Phạm vi ───────────────────────────────────────────────────────────────────

def test_nguoi_ngoai_pham_vi_employee_khong_ra(api, db, cap_quyen):
    company, dept, emp = api.world
    other = _emp(db, company, dept)
    viewer = User(email="own@dego.vn", employee_id=emp.id, is_active=True)
    db.add(viewer)
    db.commit()
    cap_quyen(viewer.id, "employee", scope="own", read=True)
    _use(viewer)
    data = _get(api).json()["data"]
    assert [i["employee_id"] for i in data["items"]] == [emp.id] and data["total"] == 1
    assert other.id not in [i["employee_id"] for i in data["items"]]


def test_don_ngoai_pham_vi_leave_request_khong_ro_dung_khi_thay_nhan_su(api, db, cap_quyen):
    company, dept, emp = api.world
    other = _emp(db, company, dept)
    secret = _leave(db, other, MON, MON, created_by=0)       # đơn của người khác, người khác lập
    mine = _leave(db, emp, date(2026, 1, 6), date(2026, 1, 6), created_by=api.user.id)
    viewer = User(email="lim@dego.vn", employee_id=emp.id, is_active=True)
    db.add(viewer)
    db.commit()
    cap_quyen(viewer.id, "employee", scope="all", read=True)
    cap_quyen(viewer.id, "leave_request", scope="own", read=True)
    _use(viewer)
    res = _get(api)
    other_cells = _row(res, other)["cells"]                  # HÀNG vẫn thấy (employee.all)…
    assert other_cells[0]["leave"] is None                   # …nhưng đơn thì không lộ
    assert other_cells[0]["work_kind"] == 2
    assert _row(res, emp)["cells"][1]["leave"]["request_id"] == mine.id
    assert secret.code not in str(res.json())


def test_khong_co_quyen_leave_request_thi_khong_lop_nghi(api, db, cap_quyen):
    company, dept, emp = api.world
    _leave(db, emp, MON, MON)
    viewer = User(email="noleave@dego.vn", employee_id=emp.id, is_active=True)
    db.add(viewer)
    db.commit()
    cap_quyen(viewer.id, "employee", scope="all", read=True)   # không có grant leave_request nào
    _use(viewer)
    res = _get(api)
    assert res.status_code == 200 and _row(res, emp)["cells"][0]["leave"] is None


def test_thieu_quyen_employee_read_403(api, db):
    nobody = User(email="nobody@dego.vn", employee_id=0, is_active=True)
    db.add(nobody)
    db.commit()
    _use(nobody)
    assert _get(api).status_code == 403


# ── Nghỉ việc, lọc, sắp xếp, phân trang ───────────────────────────────────────

def test_nghi_viec_truoc_ky_bi_loai_sau_ky_van_hien(api, db):
    company, dept, emp = api.world
    gone_status = _emp(db, company, dept, status="resigned")
    gone_inactive = _emp(db, company, dept)
    gone_inactive.is_active = False
    gone_date = _emp(db, company, dept, resign_date=date(2026, 1, 4))      # nghỉ hôm trước kỳ
    last_day = _emp(db, company, dept, resign_date=date(2026, 1, 5))       # còn làm đúng ngày đầu kỳ
    future = _emp(db, company, dept, resign_date=date(2026, 2, 1))
    db.flush()
    ids = {i["employee_id"] for i in _get(api).json()["data"]["items"]}
    assert ids == {emp.id, last_day.id, future.id}
    assert not ({gone_status.id, gone_inactive.id, gone_date.id} & ids)


def test_loc_phong_ban_cong_ty_tim_kiem_va_ky_tu_dac_biet(api, db):
    company, dept, emp = api.world
    d2 = Department(code="DB2", name="A-Phòng đầu", company_id=company.id, is_active=True)
    db.add(d2)
    db.flush()
    anna = _emp(db, company, d2, name="Anna Zed", code="ZZ1")
    _emp(db, company, d2, name="Bob 100% đúng", code="ZZ2")
    data = _get(api).json()["data"]
    assert [i["employee_id"] for i in data["items"]][0] == anna.id      # sắp phòng ban (A-…) rồi tên
    assert len(_get(api, department_id=d2.id).json()["data"]["items"]) == 2
    assert len(_get(api, company_id=company.id + 99).json()["data"]["items"]) == 0
    assert [i["code"] for i in _get(api, q="anna").json()["data"]["items"]] == ["ZZ1"]
    #  hacker gõ ký tự đại diện: `%` / `_` phải là chữ thường, không khớp mọi dòng
    assert _get(api, q="%").json()["data"]["total"] == 1                # chỉ «Bob 100% đúng»
    assert _get(api, q="_").json()["data"]["total"] == 0


def test_phan_trang_tong_khong_doi(api, db):
    company, dept, emp = api.world
    for _ in range(4):
        _emp(db, company, dept)
    p1 = _get(api, page_size=2, page=1).json()["data"]
    p3 = _get(api, page_size=2, page=3).json()["data"]
    p2 = _get(api, page_size=2, page=2).json()["data"]
    assert (p1["total"], len(p1["items"]), len(p2["items"]), len(p3["items"])) == (5, 2, 2, 1)
    seen = [i["employee_id"] for p in (p1, p2, p3) for i in p["items"]]
    assert len(set(seen)) == 5
    assert _get(api, page=99).json()["data"]["items"] == []


# ── Kiểm tham số ──────────────────────────────────────────────────────────────

def test_toi_da_42_ngay_43_ngay_loi(api):
    assert _get(api, from_date="2026-01-05", to_date="2026-02-15").status_code == 200   # 42 ngày
    res = _get(api, from_date="2026-01-05", to_date="2026-02-16")                        # 43 ngày
    assert res.status_code == 422
    assert len(_get(api, from_date="2026-01-05", to_date="2026-02-15").json()["data"]["days"]) == 42


@pytest.mark.parametrize("params", [
    {"from_date": "2026-01-11", "to_date": "2026-01-05"},      # ngược
    {"from_date": "1999-12-31", "to_date": "2000-01-02"},      # năm ngoài dải
    {"from_date": "2100-12-30", "to_date": "2101-01-02"},
    {"from_date": "không-phải-ngày", "to_date": "2026-01-05"},
    {"page": 0}, {"page_size": 0}, {"page_size": 101}, {"q": "x" * 101}, {"company_id": -1},
])
def test_tham_so_sai_422(api, params):
    assert _get(api, **params).status_code == 422


def test_thieu_tham_so_bat_buoc_422(api):
    assert api.get(URL).status_code == 422
    assert api.get(URL, params={"from_date": "2026-01-05"}).status_code == 422


def test_mot_ngay_la_hop_le(api):
    data = _get(api, from_date="2026-01-05", to_date="2026-01-05").json()["data"]
    assert len(data["days"]) == 1 and len(data["items"][0]["cells"]) == 1


def test_khong_co_nhan_su_tra_danh_sach_rong(api, db):
    company, dept, emp = api.world
    emp.is_active = False
    db.flush()
    data = _get(api).json()["data"]
    assert data["items"] == [] and data["total"] == 0 and len(data["days"]) == 7


# ── Hiệu năng: số truy vấn CỐ ĐỊNH ────────────────────────────────────────────

def _prep_world(db, n_emp: int, tag: str):
    company, dept, first = make_world(db, tag)
    sched = make_schedule(db, f"Mẫu {tag}", [FULL] * 5 + [OFF, OFF])
    assign(db, WorkScheduleLevel.DEPARTMENT, dept.id, sched.id, date(2020, 1, 1))
    db.add(Holiday(company_id=company.id, date=date(2026, 1, 8), name="Lễ", is_active=True))
    emps = [first] + [_emp(db, company, dept) for _ in range(n_emp - 1)]
    for i, e in enumerate(emps):
        if i % 3 == 0:
            assign(db, WorkScheduleLevel.EMPLOYEE, e.id, sched.id, date(2026, 1, 1 + i % 20), None)
        _leave(db, e, MON, date.fromordinal(MON.toordinal() + 1 + i % 30))
    db.commit()
    return emps


def _admin(db, cap_quyen, tag):
    user = User(email=f"{tag}@dego.vn", employee_id=0, is_active=True)
    db.add(user)
    db.commit()
    cap_quyen(user.id, "employee", scope="all", read=True)
    cap_quyen(user.id, "leave_request", scope="all", read=True)
    return user


def test_so_truy_van_khong_phu_thuoc_so_nguoi_va_so_ngay(db, cap_quyen):
    user = _admin(db, cap_quyen, "perf")
    _prep_world(db, 50, "PERF")
    profile = get_perm_profile(db, user)

    def run(page_size, days):
        p = {"from_date": MON, "to_date": date.fromordinal(MON.toordinal() + days - 1),
             "company_id": 0, "department_id": 0, "q": "", "page": 1, "page_size": page_size}
        return count_queries(db, lambda: build_roster(db, user, profile, p))

    small, q_small = run(5, 7)
    big, q_big = run(50, 42)
    assert len(small["items"]) == 5 and len(big["items"]) == 50
    assert len(big["items"][0]["cells"]) == 42
    assert len(q_small) == len(q_big), (len(q_small), len(q_big))
    assert len(q_big) <= 8, [s[:80] for s in q_big]
