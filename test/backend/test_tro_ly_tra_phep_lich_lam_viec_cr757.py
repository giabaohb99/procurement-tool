"""duoc-CR-757 — trợ lý tra phép theo lịch làm việc + lịch hiệu lực của phòng ban.

1. `my_leave_summary` thêm `work_schedule` (lịch đang áp hôm nay) và `taken_by_type` (ngày đã nghỉ MỌI loại, năm của
   đơn = năm của ngày bắt đầu như sổ quỹ); năm mặc định theo giờ VN.
2. `employee_leave_summary` (mới): phép của nhân sự khác, gác `leave_balance.read` + phạm vi employee ∩ leave_balance,
   số truy vấn cố định.
3. `GET /api/work-schedules/tools/effective-department`: lịch phòng, nguồn kế thừa, lịch sử gán cấp phòng.
"""
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.vn_time import vn_today
from app.core.work_schedule_codes import WorkScheduleLevel
from app.main import app
from app.modules.assistant import tools as T
from app.modules.assistant.tools.base import ToolContext
from app.modules.assistant.tools.employee_leave_tool import EMPLOYEE_LEAVE_SUMMARY_SPEC, NOT_FOUND
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LR_APPROVED, LR_CANCELLED, LR_DRAFT, LR_PENDING
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine
from app.modules.user.model import User
from lich_lam_viec_factory import assign, count_queries, make_schedule, make_world, week_t2_t6_sat_am

YEAR = 2026
LONG_AGO = date(2020, 1, 1)


def _types(db):
    annual = LeaveType(code="ANNUAL", name="Phép năm", is_paid=True, counts_balance=True,
                       annual_quota_days=12, is_active=True)
    unpaid = LeaveType(code="UNPAID", name="Nghỉ không lương", is_paid=False, counts_balance=False,
                       annual_quota_days=0, is_active=True)
    db.add_all([annual, unpaid])
    db.flush()
    return annual, unpaid


def _request(db, emp_id, code, start, end, status, lines, deleted=False):
    """Đơn chép công ty / phòng từ hồ sơ người nghỉ như đường lập đơn thật (hai cột lọc phạm vi `leave_request`)."""
    emp = db.get(Employee, emp_id)
    req = LeaveRequest(code=code, employee_id=emp_id, company_id=emp.company_id, department_id=emp.department_id,
                       from_date=start, to_date=end, status=status,
                       total_days=sum(d for _, d in lines), leave_type_id=lines[0][0].id, is_deleted=deleted)
    db.add(req)
    db.flush()
    db.add_all([LeaveRequestLine(request_id=req.id, leave_type_id=t.id, days=d, sort_order=i)
                for i, (t, d) in enumerate(lines)])
    db.flush()
    return req


# ── P1: my_leave_summary ─────────────────────────────────────────────────────────────

def test_lich_lam_viec_cua_toi_lay_tu_phong_ban(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="all", read=True)
    sched = make_schedule(db, "Lịch phòng Test", week_t2_t6_sat_am())
    assign(db, WorkScheduleLevel.DEPARTMENT, seed.dept_id, sched.id, LONG_AGO)
    db.commit()

    out = T.run_tool(db, db.get(User, seed.u_req_id), "my_leave_summary", {"year": YEAR})
    ws = out["work_schedule"]
    assert ws["schedule_name"] == "Lịch phòng Test" and ws["is_fallback"] is False
    assert ws["level_label"] == "Phòng ban" and ws["target_name"] == "Phòng Test"
    assert ws["weekly_workdays"] == 5.5 and ws["effective_from"] == "2020-01-01"
    assert [d["weekday_label"] for d in ws["days"]][0] == "Thứ Hai"
    assert ws["days"][5]["day_kind_label"] == "Buổi sáng" and ws["days"][5]["end_time"] == "12:00"
    assert ws["days"][6] == {"weekday_label": "Chủ Nhật", "day_kind_label": "Nghỉ"}
    assert "work_schedule" in out["glossary"] and "taken_by_type" in out["glossary"]


def test_ngay_da_nghi_theo_loai_gom_ca_loai_khong_tru_quy(db, seed, cap_quyen, monkeypatch):
    from app.modules.assistant.tools import leave_tool

    monkeypatch.setattr(leave_tool, "vn_today", lambda: date(YEAR, 6, 15))   # "hôm nay" cố định giữa năm
    cap_quyen(seed.u_req_id, "leave_request", scope="all", read=True)
    annual, unpaid = _types(db)
    me, other = seed.emp_req_id, seed.emp_nstm_id
    _request(db, me, "NP1", date(YEAR, 3, 2), date(YEAR, 3, 4), LR_APPROVED, [(annual, 2), (unpaid, 1)])
    _request(db, me, "NP2", date(YEAR, 4, 6), date(YEAR, 4, 6), LR_PENDING, [(annual, 1.5)])
    _request(db, me, "NP3", date(YEAR, 5, 4), date(YEAR, 5, 8), LR_DRAFT, [(annual, 5)])          # nháp: không tính
    _request(db, me, "NP4", date(YEAR, 6, 1), date(YEAR, 6, 1), LR_CANCELLED, [(annual, 1)])      # hủy: không tính
    _request(db, me, "NP5", date(YEAR, 7, 1), date(YEAR, 7, 1), LR_APPROVED, [(annual, 1)], deleted=True)
    _request(db, me, "NP6", date(YEAR - 1, 12, 30), date(YEAR, 1, 2), LR_APPROVED, [(annual, 3)])  # năm trước
    _request(db, me, "NP7", date(YEAR, 12, 31), date(YEAR + 1, 1, 2), LR_APPROVED, [(unpaid, 2)])  # năm nay, sắp tới
    _request(db, other, "NP8", date(YEAR, 3, 2), date(YEAR, 3, 2), LR_APPROVED, [(annual, 1)])      # người khác
    db.commit()

    out = T.run_tool(db, db.get(User, seed.u_req_id), "my_leave_summary", {"year": YEAR})
    by_type = {t["leave_type_code"]: t for t in out["taken_by_type"]}
    assert by_type["ANNUAL"]["approved_days"] == 2 and by_type["ANNUAL"]["pending_days"] == 1.5
    assert by_type["ANNUAL"]["approved_upcoming_days"] == 0
    #  G1: đơn đã duyệt cho ngày SẮP TỚI không tính vào "đã nghỉ".
    assert by_type["UNPAID"]["approved_days"] == 1 and by_type["UNPAID"]["approved_upcoming_days"] == 2
    assert by_type["UNPAID"]["counts_balance"] is False
    assert out["taken_total_days"] == 3 and out["upcoming_total_days"] == 2 and out["pending_total_days"] == 1.5


def test_nam_mac_dinh_theo_gio_viet_nam(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="all", read=True)
    out = T.run_tool(db, db.get(User, seed.u_req_id), "my_leave_summary", {"year": "rác"})
    assert out["year"] == vn_today().year
    assert out["work_schedule"]["is_fallback"] is True and out["taken_by_type"] == []


# ── P2: employee_leave_summary ───────────────────────────────────────────────────────

def _other_company(db):
    company = Company(name="Cty Khác", code="CK01", is_active=True)
    db.add(company)
    db.flush()
    dept = Department(code="DK01", name="Phòng Khác", company_id=company.id, is_active=True)
    db.add(dept)
    db.flush()
    emp = Employee(code="KHAC01", full_name="Lê Văn Khác", company_id=company.id, department_id=dept.id,
                   is_active=True)
    db.add(emp)
    db.flush()
    return company, emp


def _ask(db, user_id, **args):
    return T.run_tool(db, db.get(User, user_id), "employee_leave_summary", args)


def test_tra_phep_nguoi_khac_can_quyen_quy_phep(db, seed, cap_quyen):
    cap_quyen(seed.u_nstm_id, "leave_request", scope="all", read=True)
    cap_quyen(seed.u_nstm_id, "employee", scope="all", read=True)
    out = _ask(db, seed.u_nstm_id, employee="TESTREQ")
    assert out.get("denied") is True and "employees" not in out


def test_tra_phep_nguoi_khac_khong_lot_cong_ty_khac(db, seed, cap_quyen):
    annual, unpaid = _types(db)
    _, stranger = _other_company(db)
    for emp_id in (seed.emp_req_id, stranger.id):
        db.add(LeaveBalance(employee_id=emp_id, year=YEAR, leave_type_id=annual.id,
                            company_id=db.get(Employee, emp_id).company_id, allocated_days=12, used_days=2))
    _request(db, seed.emp_req_id, "NP1", date(YEAR, 3, 2), date(YEAR, 3, 3), LR_APPROVED, [(annual, 2)])
    _request(db, seed.emp_req_id, "NP2", date(YEAR, 4, 1), date(YEAR, 4, 1), LR_APPROVED, [(unpaid, 1)])
    sched = make_schedule(db, "Lịch phòng Test", week_t2_t6_sat_am())
    assign(db, WorkScheduleLevel.DEPARTMENT, seed.dept_id, sched.id, LONG_AGO)
    db.commit()
    cap_quyen(seed.u_nstm_id, "leave_balance", scope="company", read=True)
    cap_quyen(seed.u_nstm_id, "employee", scope="company", read=True)
    cap_quyen(seed.u_nstm_id, "leave_request", scope="company", read=True)

    out = _ask(db, seed.u_nstm_id, employee="nguoi yc", year=YEAR)   # không dấu vẫn khớp "Người YC"
    assert [e["code"] for e in out["employees"]] == ["TESTREQ"]
    row = out["employees"][0]
    assert row["department_name"] == "Phòng Test"
    assert row["work_schedule"] == {"schedule_name": "Lịch phòng Test", "is_fallback": False,
                                    "level_label": "Phòng ban"}
    assert row["balances"][0]["remaining_days"] == 10 and row["balances"][0]["leave_type_code"] == "ANNUAL"
    assert row["taken_total_days"] == 3
    assert "salary_monthly" not in str(out)

    #  Người công ty khác và người không tồn tại: CÙNG một câu.
    khac = _ask(db, seed.u_nstm_id, employee="KHAC01", year=YEAR)
    khong_co = _ask(db, seed.u_nstm_id, employee="ZZZ-KHONG-CO", year=YEAR)
    assert khac["employees"] == [] == khong_co["employees"]
    assert khac["note"] == khong_co["note"] == NOT_FOUND
    assert "Lê Văn Khác" not in str(_ask(db, seed.u_nstm_id, department="Phòng", year=YEAR))


def test_pham_vi_quy_phep_hep_hon_ho_so_thi_theo_quy_phep(db, seed, cap_quyen):
    """Xem được hồ sơ cả công ty nhưng quỹ phép chỉ của mình → chỉ tra được chính mình."""
    cap_quyen(seed.u_nstm_id, "leave_balance", scope="own", read=True)
    cap_quyen(seed.u_nstm_id, "employee", scope="all", read=True)
    assert [e["code"] for e in _ask(db, seed.u_nstm_id, employee="DEMONV")["employees"]] == ["DEMONV"]
    assert _ask(db, seed.u_nstm_id, employee="TESTREQ")["employees"] == []


def test_truong_phong_pham_vi_phong_chi_thay_phong_minh(db, seed, cap_quyen):
    """Trưởng phòng (quỹ phép + hồ sơ bậc phòng) chỉ tra được người phòng mình — không lộ phòng khác cùng công ty.
    Từ duoc-CR-757 lượt 2 bậc `dept` của quỹ phép tự nó đã đi qua hồ sơ nhân sự, không còn dựa vào giao với `employee`."""
    other_dept = Department(code="DEPT02", name="Phòng Bên Cạnh", company_id=seed.company_id, is_active=True)
    db.add(other_dept)
    db.flush()
    db.add(Employee(code="BENCANH1", full_name="Người Bên Cạnh", company_id=seed.company_id,
                    department_id=other_dept.id, is_active=True))
    db.commit()
    cap_quyen(seed.u_nstm_id, "leave_balance", scope="dept", read=True)
    cap_quyen(seed.u_nstm_id, "employee", scope="dept", read=True)
    assert [e["code"] for e in _ask(db, seed.u_nstm_id, employee="TESTREQ")["employees"]] == ["TESTREQ"]
    assert _ask(db, seed.u_nstm_id, employee="BENCANH1")["employees"] == []


def _stranger_in_my_company(db, seed, unpaid, annual):
    """Người PHÒNG KHÁC cùng công ty, có quỹ + 3 ngày nghỉ không lương đã duyệt."""
    other_dept = Department(code="DEPT03", name="Kế toán", company_id=seed.company_id, is_active=True)
    db.add(other_dept)
    db.flush()
    emp = Employee(code="KETOAN1", full_name="Người Kế Toán", company_id=seed.company_id,
                   department_id=other_dept.id, is_active=True)
    db.add(emp)
    db.flush()
    db.add(LeaveBalance(employee_id=emp.id, year=YEAR, leave_type_id=annual.id, company_id=seed.company_id,
                        allocated_days=12))
    _request(db, emp.id, "NPK1", date(YEAR, 2, 2), date(YEAR, 2, 4), LR_APPROVED, [(unpaid, 3)])
    db.commit()
    return emp


def test_ngay_da_nghi_can_quyen_don_nghi_phep(db, seed, cap_quyen):
    """C1 kịch bản 1: có quỹ phép + hồ sơ tất cả, KHÔNG có leave_request → thấy quỹ, không thấy ngày đã nghỉ."""
    annual, unpaid = _types(db)
    _stranger_in_my_company(db, seed, unpaid, annual)
    cap_quyen(seed.u_nstm_id, "leave_balance", scope="all", read=True)
    cap_quyen(seed.u_nstm_id, "employee", scope="all", read=True)
    out = _ask(db, seed.u_nstm_id, employee="KETOAN1", year=YEAR)
    row = out["employees"][0]
    assert row["balances"] and row["taken_by_type"] == [] and row["taken_total_days"] == 0
    assert "không có quyền xem đơn nghỉ" in out["glossary"]["taken_by_type"]


def test_ngay_da_nghi_theo_pham_vi_don_nghi_khong_theo_danh_ba(db, seed, cap_quyen):
    """C1 kịch bản 2: quỹ phép bậc công ty + đơn / hồ sơ bậc phòng + một vai trò danh bạ xem hồ sơ tất cả. Người phòng
    khác hiện ra (quỹ phép rộng cả công ty), nhưng ngày đã nghỉ của họ đi theo phạm vi ĐƠN NGHỈ (phòng).
    (Trước duoc-CR-757 lượt 2 bậc phòng của quỹ phép cũng rộng cả công ty; nay đã thu về đúng phòng nên bài dùng bậc công ty.)"""
    annual, unpaid = _types(db)
    _stranger_in_my_company(db, seed, unpaid, annual)
    _request(db, seed.emp_req_id, "NPR1", date(YEAR, 3, 2), date(YEAR, 3, 2), LR_APPROVED, [(unpaid, 1)])
    db.commit()
    cap_quyen(seed.u_nstm_id, "leave_balance", scope="company", read=True)
    for entity in ("leave_request", "employee"):
        cap_quyen(seed.u_nstm_id, entity, scope="dept", read=True)
    cap_quyen(seed.u_nstm_id, "employee", scope="all", read=True)   # vai trò danh bạ
    other = _ask(db, seed.u_nstm_id, employee="KETOAN1", year=YEAR)["employees"][0]
    assert other["taken_by_type"] == [] and other["taken_total_days"] == 0
    mine = _ask(db, seed.u_nstm_id, employee="TESTREQ", year=YEAR)["employees"][0]
    assert mine["taken_total_days"] == 1


def test_tra_phong_bang_ten_tu_nhien_va_id_khong_hop_le(db, seed, cap_quyen):
    annual, unpaid = _types(db)
    _stranger_in_my_company(db, seed, unpaid, annual)
    db.add(Employee(code="KHONGPHONG", full_name="Chưa Gắn Phòng", company_id=seed.company_id, department_id=0,
                    is_active=True))
    db.commit()
    cap_quyen(seed.u_nstm_id, "leave_balance", scope="all", read=True)
    cap_quyen(seed.u_nstm_id, "employee", scope="all", read=True)
    for raw in ("phòng Kế toán", "Phòng kế toán", "bộ phận ke toan", "Kế toán"):
        assert [e["code"] for e in _ask(db, seed.u_nstm_id, department=raw)["employees"]] == ["KETOAN1"], raw
    for raw in ("0", "-1", 0):   # số 0 bị coi như bỏ trống → câu nhắc thiếu tham số, không trả ai
        assert _ask(db, seed.u_nstm_id, department=raw).get("employees", []) == [], raw


def test_tra_theo_phong_va_tham_so_rac(db, seed, cap_quyen):
    cap_quyen(seed.u_nstm_id, "leave_balance", scope="all", read=True)
    cap_quyen(seed.u_nstm_id, "employee", scope="all", read=True)
    assert "error" in _ask(db, seed.u_nstm_id)
    out = _ask(db, seed.u_nstm_id, department="phong test", limit=2)
    assert out["total"] == 4 and len(out["employees"]) == 2 and out["has_more"] is True and out["note"]
    assert _ask(db, seed.u_nstm_id, department=str(seed.dept_id), limit="x")["total"] == 4
    assert _ask(db, seed.u_nstm_id, department="Không có phòng này")["employees"] == []
    assert _ask(db, seed.u_nstm_id, employee="x" * 5000, year=99999)["employees"] == []


def _many(db, n, annual, unpaid):
    company, dept, _ = make_world(db, f"N{n}")
    for i in range(n):
        emp = Employee(code=f"E{n}-{i}", full_name=f"Nhân sự {i}", company_id=company.id,
                       department_id=dept.id, is_active=True)
        db.add(emp)
        db.flush()
        db.add(LeaveBalance(employee_id=emp.id, year=YEAR, leave_type_id=annual.id, company_id=company.id,
                            allocated_days=12))
        _request(db, emp.id, f"R{n}-{i}", date(YEAR, 2, 2), date(YEAR, 2, 2), LR_APPROVED, [(unpaid, 1)])
    db.commit()
    return dept


def test_so_truy_van_co_dinh(db, seed, cap_quyen):
    cap_quyen(seed.u_nstm_id, "leave_balance", scope="all", read=True)
    cap_quyen(seed.u_nstm_id, "employee", scope="all", read=True)
    cap_quyen(seed.u_nstm_id, "leave_request", scope="all", read=True)   # nhánh có đọc ngày đã nghỉ
    ctx = ToolContext(db, db.get(User, seed.u_nstm_id))
    annual, unpaid = _types(db)
    counts = []
    for n in (2, 10):
        dept = _many(db, n, annual, unpaid)
        args = {"department": str(dept.id), "year": YEAR, "limit": 50}
        EMPLOYEE_LEAVE_SUMMARY_SPEC.handler(ctx, args)   # nạp sẵn hồ sơ quyền
        out, sql = count_queries(db, lambda a=args: EMPLOYEE_LEAVE_SUMMARY_SPEC.handler(ctx, a))
        assert len(out["employees"]) == n + 1   # + người của make_world
        assert sum(e["taken_total_days"] for e in out["employees"]) == n   # mỗi người 1 ngày không lương tháng 2
        counts.append(len(sql))
    assert counts[0] == counts[1], counts


# ── P3: GET /api/work-schedules/tools/effective-department ──────────────────────────

@pytest.fixture
def api(db, cap_quyen):
    company, dept, emp = make_world(db, "PB1")
    user = User(email="hr757@dego.vn", employee_id=emp.id, is_active=True)
    db.add(user)
    db.commit()
    cap_quyen(user.id, "department", scope="company", read=True)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app, headers={"Authorization": f"Bearer t-{uuid.uuid4().hex}"})
    client.world = (company, dept, emp)
    yield client
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


URL = "/api/work-schedules/tools/effective-department"


def test_phong_co_lich_rieng_cap_phong_ban(api, db):
    company, dept, _ = api.world
    old = make_schedule(db, "Lịch cũ", week_t2_t6_sat_am())
    new = make_schedule(db, "Lịch mới", week_t2_t6_sat_am())
    assign(db, WorkScheduleLevel.COMPANY, company.id, old.id, LONG_AGO)
    assign(db, WorkScheduleLevel.DEPARTMENT, dept.id, old.id, date(2025, 1, 1), date(2025, 12, 31))
    assign(db, WorkScheduleLevel.DEPARTMENT, dept.id, new.id, date(2026, 1, 1))
    db.commit()

    data = api.get(f"{URL}?department_id={dept.id}&on_date=2026-03-02").json()["data"]
    assert (data["schedule_name"], data["level"], data["level_label"]) == ("Lịch mới", 3, "Phòng ban")
    assert data["target_name"] == dept.name and data["is_fallback"] is False
    assert (data["department_id"], data["department_name"], data["company_id"]) == (dept.id, dept.name, company.id)
    assert len(data["days"]) == 7 and data["weekly_workdays"] == 5.5
    assert [a["effective_from"] for a in data["assignments"]] == ["2026-01-01", "2025-01-01"]
    assert data["assignments"][0]["schedule_name"] == "Lịch mới" and data["assignments"][0]["target_level"] == 3


def test_phong_chua_gan_thi_ke_thua_phap_nhan(api, db):
    company, dept, _ = api.world
    sched = make_schedule(db, "Lịch công ty", week_t2_t6_sat_am())
    assign(db, WorkScheduleLevel.COMPANY, company.id, sched.id, LONG_AGO)
    db.commit()
    data = api.get(f"{URL}?department_id={dept.id}").json()["data"]
    assert (data["level"], data["level_label"], data["target_name"]) == (2, "Pháp nhân", company.name)
    assert data["assignments"] == []


def test_chua_gan_gi_thi_mac_dinh_va_loi(api, db):
    company, dept, _ = api.world
    data = api.get(f"{URL}?department_id={dept.id}").json()["data"]
    assert data["is_fallback"] is True and data["level"] == 0 and data["schedule_id"] == 0
    assert api.get(f"{URL}?department_id=999999").status_code == 404
    assert api.get(f"{URL}?department_id={dept.id}&on_date=1900-01-01").status_code == 422
    assert api.get(f"{URL}?department_id=0").status_code == 422

    #  Phòng của pháp nhân khác: ngoài phạm vi `department` (công ty) → 404 như không tồn tại.
    other = Company(name="Cty xa", code="CX9", is_active=True)
    db.add(other)
    db.flush()
    far = Department(code="DX9", name="Phòng xa", company_id=other.id, is_active=True)
    db.add(far)
    db.commit()
    assert api.get(f"{URL}?department_id={far.id}").status_code == 404


def test_thieu_quyen_phong_ban_bi_chan(db, cap_quyen):
    _, dept, emp = make_world(db, "PB2")
    user = User(email="nv757@dego.vn", employee_id=emp.id, is_active=True)
    db.add(user)
    db.commit()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        client = TestClient(app, headers={"Authorization": f"Bearer t-{uuid.uuid4().hex}"})
        assert client.get(f"{URL}?department_id={dept.id}").status_code == 403
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


# ── Khai báo ở cổng MCP / bộ lọc công cụ ─────────────────────────────────────────────

@pytest.mark.parametrize("text", ["nhân viên phòng IT nghỉ bao nhiêu ngày", "phòng IT năm nay ai nghỉ bao nhiêu",
                                  "số ngày nghỉ của anh Nam", "lịch làm việc của tôi thế nào"])
def test_bo_loc_cong_cu_nap_nhom_nghi_phep(text):
    from app.modules.assistant import tool_router

    assert "leave" in tool_router.groups_for(text), text


def test_tinh_vao_ngan_sach_dong_cua_khoa_mcp(db, monkeypatch):
    from types import SimpleNamespace

    from app.core.config import settings
    from app.modules.agent_hub import mcp, mcp_keys, mcp_log

    monkeypatch.setattr(mcp_log, "_redis", lambda: (_ for _ in ()).throw(ConnectionError("không Redis")))
    monkeypatch.setattr(mcp_log, "_mem", {})
    monkeypatch.setattr(settings, "AGENT_MCP_ROW_BUDGET_PER_MIN", 3)
    calls: list = []
    monkeypatch.setattr(mcp, "call_tool", lambda db_, u, scope, name, args: calls.append(name) or
                        {"total": 9, "employees": [{"code": "A"}, {"code": "B"}]})
    assert "employee_leave_summary" in mcp.READ_TOOLS and "employee_leave_summary" in mcp.ROW_BUDGET_TOOLS
    key, user = SimpleNamespace(id=757, scope=mcp_keys.SCOPE_READ), SimpleNamespace(id=5, is_active=True)
    msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": "employee_leave_summary", "arguments": {"department": "Kế toán"}}}
    traces = []
    for _ in range(3):
        t: dict = {}
        mcp.handle(db, user, key, msg, t)
        traces.append(t)
    assert calls == ["employee_leave_summary"] * 2                     # 2 + 2 = 4 ≥ 3 → lượt ba không chạy
    assert traces[2]["reason"] == mcp_log.REASON_ROW_BUDGET
