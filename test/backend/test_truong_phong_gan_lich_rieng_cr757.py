"""duoc-CR-757 lượt 2 — Trưởng phòng gán lịch làm việc RIÊNG + quỹ phép bậc phòng đúng phòng.

Q1: khóa `work_schedule_personal` — Trưởng phòng gán lịch cấp Nhân sự cho người trong phạm vi; chỉ mẫu đang dùng; không
đụng mẫu lịch / cấp phòng ban / pháp nhân / toàn hệ thống; không gán cho chính mình. Đường Nhân sự (`work_schedule.*`) giữ nguyên.
Q2: `leave_balance` bậc `dept` đi qua phòng ban của hồ sơ nhân sự (chính + kiêm nhiệm), không còn là cả công ty.
"""
import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user, perm_cache_clear
from app.core.database import get_db
from app.core.report_period import parse_period
from app.core.vn_time import vn_today
from app.core.scoping import SCOPE_FIELDS
from app.core.work_schedule_codes import WorkScheduleLevel as L
from app.main import app
from app.modules.assistant.tools.base import ToolContext
from app.modules.assistant.tools.employee_leave_tool import EMPLOYEE_LEAVE_SUMMARY_SPEC
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.model import Employee
from app.modules.leave import balance_report_service, workday_service
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.user.model import User
from app.modules.work_schedule.model import WorkScheduleAssignment
from lich_lam_viec_factory import FULL, OFF, assign, count_queries, make_schedule

URL = "/api/work-schedule-assignments"
LONG_AGO = date(2020, 1, 1)
NOT_FOUND_TARGET = "Đối tượng được gán lịch không tồn tại"
WEEK_MON_FRI = [FULL] * 5 + [OFF, OFF]           # T7 nghỉ: 5 ngày công / tuần
YEAR = 2026


class World:
    """Một công ty, hai phòng (A của trưởng phòng, B phòng khác), ba mẫu lịch."""


def _emp(db, code, company, dept_id):
    emp = Employee(code=code, full_name=f"Người {code}", company_id=company.id, department_id=dept_id, is_active=True)
    db.add(emp)
    db.flush()
    return emp


def _user(db, emp, email):
    user = User(email=email, employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def w(db, cap_quyen):
    world = World()
    world.company = Company(name="Cty 757b", code="C757B", is_active=True)
    db.add(world.company)
    db.flush()
    world.dept_a = Department(code="D757A", name="Phòng A", company_id=world.company.id, is_active=True)
    world.dept_b = Department(code="D757B", name="Phòng B", company_id=world.company.id, is_active=True)
    db.add_all([world.dept_a, world.dept_b])
    db.flush()
    world.mgr = _emp(db, "TP757", world.company, world.dept_a.id)
    world.a1 = _emp(db, "A1757", world.company, world.dept_a.id)
    world.a2 = _emp(db, "A2757", world.company, world.dept_a.id)
    world.b1 = _emp(db, "B1757", world.company, world.dept_b.id)
    world.nodept = _emp(db, "ND757", world.company, 0)
    world.mgr_user = _user(db, world.mgr, "tp757@dego.vn")
    world.hr_user = _user(db, _emp(db, "HR757", world.company, world.dept_b.id), "hr757@dego.vn")
    world.sched = make_schedule(db, "Lịch T2-T6", WEEK_MON_FRI)
    world.sched2 = make_schedule(db, "Lịch T2-T6 bản 2", WEEK_MON_FRI)
    world.off_sched = make_schedule(db, "Lịch đã tắt", WEEK_MON_FRI, is_active=False)
    #  Trưởng phòng: đọc lịch (mọi vai trò có) + khóa riêng bậc phòng + hồ sơ bậc phòng.
    cap_quyen(world.mgr_user.id, "work_schedule", scope="all", read=True)
    cap_quyen(world.mgr_user.id, "work_schedule_personal", scope="dept",
              read=True, create=True, write=True, delete=True)
    cap_quyen(world.mgr_user.id, "employee", scope="dept", read=True)
    #  Nhân sự: khóa cũ, mọi cấp.
    cap_quyen(world.hr_user.id, "work_schedule", scope="all", read=True, create=True, write=True, delete=True)
    cap_quyen(world.hr_user.id, "employee", scope="all", read=True)
    db.commit()
    return world


@pytest.fixture
def client_as(db):
    """`client_as(user)` → TestClient chạy dưới quyền `user`; dọn override khi bài xong."""
    def _make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer t-{uuid.uuid4().hex}"})

    yield _make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _today():
    return vn_today()


def _next_week():
    """Thứ Hai và thứ Bảy của tuần SAU (luôn sau hôm nay, nằm trong lịch bắt đầu từ hôm nay)."""
    monday = _today() + timedelta(days=7 - _today().weekday())
    return monday, monday + timedelta(days=5)


def _body(level, target, schedule_id, start=None, end=None):
    start = start or _today().isoformat()
    return {"target_level": int(level), "target_id": target, "schedule_id": schedule_id,
            "effective_from": start, "effective_to": end, "note": ""}


def _days():
    days = [{"weekday": i, "day_kind": 2, "start_time": "08:00", "end_time": "17:00",
             "lunch_start": "12:00", "lunch_end": "13:00"} for i in range(6)]
    return days + [{"weekday": 6, "day_kind": 1}]


def _rows(db, level, target_id):
    return db.query(WorkScheduleAssignment).filter(
        WorkScheduleAssignment.target_level == int(level),
        WorkScheduleAssignment.target_id == target_id).order_by(WorkScheduleAssignment.effective_from).all()


# ── Q1: Trưởng phòng gán lịch riêng ───────────────────────────────────────────────────

def test_truong_phong_gan_lich_rieng_cho_nguoi_phong_minh_va_so_ngay_nghi_doi(w, db, client_as):
    mon, sat = _next_week()
    before = workday_service.count_leave_days(db, mon, sat, employee=w.a1)
    assert before == 6.0   # mặc định T2–T7
    client = client_as(w.mgr_user)
    res = client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id))
    assert res.status_code == 201, res.text
    assert res.json()["data"]["target_name"] == w.a1.full_name
    assert workday_service.count_leave_days(db, mon, sat, employee=w.a1) == 5.0   # T7 nghỉ theo lịch riêng
    assert workday_service.count_leave_days(db, mon, sat, employee=w.a2) == 6.0   # người khác không đổi
    #  Đọc: trưởng phòng thấy dòng lịch riêng của người phòng mình (khóa `work_schedule.read`, lọc `employee.read`).
    listed = client.get(URL, params={"target_level": int(L.EMPLOYEE), "target_id": w.a1.id}).json()["data"]
    assert listed["total"] == 1 and listed["items"][0]["schedule_name"] == w.sched.name


def test_nguoi_phong_khac_bi_400_cung_cau_voi_id_khong_ton_tai(w, db, client_as):
    client = client_as(w.mgr_user)
    other = client.post(URL, json=_body(L.EMPLOYEE, w.b1.id, w.sched.id))
    ghost = client.post(URL, json=_body(L.EMPLOYEE, 9_999_999, w.sched.id))
    nodept = client.post(URL, json=_body(L.EMPLOYEE, w.nodept.id, w.sched.id))
    assert other.status_code == ghost.status_code == nodept.status_code == 400
    assert other.json()["error"]["message"] == ghost.json()["error"]["message"] == NOT_FOUND_TARGET
    assert _rows(db, L.EMPLOYEE, w.b1.id) == []


def test_khong_tu_gan_cho_chinh_minh(w, db, client_as):
    client = client_as(w.mgr_user)
    res = client.post(URL, json=_body(L.EMPLOYEE, w.mgr.id, w.sched.id))
    assert res.status_code == 403 and "chính mình" in res.json()["error"]["message"]
    assert _rows(db, L.EMPLOYEE, w.mgr.id) == []


@pytest.mark.parametrize("level_name,target", [("SYSTEM", "none"), ("COMPANY", "company"), ("DEPARTMENT", "dept_a")])
def test_cap_khac_nhan_su_bi_403(w, db, client_as, level_name, target):
    target_id = {"none": 0, "company": w.company.id, "dept_a": w.dept_a.id}[target]
    res = client_as(w.mgr_user).post(URL, json=_body(L[level_name], target_id, w.sched.id))
    assert res.status_code == 403
    assert _rows(db, L[level_name], target_id) == []


def test_khong_dung_vao_mau_lich(w, client_as):
    client = client_as(w.mgr_user)
    body = {"name": "Mẫu lạ", "note": "", "is_active": True, "days": _days()}
    assert client.post("/api/work-schedules", json=body).status_code == 403
    assert client.patch(f"/api/work-schedules/{w.sched.id}", json={"name": "Đổi tên"}).status_code == 403
    assert client.delete(f"/api/work-schedules/{w.sched.id}").status_code == 403
    #  Xem danh sách mẫu để chọn vẫn được (khóa đọc).
    assert client.get("/api/work-schedules").status_code == 200


def test_mau_lich_da_tat_khong_gan_duoc(w, db, client_as):
    res = client_as(w.mgr_user).post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.off_sched.id))
    assert res.status_code == 400 and "đã tắt" in res.json()["error"]["message"]
    assert _rows(db, L.EMPLOYEE, w.a1.id) == []


def test_sua_dong_lich_rieng_trong_pham_vi_va_chan_chuyen_sang_nguoi_ngoai_pham_vi(w, db, client_as):
    client = client_as(w.mgr_user)
    row_id = client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id)).json()["data"]["id"]
    #  Đổi mẫu + chuyển sang người khác CÙNG phòng: được.
    ok = client.patch(f"{URL}/{row_id}", json={"schedule_id": w.sched2.id, "target_id": w.a2.id})
    assert ok.status_code == 200 and ok.json()["data"]["target_id"] == w.a2.id
    #  Chuyển sang người phòng khác / chính mình / đổi cấp: bị chặn, dòng không đổi.
    to_b = client.patch(f"{URL}/{row_id}", json={"target_id": w.b1.id})
    to_self = client.patch(f"{URL}/{row_id}", json={"target_id": w.mgr.id})
    to_dept = client.patch(f"{URL}/{row_id}", json={"target_level": int(L.DEPARTMENT), "target_id": w.dept_a.id})
    assert (to_b.status_code, to_self.status_code, to_dept.status_code) == (400, 403, 403)
    assert to_b.json()["error"]["message"] == NOT_FOUND_TARGET
    db.expire_all()
    assert db.get(WorkScheduleAssignment, row_id).target_id == w.a2.id


def test_khong_sua_xoa_dong_cap_khac_dong_nguoi_phong_khac_va_dong_cua_chinh_minh(w, db, client_as):
    dept_row = assign(db, L.DEPARTMENT, w.dept_a.id, w.sched.id, LONG_AGO)
    b_row = assign(db, L.EMPLOYEE, w.b1.id, w.sched.id, LONG_AGO)
    own_row = assign(db, L.EMPLOYEE, w.mgr.id, w.sched.id, LONG_AGO)
    db.commit()
    client = client_as(w.mgr_user)
    for row, expected in ((dept_row, 403), (b_row, 404), (own_row, 403)):
        assert client.patch(f"{URL}/{row.id}", json={"note": "x"}).status_code == expected, row.id
        assert client.delete(f"{URL}/{row.id}").status_code == expected, row.id
    db.expire_all()
    assert all(db.get(WorkScheduleAssignment, r.id) is not None and db.get(WorkScheduleAssignment, r.id).note == ""
               for r in (dept_row, b_row, own_row))


def test_xoa_dong_lich_rieng_cua_nguoi_trong_phong(w, db, client_as):
    client = client_as(w.mgr_user)
    row_id = client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id)).json()["data"]["id"]
    assert client.delete(f"{URL}/{row_id}").status_code == 200
    assert _rows(db, L.EMPLOYEE, w.a1.id) == []
    assert workday_service.count_leave_days(db, *_next_week(), employee=w.a1) == 6.0   # trả về lịch mặc định


def test_tu_dong_dong_va_mo_lai_chi_cham_dong_cua_cung_nhan_su(w, db, client_as):
    """Dòng gán mới tự đóng dòng 'không thời hạn' cũ; xóa nó thì mở lại — chỉ trong CÙNG một nhân sự."""
    old_a1 = assign(db, L.EMPLOYEE, w.a1.id, w.sched.id, LONG_AGO)
    old_a2 = assign(db, L.EMPLOYEE, w.a2.id, w.sched.id, LONG_AGO)
    old_b1 = assign(db, L.EMPLOYEE, w.b1.id, w.sched.id, LONG_AGO)
    db.commit()
    client = client_as(w.mgr_user)
    new_id = client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched2.id, start=(_today() + timedelta(days=10)).isoformat())).json()["data"]["id"]
    db.expire_all()
    assert db.get(WorkScheduleAssignment, old_a1.id).effective_to == _today() + timedelta(days=9)
    assert db.get(WorkScheduleAssignment, old_a2.id).effective_to is None
    assert db.get(WorkScheduleAssignment, old_b1.id).effective_to is None
    assert client.delete(f"{URL}/{new_id}").status_code == 200
    db.expire_all()
    assert db.get(WorkScheduleAssignment, old_a1.id).effective_to is None   # mở lại
    assert db.get(WorkScheduleAssignment, old_a2.id).effective_to is None
    assert db.get(WorkScheduleAssignment, old_b1.id).effective_to is None


def test_khoa_rieng_pham_vi_own_thi_khong_gan_cho_nguoi_khac(w, db, client_as, cap_quyen):
    user = _user(db, _emp(db, "OWN757", w.company, w.dept_a.id), "own757@dego.vn")
    cap_quyen(user.id, "work_schedule", scope="all", read=True)
    cap_quyen(user.id, "work_schedule_personal", scope="own", create=True)
    db.commit()
    assert client_as(user).post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id)).status_code == 400


def test_chi_co_quyen_doc_thi_khong_ghi_duoc(w, db, client_as, cap_quyen):
    user = _user(db, _emp(db, "RD757", w.company, w.dept_a.id), "rd757@dego.vn")
    cap_quyen(user.id, "work_schedule", scope="all", read=True)
    db.commit()
    client = client_as(user)
    assert client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id)).status_code == 403
    assert client.patch(f"{URL}/1", json={"note": "x"}).status_code == 403
    assert client.delete(f"{URL}/1").status_code == 403


def test_dong_nhan_su_hanh_dong_khong_co_khoa_rieng_thi_khong_ke_thua(w, db, client_as, cap_quyen):
    """Chỉ có `work_schedule_personal.create` thì tạo được nhưng KHÔNG sửa / xóa được (khóa theo từng hành động)."""
    user = _user(db, _emp(db, "CR757", w.company, w.dept_a.id), "cr757@dego.vn")
    cap_quyen(user.id, "work_schedule", scope="all", read=True)
    cap_quyen(user.id, "work_schedule_personal", scope="dept", create=True)
    db.commit()
    client = client_as(user)
    created = client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id))
    assert created.status_code == 201
    row_id = created.json()["data"]["id"]
    assert client.patch(f"{URL}/{row_id}", json={"note": "x"}).status_code == 403
    assert client.delete(f"{URL}/{row_id}").status_code == 403


def test_duong_nhan_su_giu_nguyen(w, db, client_as):
    """Nhân sự (khóa `work_schedule.*`) vẫn gán được mọi cấp, kể cả cho người ở phòng khác và cho chính họ."""
    client = client_as(w.hr_user)
    hr_emp = w.hr_user.employee_id
    assert client.post(URL, json=_body(L.SYSTEM, 0, w.sched.id)).status_code == 201
    assert client.post(URL, json=_body(L.COMPANY, w.company.id, w.sched.id)).status_code == 201
    assert client.post(URL, json=_body(L.DEPARTMENT, w.dept_a.id, w.sched.id)).status_code == 201
    row = client.post(URL, json=_body(L.EMPLOYEE, w.b1.id, w.sched.id))
    own = client.post(URL, json=_body(L.EMPLOYEE, hr_emp, w.sched.id))
    assert row.status_code == own.status_code == 201
    assert client.patch(f"{URL}/{row.json()['data']['id']}", json={"note": "ghi chú"}).status_code == 200
    assert client.delete(f"{URL}/{row.json()['data']['id']}").status_code == 200
    #  Mẫu lịch: vẫn thuộc Nhân sự.
    assert client.post("/api/work-schedules",
                       json={"name": "Mẫu HR", "note": "", "is_active": True, "days": _days()}).status_code == 201
    #  Người ngoài phạm vi `employee` vẫn nhận câu 400 cũ ở đường Nhân sự có phạm vi hẹp.
    assert client.post(URL, json=_body(L.EMPLOYEE, 9_999_999, w.sched.id)).status_code == 400


# ── Khai báo khóa: SCOPE_FIELDS, seed ─────────────────────────────────────────────────

def test_khoa_moi_khai_cot_cua_ho_so_nhan_su_va_seed_dung_vai_tro():
    from app.core.permissions import ENTITIES, ENTITY_LABELS
    from app.seed import STD_ROLES, _PUR_MANAGER_PERMS, _SYS_ENTITIES

    assert SCOPE_FIELDS["work_schedule_personal"] == {"company": "company_id", "dept_id": "department_id", "self": "id"}
    from app.core.scoping import INCLUDE_DEPT_SAME_COMPANY
    assert "work_schedule_personal" in INCLUDE_DEPT_SAME_COMPANY
    assert "work_schedule_personal" in ENTITIES and ENTITY_LABELS["work_schedule_personal"]
    assert "work_schedule_personal" in _SYS_ENTITIES and "work_schedule_personal" not in _PUR_MANAGER_PERMS
    assert STD_ROLES["dept_head"]["perms"]["work_schedule_personal"] == (["read", "create", "write", "delete"], "dept")
    assert STD_ROLES["dept_head"]["perms"]["leave_balance"] == (["read"], "dept")
    holders = [code for code, info in STD_ROLES.items() if "work_schedule_personal" in info["perms"]]
    assert holders == ["dept_head"]


# ── Q2: quỹ phép bậc phòng ────────────────────────────────────────────────────────────

@pytest.fixture
def balances(db, w, cap_quyen):
    annual = LeaveType(code="ANNUAL", name="Phép năm", is_paid=True, counts_balance=True,
                       annual_quota_days=12, is_active=True)
    db.add(annual)
    db.flush()
    for emp in (w.mgr, w.a1, w.a2, w.b1, w.nodept):
        db.add(LeaveBalance(employee_id=emp.id, year=YEAR, leave_type_id=annual.id, company_id=emp.company_id,
                            allocated_days=12))
    other_company = Company(name="Cty khác 757", code="CK757", is_active=True)
    db.add(other_company)
    db.flush()
    far_dept = Department(code="DK757", name="Phòng xa", company_id=other_company.id, is_active=True)
    db.add(far_dept)
    db.flush()
    far = _emp(db, "FAR757", other_company, far_dept.id)
    db.add(LeaveBalance(employee_id=far.id, year=YEAR, leave_type_id=annual.id, company_id=other_company.id,
                        allocated_days=12))
    cap_quyen(w.mgr_user.id, "leave_balance", scope="dept", read=True)
    db.commit()
    return w


def _codes(res, db):
    ids = [i["employee_id"] for i in res.json()["data"]["items"]]
    return sorted(db.get(Employee, i).code for i in ids)


def test_quy_phep_bac_phong_chi_thay_nguoi_phong_minh(balances, db, client_as):
    res = client_as(balances.mgr_user).get("/api/leave-balances", params={"limit": 100})
    assert res.status_code == 200
    assert _codes(res, db) == ["A1757", "A2757", "TP757"]   # không có B1, không người chưa gắn phòng, không công ty khác


def test_quy_phep_bac_phong_gom_ca_phong_kiem_nhiem(balances, db, client_as):
    db.add(EmployeeConcurrent(employee_id=balances.mgr.id, kind=1, company_id=balances.company.id,
                              department_id=balances.dept_b.id, from_date=LONG_AGO, to_date=None, counts_scope=True))
    db.commit()
    perm_cache_clear(balances.mgr_user.id)
    res = client_as(balances.mgr_user).get("/api/leave-balances", params={"limit": 100})
    assert _codes(res, db) == ["A1757", "A2757", "B1757", "TP757"]


def test_quy_phep_bac_phong_nguoi_chua_gan_phong_khong_thay_gi(balances, db, client_as, cap_quyen):
    user = _user(db, balances.nodept, "nd757@dego.vn")
    cap_quyen(user.id, "leave_balance", scope="dept", read=True)
    db.commit()
    res = client_as(user).get("/api/leave-balances", params={"limit": 100})
    assert res.status_code == 200 and res.json()["data"]["total"] == 0


def _ask(db, user_id, **args):
    return EMPLOYEE_LEAVE_SUMMARY_SPEC.handler(ToolContext(db, db.get(User, user_id)), {"year": YEAR, **args})


def test_cong_cu_tro_ly_ke_thua_pham_vi_quy_phep_bac_phong(balances, db, cap_quyen):
    """Hồ sơ xem TẤT CẢ nhưng quỹ phép bậc phòng: chính phạm vi quỹ phép (không phải hồ sơ) cắt người phòng khác."""
    cap_quyen(balances.mgr_user.id, "employee", scope="all", read=True)
    db.commit()
    perm_cache_clear(balances.mgr_user.id)
    mine = _ask(db, balances.mgr_user.id, employee="A1757")
    assert [e["code"] for e in mine["employees"]] == ["A1757"] and mine["employees"][0]["balances"]
    assert _ask(db, balances.mgr_user.id, employee="B1757")["employees"] == []
    by_dept = _ask(db, balances.mgr_user.id, department=str(balances.dept_b.id))
    assert by_dept["employees"] == []
    listed = _ask(db, balances.mgr_user.id, department=str(balances.dept_a.id))
    assert sorted(e["code"] for e in listed["employees"]) == ["A1757", "A2757", "TP757"]


def test_so_truy_van_cong_cu_khong_doi_khi_them_nguoi_o_bac_phong(balances, db):
    ctx = ToolContext(db, db.get(User, balances.mgr_user.id))
    counts = []
    for n in (2, 8):
        for i in range(n):
            emp = _emp(db, f"X{n}-{i}", balances.company, balances.dept_a.id)
            db.add(LeaveBalance(employee_id=emp.id, year=YEAR, leave_type_id=db.query(LeaveType).first().id,
                                company_id=emp.company_id, allocated_days=12))
        db.commit()
        args = {"department": str(balances.dept_a.id), "year": YEAR, "limit": 50}
        EMPLOYEE_LEAVE_SUMMARY_SPEC.handler(ctx, args)   # nạp sẵn hồ sơ quyền
        out, sql = count_queries(db, lambda a=args: EMPLOYEE_LEAVE_SUMMARY_SPEC.handler(ctx, a))
        assert out["total"] >= n
        counts.append(len(sql))
    assert counts[0] == counts[1], counts


def test_ma_tran_va_bao_cao_quy_phep_ke_thua_bac_phong(balances, db, client_as):
    client = client_as(balances.mgr_user)
    matrix = client.get("/api/leave-balances/matrix", params={"year": YEAR})
    assert matrix.status_code == 200
    names = str(matrix.json()["data"])
    assert "A1757" in names or "Người A1757" in names
    assert "B1757" not in names and "Người B1757" not in names and "FAR757" not in names


def test_bao_cao_quy_phep_ke_thua_bac_phong(balances, db):
    """Số tổng của báo cáo Quỹ phép chỉ cộng quỹ người phòng A (3 người × 12 ngày), không phải cả công ty."""
    from app.core.auth import get_perm_profile

    period = parse_period({"preset": "custom", "date_from": "2026-01-01", "date_to": "2026-12-31", "compare": "none"})
    user = db.get(User, balances.mgr_user.id)
    out = balance_report_service.build_summary(db, user, get_perm_profile(db, user), period, None)
    assert out["totals"]["current"]["granted"] == 36


def test_quy_phep_bac_phong_rang_cong_ty_hien_tai_cua_nhan_su_khong_rang_anh_chup(balances, db, client_as):
    """Cột `LeaveBalance.company_id` chỉ là ảnh chụp lúc cấp quỹ (có thể 0 hoặc công ty cũ). Bậc phòng phải ràng công ty
    HIỆN TẠI của nhân sự: dòng quỹ `company_id = 0` / công ty cũ của người đang ở phòng + công ty mình vẫn hiện; người có
    CÙNG id phòng nhưng thuộc công ty khác (id phòng dùng chung nhiều công ty) thì không."""
    other_company = db.query(Company).filter(Company.code == "CK757").one()
    rows = {r.employee_id: r for r in db.query(LeaveBalance).all()}
    rows[balances.a1.id].company_id = 0                       # ảnh chụp trống
    rows[balances.a2.id].company_id = other_company.id        # ảnh chụp công ty cũ
    leave_type_id = rows[balances.a1.id].leave_type_id
    #  Cùng id phòng A nhưng hồ sơ đang ở công ty khác, quỹ cũng ghi công ty đó.
    shared = _emp(db, "SHARED757", other_company, balances.dept_a.id)
    db.add(LeaveBalance(employee_id=shared.id, year=YEAR, leave_type_id=leave_type_id, company_id=other_company.id,
                        allocated_days=12))
    #  Và một dòng ghi công ty của MÌNH nhưng hồ sơ đã chuyển sang công ty khác: không hiện.
    moved = _emp(db, "MOVED757", other_company, balances.dept_a.id)
    db.add(LeaveBalance(employee_id=moved.id, year=YEAR, leave_type_id=leave_type_id,
                        company_id=balances.company.id, allocated_days=12))
    db.commit()
    perm_cache_clear(balances.mgr_user.id)

    res = client_as(balances.mgr_user).get("/api/leave-balances", params={"limit": 100})
    assert _codes(res, db) == ["A1757", "A2757", "TP757"]

    #  Công cụ trợ lý cùng luật (hồ sơ xem tất cả, chỉ phạm vi quỹ phép cắt).
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import UserRole
    role = Role(code="VT_TEST_EMP757", name="Hồ sơ tất cả 757")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity="employee", scope="all", can_read=True))
    db.add(UserRole(user_id=balances.mgr_user.id, role_id=role.id))
    db.commit()
    perm_cache_clear(balances.mgr_user.id)
    listed = _ask(db, balances.mgr_user.id, department=str(balances.dept_a.id))
    assert sorted(e["code"] for e in listed["employees"]) == ["A1757", "A2757", "TP757"]
    assert all(e["balances"] for e in listed["employees"])


# ── Phòng DÙNG CHUNG nhiều công ty (tab_department.company_id = 0) ─────────────────────

@pytest.fixture
def shared(db, w, cap_quyen):
    """Một phòng dùng chung, hai công ty cùng có người ở đó; quỹ phép ghi ảnh chụp công ty = 0 hoặc công ty cũ."""
    from app.modules.user.model import UserScope

    other = Company(name="Cty B 757", code="CB757", is_active=True)
    db.add(other)
    db.flush()
    dept = Department(code="SH757", name="Phòng dùng chung", company_id=0, is_active=True)
    db.add(dept)
    db.flush()
    annual = LeaveType(code="ANNUAL", name="Phép năm", is_paid=True, counts_balance=True,
                       annual_quota_days=12, is_active=True)
    db.add(annual)
    db.flush()
    s = World()
    s.dept, s.other, s.w = dept, other, w
    s.boss = _emp(db, "BOSS757", w.company, dept.id)            # người xem: phòng dùng chung ở công ty A
    s.in_a = _emp(db, "INA757", w.company, dept.id)             # quỹ ghi công ty 0
    s.in_a_old = _emp(db, "INAOLD757", w.company, dept.id)      # quỹ ghi công ty cũ (B)
    s.in_b = _emp(db, "INB757", other, dept.id)                 # cùng id phòng, công ty B
    s.boss_user = _user(db, s.boss, "boss757@dego.vn")
    for emp, snapshot in ((s.boss, w.company.id), (s.in_a, 0), (s.in_a_old, other.id), (s.in_b, 0)):
        db.add(LeaveBalance(employee_id=emp.id, year=YEAR, leave_type_id=annual.id, company_id=snapshot,
                            allocated_days=12))
    #  Người xem khác: phòng của họ KHÔNG phải phòng dùng chung, chỉ có ô "Phòng ban được xem" = phòng dùng chung.
    s.viewer = _emp(db, "VIEW757", w.company, w.dept_a.id)
    s.viewer_user = _user(db, s.viewer, "view757@dego.vn")
    role_balance = cap_quyen(s.viewer_user.id, "leave_balance", scope="own", read=True)
    role_personal = cap_quyen(s.viewer_user.id, "work_schedule_personal", scope="own", create=True)
    cap_quyen(s.viewer_user.id, "work_schedule", scope="all", read=True)
    for role in (role_balance, role_personal):
        db.add(UserScope(user_id=s.viewer_user.id, role_id=role.id, dim="department", value=str(dept.id),
                         is_exclude=False))
    cap_quyen(s.boss_user.id, "leave_balance", scope="dept", read=True)
    db.commit()
    perm_cache_clear(s.viewer_user.id)
    perm_cache_clear(s.boss_user.id)
    return s


def test_quy_phep_bac_phong_o_phong_dung_chung_voi_dong_quy_ghi_cong_ty_0_hoac_cu(shared, db, client_as):
    res = client_as(shared.boss_user).get("/api/leave-balances", params={"limit": 100})
    #  Người cùng phòng + cùng công ty hiện: hiện dù quỹ ghi công ty 0 / công ty cũ; người công ty B cùng id phòng: không.
    assert _codes(res, db) == ["BOSS757", "INA757", "INAOLD757"]


def test_o_phong_ban_duoc_xem_khong_mo_xuyen_cong_ty_quy_phep(shared, db, client_as):
    res = client_as(shared.viewer_user).get("/api/leave-balances", params={"limit": 100})
    assert _codes(res, db) == ["BOSS757", "INA757", "INAOLD757"]   # có phòng dùng chung của công ty mình, không có INB757


def test_o_phong_ban_duoc_xem_khong_mo_xuyen_cong_ty_lich_rieng(shared, db, client_as):
    client = client_as(shared.viewer_user)
    ok = client.post(URL, json=_body(L.EMPLOYEE, shared.in_a.id, shared.w.sched.id))
    cross = client.post(URL, json=_body(L.EMPLOYEE, shared.in_b.id, shared.w.sched.id))
    assert ok.status_code == 201, ok.text
    assert cross.status_code == 400 and cross.json()["error"]["message"] == NOT_FOUND_TARGET


def test_bac_dept_proc_cua_quy_phep_khong_mo_xuyen_cong_ty(shared, db, client_as, cap_quyen):
    user = _user(db, _emp(db, "PROC757", shared.w.company, shared.dept.id), "proc757@dego.vn")
    cap_quyen(user.id, "leave_balance", scope="dept_proc", read=True)
    db.commit()
    res = client_as(user).get("/api/leave-balances", params={"limit": 100})
    assert _codes(res, db) == ["BOSS757", "INA757", "INAOLD757"]


# ── N2: chỉ sửa / xóa dòng do chính mình gán; ngày hiệu lực từ hôm nay; created_by ───────────

NOT_CREATOR = "Lịch này do Nhân sự hoặc người khác gán, bạn chỉ sửa được lịch do chính mình gán"
PAST_DATE = "Ngày hiệu lực phải từ hôm nay trở đi"


def test_khong_sua_xoa_dong_do_nhan_su_hoac_truong_phong_khac_gan(w, db, client_as, cap_quyen):
    hr_row = client_as(w.hr_user).post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id)).json()["data"]["id"]
    other_mgr = _user(db, _emp(db, "TP2757", w.company, w.dept_a.id), "tp2757@dego.vn")
    cap_quyen(other_mgr.id, "work_schedule", scope="all", read=True)
    cap_quyen(other_mgr.id, "work_schedule_personal", scope="dept", create=True, write=True, delete=True)
    cap_quyen(other_mgr.id, "employee", scope="dept", read=True)
    db.commit()
    other_row = client_as(other_mgr).post(URL, json=_body(L.EMPLOYEE, w.a2.id, w.sched.id)).json()["data"]["id"]

    client = client_as(w.mgr_user)
    for row_id in (hr_row, other_row):
        patch = client.patch(f"{URL}/{row_id}", json={"note": "x"})
        delete = client.delete(f"{URL}/{row_id}")
        assert (patch.status_code, delete.status_code) == (403, 403), row_id
        assert patch.json()["error"]["message"] == delete.json()["error"]["message"] == NOT_CREATOR
    db.expire_all()
    assert db.get(WorkScheduleAssignment, hr_row).note == "" and db.get(WorkScheduleAssignment, other_row) is not None
    #  Nhân sự (đường cũ) vẫn sửa / xóa được dòng của Trưởng phòng.
    hr_client = client_as(w.hr_user)
    assert hr_client.patch(f"{URL}/{other_row}", json={"note": "HR sửa"}).status_code == 200
    assert hr_client.delete(f"{URL}/{other_row}").status_code == 200


def test_tao_dong_moi_cat_doi_dong_khong_thoi_han_cua_nhan_su_va_xoa_thi_mo_lai(w, db, client_as):
    start = _today() + timedelta(days=10)
    end = _today() + timedelta(days=20)
    hr_row = client_as(w.hr_user).post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id,
                                                       start=_today().isoformat())).json()["data"]["id"]
    client = client_as(w.mgr_user)
    temp = client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched2.id, start=start.isoformat(), end=end.isoformat()))
    assert temp.status_code == 201, temp.text
    rows = _rows(db, L.EMPLOYEE, w.a1.id)
    assert [(r.effective_from, r.effective_to) for r in rows] == [
        (_today(), start - timedelta(days=1)), (start, end), (end + timedelta(days=1), None)]
    assert rows[2].schedule_id == w.sched.id   # nửa sau nối lại lịch cũ của Nhân sự
    #  Xóa dòng tạm do chính mình gán: dòng Nhân sự mở lại "không thời hạn", dòng nối lại biến mất.
    assert client.delete(f"{URL}/{temp.json()['data']['id']}").status_code == 200
    db.expire_all()
    rows = _rows(db, L.EMPLOYEE, w.a1.id)
    assert [(r.id, r.effective_to) for r in rows] == [(hr_row, None)]


def test_ngay_hieu_luc_phai_tu_hom_nay_tren_duong_truong_phong(w, db, client_as):
    client = client_as(w.mgr_user)
    yesterday = (_today() - timedelta(days=1)).isoformat()
    past = client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id, start=yesterday))
    assert past.status_code == 422 and past.json()["error"]["message"] == PAST_DATE
    assert _rows(db, L.EMPLOYEE, w.a1.id) == []
    created = client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id, start=_today().isoformat()))
    assert created.status_code == 201
    row_id = created.json()["data"]["id"]
    #  Sửa mà ngày đổi về quá khứ: 422; đổi sang tương lai, hoặc không đổi ngày: được.
    assert client.patch(f"{URL}/{row_id}", json={"effective_from": yesterday}).status_code == 422
    assert client.patch(f"{URL}/{row_id}", json={"note": "giữ ngày"}).status_code == 200
    assert client.patch(f"{URL}/{row_id}", json={"effective_from": _today().isoformat()}).status_code == 200
    later = (_today() + timedelta(days=3)).isoformat()
    assert client.patch(f"{URL}/{row_id}", json={"effective_from": later}).status_code == 200
    #  `effective_to` nhỏ hơn `effective_from` vẫn là lỗi cũ.
    assert client.patch(f"{URL}/{row_id}", json={"effective_to": _today().isoformat()}).status_code in (400, 422)
    #  Nhân sự (đường cũ) vẫn gán lùi ngày được.
    assert client_as(w.hr_user).post(URL, json=_body(L.EMPLOYEE, w.a2.id, w.sched.id, start="2026-01-01")).status_code == 201


def test_dong_gan_tra_ve_created_by_de_giao_dien_an_nut(w, db, client_as):
    hr_row = client_as(w.hr_user).post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id))
    assert hr_row.json()["data"]["created_by"] == w.hr_user.id
    client = client_as(w.mgr_user)   # `client_as` thay người dùng của MỌI client, nên dựng sau khi HR xong việc
    created = client.post(URL, json=_body(L.EMPLOYEE, w.a2.id, w.sched.id))
    assert created.json()["data"]["created_by"] == w.mgr_user.id
    patched = client.patch(f"{URL}/{created.json()['data']['id']}", json={"note": "x"})
    assert patched.json()["data"]["created_by"] == w.mgr_user.id
    items = client.get(URL, params={"target_level": int(L.EMPLOYEE)}).json()["data"]["items"]
    assert {i["target_id"]: i["created_by"] for i in items} == {w.a1.id: w.hr_user.id, w.a2.id: w.mgr_user.id}
    one = client.get(f"{URL}/{created.json()['data']['id']}").json()["data"]
    assert one["created_by"] == w.mgr_user.id
    assert one["replaces_previous"] is False and hr_row.json()["data"]["replaces_previous"] is False


def test_co_replaces_previous_cho_dong_da_thay_lich_va_so_truy_van_co_dinh(w, db, client_as):
    start = (_today() + timedelta(days=10)).isoformat()
    client_as(w.hr_user).post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id))
    client = client_as(w.mgr_user)
    new = client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched2.id, start=start))
    assert new.json()["data"]["replaces_previous"] is True
    items = client.get(URL, params={"target_level": int(L.EMPLOYEE), "target_id": w.a1.id}).json()["data"]["items"]
    assert {i["id"]: i["replaces_previous"] for i in items}[new.json()["data"]["id"]] is True
    assert [i["replaces_previous"] for i in items].count(True) == 1
    counts = []
    for n in (2, 8):
        for i in range(n):
            assign(db, L.EMPLOYEE, w.a2.id if i % 2 else w.a1.id, w.sched.id, date(2020 + i + n, 1, 1), date(2020 + i + n, 1, 5))
        db.commit()
        client.get(URL, params={"page_size": 100})   # nạp sẵn hồ sơ quyền
        res, sql = count_queries(db, lambda: client.get(URL, params={"page_size": 100}))
        assert len(res.json()["data"]["items"]) >= n
        counts.append(len(sql))
    assert counts[0] == counts[1], counts


# ── Kết thúc dòng thay lịch đã bắt đầu: lịch cũ của Nhân sự tự nối lại, dời theo ngày kết thúc ────

def _replacing_pair(db, w, hr_schedule, mgr_schedule):
    """Dòng của Nhân sự (đã bị đóng) + dòng thay lịch của Trưởng phòng ĐÃ BẮT ĐẦU, nối với nhau như lúc tạo thật."""
    today = _today()
    hr_row = assign(db, L.EMPLOYEE, w.a1.id, hr_schedule.id, today - timedelta(days=30), today - timedelta(days=4))
    hr_row.created_by = w.hr_user.id
    mgr_row = assign(db, L.EMPLOYEE, w.a1.id, mgr_schedule.id, today - timedelta(days=3))
    mgr_row.created_by = w.mgr_user.id
    db.flush()
    hr_row.linked_assignment_id = mgr_row.id
    db.commit()
    return hr_row, mgr_row


def _shape(db, w):
    """`[(từ, đến, mẫu lịch, người gán)]` của nhân sự A1, theo thứ tự thời gian — kiểm liền mạch, không chồng, không trùng."""
    db.expire_all()
    rows = _rows(db, L.EMPLOYEE, w.a1.id)
    for before, after in zip(rows, rows[1:]):
        assert before.effective_to is not None and after.effective_from == before.effective_to + timedelta(days=1), rows
    return [(r.effective_from, r.effective_to, r.schedule_id, r.created_by) for r in rows]


@pytest.mark.parametrize("who", ["mgr_user", "hr_user"])
def test_ket_thuc_dong_thay_lich_da_bat_dau_thi_lich_cu_tu_noi_lai_va_doi_ngay_theo(w, db, client_as, who):
    sat_full = make_schedule(db, "Lịch cả T7", [FULL] * 6 + [OFF])
    db.commit()
    hr_row, mgr_row = _replacing_pair(db, w, sat_full, w.sched)   # lịch cũ 6 ngày công, lịch thay (T2–T6) 5 ngày công
    today = _today()
    client = client_as(getattr(w, who))
    url = f"{URL}/{mgr_row.id}"
    monday, saturday = _next_week()
    end = monday + timedelta(days=6)                   # hết Chủ nhật tuần sau
    assert client.patch(url, json={"effective_to": end.isoformat()}).status_code == 200
    shape = _shape(db, w)
    assert shape[2] == (end + timedelta(days=1), None, sat_full.id, w.hr_user.id)   # nối lại, GIỮ người gán gốc
    #  Hai bên mốc: trước mốc theo lịch thay (5), sau mốc theo lịch cũ nối lại (6).
    assert workday_service.count_leave_days(db, monday, saturday, employee=w.a1) == 5.0
    assert workday_service.count_leave_days(db, monday + timedelta(days=7), saturday + timedelta(days=7),
                                            employee=w.a1) == 6.0
    #  Đổi ngày kết thúc lần 1: lùi xa hơn một tuần; lần 2: rút ngắn về hôm qua. Không hở, không chồng, không bản sao dư.
    assert client.patch(url, json={"effective_to": (end + timedelta(days=7)).isoformat()}).status_code == 200
    shape = _shape(db, w)
    assert len(shape) == 3 and shape[2][0] == end + timedelta(days=8)
    assert workday_service.count_leave_days(db, monday + timedelta(days=7), saturday + timedelta(days=7),
                                            employee=w.a1) == 5.0
    yesterday = today - timedelta(days=1)
    assert client.patch(url, json={"effective_to": yesterday.isoformat()}).status_code == 200
    shape = _shape(db, w)
    assert len(shape) == 3 and shape[1][1] == yesterday and shape[2][0] == today
    assert workday_service.count_leave_days(db, monday, saturday, employee=w.a1) == 6.0
    #  Mở lại không thời hạn: dòng nối lại hết chỗ, bị xóa; rồi kết thúc lần nữa thì tạo lại đúng một bản.
    assert client.patch(url, json={"effective_to": None}).status_code == 200
    assert len(_shape(db, w)) == 2
    assert client.patch(url, json={"effective_to": yesterday.isoformat()}).status_code == 200
    shape = _shape(db, w)
    assert len(shape) == 3 and shape[2] == (today, None, sat_full.id, w.hr_user.id)
    #  Đích / ngày bắt đầu vẫn khóa ở đường Trưởng phòng (400); Nhân sự được đổi như cũ.
    if who == "mgr_user":
        assert client.patch(url, json={"target_id": w.a2.id}).status_code in (400, 403)


def test_dong_thay_lich_da_bat_dau_ket_thuc_thieu_hon_hom_qua_van_bi_chan(w, db, client_as):
    _, mgr_row = _replacing_pair(db, w, w.sched2, w.sched)
    res = client_as(w.mgr_user).patch(f"{URL}/{mgr_row.id}",
                                      json={"effective_to": (_today() - timedelta(days=2)).isoformat()})
    assert res.status_code == 422
    assert len(_shape(db, w)) == 2


def test_keo_dai_ngay_ket_thuc_dong_thay_lich_chua_bat_dau_roi_xoa_thi_ve_nhu_cu(w, db, client_as):
    start, end = _today() + timedelta(days=10), _today() + timedelta(days=20)
    client_as(w.hr_user).post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id))
    client = client_as(w.mgr_user)
    new_id = client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched2.id, start=start.isoformat(),
                                         end=end.isoformat())).json()["data"]["id"]
    #  Dòng nối lại đang mở không thời hạn nên kéo dài thoải mái; xóa dòng thay lịch thì mọi thứ về như cũ.
    assert client.patch(f"{URL}/{new_id}", json={"effective_to": (end + timedelta(days=30)).isoformat()}).status_code == 200
    assert len(_shape(db, w)) == 3
    assert client.delete(f"{URL}/{new_id}").status_code == 200
    assert [(r[0], r[1]) for r in _shape(db, w)] == [(_today(), None)]


# ── Lượt 3: dòng đã bắt đầu, bản sao nối lại giữ người gán, dòng đã thay lịch, ô chọn đối tượng ─────

STARTED_EDIT = "Lịch đã bắt đầu, chỉ đặt được ngày kết thúc"
STARTED_DELETE = "Lịch đã bắt đầu, không xóa được — hãy đặt ngày kết thúc"
LINKED = "Lịch này đã thay lịch trước đó, muốn đổi hãy xóa rồi tạo lại"


def _started_row_of_manager(db, w, days_ago=5):
    row = assign(db, L.EMPLOYEE, w.a1.id, w.sched.id, _today() - timedelta(days=days_ago))
    row.created_by = w.mgr_user.id
    db.commit()
    return row


def test_dong_da_bat_dau_chi_dat_duoc_ngay_ket_thuc(w, db, client_as):
    row = _started_row_of_manager(db, w)
    client = client_as(w.mgr_user)
    url = f"{URL}/{row.id}"
    for patch in ({"schedule_id": w.sched2.id}, {"target_id": w.a2.id},
                  {"effective_from": (_today() + timedelta(days=1)).isoformat()},
                  {"target_level": int(L.DEPARTMENT), "target_id": w.dept_a.id}):
        res = client.patch(url, json=patch)
        assert res.status_code == 403 and (res.json()["error"]["message"] == STARTED_EDIT
                                                 or "Bạn chỉ được" in res.json()["error"]["message"]), patch
    #  Ngày kết thúc phải từ hôm qua trở đi.
    assert client.patch(url, json={"effective_to": (_today() - timedelta(days=2)).isoformat()}).status_code == 422
    #  Gửi lại đúng giá trị cũ của các ô khóa + ghi chú: được (form hay gửi đủ mọi ô).
    same = {"schedule_id": w.sched.id, "target_id": w.a1.id, "target_level": int(L.EMPLOYEE),
            "effective_from": row.effective_from.isoformat(), "note": "ghi chú"}
    assert client.patch(url, json=same).status_code == 200
    yesterday = (_today() - timedelta(days=1)).isoformat()
    assert client.patch(url, json={"effective_to": yesterday}).status_code == 200
    assert client.patch(url, json={"effective_to": (_today() + timedelta(days=5)).isoformat()}).status_code == 200
    assert client.patch(url, json={"effective_to": None}).status_code == 200
    delete = client.delete(url)
    assert delete.status_code == 403 and delete.json()["error"]["message"] == STARTED_DELETE
    db.expire_all()
    assert db.get(WorkScheduleAssignment, row.id) is not None


def test_dong_bat_dau_hom_nay_van_sua_xoa_nhu_cu(w, db, client_as):
    client = client_as(w.mgr_user)
    row_id = client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id)).json()["data"]["id"]   # bắt đầu hôm nay
    assert client.patch(f"{URL}/{row_id}", json={"schedule_id": w.sched2.id}).status_code == 200
    assert client.delete(f"{URL}/{row_id}").status_code == 200


def test_duong_nhan_su_van_sua_xoa_dong_da_bat_dau(w, db, client_as):
    row = _started_row_of_manager(db, w)
    client = client_as(w.hr_user)
    assert client.patch(f"{URL}/{row.id}", json={"schedule_id": w.sched2.id}).status_code == 200
    assert client.delete(f"{URL}/{row.id}").status_code == 200


def test_ban_sao_noi_lai_giu_nguoi_gan_goc_nen_truong_phong_khong_xoa_duoc(w, db, client_as):
    start, end = _today() + timedelta(days=10), _today() + timedelta(days=20)
    hr_row = client_as(w.hr_user).post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id)).json()["data"]["id"]
    client = client_as(w.mgr_user)
    assert client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched2.id, start=start.isoformat(),
                                       end=end.isoformat())).status_code == 201
    resume = _rows(db, L.EMPLOYEE, w.a1.id)[2]
    assert resume.effective_from == end + timedelta(days=1) and resume.created_by == w.hr_user.id
    assert client.delete(f"{URL}/{resume.id}").status_code == 403
    assert client.patch(f"{URL}/{resume.id}", json={"note": "x"}).status_code == 403
    assert db.get(WorkScheduleAssignment, hr_row).created_by == w.hr_user.id


def test_dong_da_thay_lich_truoc_do_khong_doi_dich_hay_ngay_bat_dau_nhung_xoa_van_mo_lai(w, db, client_as):
    start = _today() + timedelta(days=10)
    hr_row = client_as(w.hr_user).post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched.id,
                                                       start=_today().isoformat())).json()["data"]["id"]
    client = client_as(w.mgr_user)
    new_id = client.post(URL, json=_body(L.EMPLOYEE, w.a1.id, w.sched2.id, start=start.isoformat())).json()["data"]["id"]
    url = f"{URL}/{new_id}"
    for patch in ({"effective_from": (start + timedelta(days=1)).isoformat()}, {"target_id": w.a2.id}):
        res = client.patch(url, json=patch)
        assert res.status_code == 400 and res.json()["error"]["message"] == LINKED, patch
    assert client.patch(url, json={"note": "đổi ghi chú"}).status_code == 200   # trường không gỡ liên kết
    assert client.patch(url, json={"schedule_id": w.sched.id}).status_code == 200
    db.expire_all()
    assert db.get(WorkScheduleAssignment, hr_row).effective_to == start - timedelta(days=1)
    assert client.delete(url).status_code == 200   # chưa bắt đầu → xóa được và mở lại dòng Nhân sự
    db.expire_all()
    assert db.get(WorkScheduleAssignment, hr_row).effective_to is None


def test_o_chon_doi_tuong_duong_truong_phong_chi_nguoi_trong_pham_vi_tru_chinh_minh(w, db, client_as):
    db.add(Employee(code="OFF757", full_name="Người Nghỉ Việc", company_id=w.company.id,
                    department_id=w.dept_a.id, is_active=False))
    db.commit()
    client = client_as(w.mgr_user)
    data = client.get(f"{URL}/tools/assignable-employees").json()["data"]
    assert data["total"] == 2 and [i["code"] for i in data["items"]] == ["A1757", "A2757"]   # không TP757, B1757, ND757, OFF757
    assert data["items"][0] == {"id": w.a1.id, "code": "A1757", "full_name": "Người A1757", "department_name": "Phòng A"}
    #  Tìm không dấu theo họ tên / mã; phân trang.
    assert [i["code"] for i in client.get(f"{URL}/tools/assignable-employees", params={"q": "nguoi a2"})
            .json()["data"]["items"]] == ["A2757"]
    page = client.get(f"{URL}/tools/assignable-employees", params={"page": 2, "page_size": 1}).json()["data"]
    assert page["total"] == 2 and [i["code"] for i in page["items"]] == ["A2757"]


def test_o_chon_doi_tuong_duong_nhan_su_theo_pham_vi_ho_so(w, db, client_as):
    data = client_as(w.hr_user).get(f"{URL}/tools/assignable-employees", params={"page_size": 100}).json()["data"]
    codes = [i["code"] for i in data["items"]]
    assert {"A1757", "A2757", "B1757", "ND757", "TP757", "HR757"} <= set(codes)   # HR chọn được cả chính mình như đường cũ
    assert codes == sorted(codes, key=lambda c: db.query(Employee).filter(Employee.code == c).one().full_name)


def test_o_chon_doi_tuong_thieu_quyen_403_va_ke_thua_o_phong_ban_duoc_xem(w, db, client_as, cap_quyen):
    reader = _user(db, _emp(db, "RDP757", w.company, w.dept_a.id), "rdp757@dego.vn")
    cap_quyen(reader.id, "work_schedule", scope="all", read=True)
    db.commit()
    assert client_as(reader).get(f"{URL}/tools/assignable-employees").status_code == 403


def test_o_chon_doi_tuong_ke_thua_o_phong_ban_duoc_xem_khong_xuyen_cong_ty(shared, db, client_as):
    items = client_as(shared.viewer_user).get(f"{URL}/tools/assignable-employees").json()["data"]["items"]
    assert [i["code"] for i in items] == ["BOSS757", "INA757", "INAOLD757"]   # người phòng dùng chung ở công ty mình


def test_o_chon_doi_tuong_so_truy_van_co_dinh(w, db, client_as):
    client = client_as(w.mgr_user)
    counts = []
    for n in (2, 8):
        for i in range(n):
            _emp(db, f"Q{n}-{i}", w.company, w.dept_a.id)
        db.commit()
        client.get(f"{URL}/tools/assignable-employees")   # nạp sẵn hồ sơ quyền
        res, sql = count_queries(db, lambda: client.get(f"{URL}/tools/assignable-employees", params={"page_size": 100}))
        assert res.json()["data"]["total"] >= n
        counts.append(len(sql))
    assert counts[0] == counts[1], counts
