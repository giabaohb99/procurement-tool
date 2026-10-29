"""duoc-CR-689 — báo cáo B4 «Đối tượng cần chú ý theo luật» (khóa 29): `/api/legal-watch/summary`.

Canh: hàm tuổi nghỉ hưu thuần theo lộ trình Nghị định 135/2020 (từng năm 2021→2035, hai giới, sinh nhật biên),
ba loại đối tượng (nghỉ hưu 12 tháng · đang nghỉ thai sản · nữ nuôi con dưới 12 tháng), đòi quyền nhạy cảm
(403 câu tiếng Việt, không lộ mã quyền), KHÔNG in ngày sinh, phạm vi, 422, xlsx, số truy vấn CỐ ĐỊNH.
"""
import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.scoping import apply_scope
from app.core.subject_match import SUBJECT_EMPLOYEE
from app.core.vn_time import vn_today
from app.main import app
from app.modules.employee import legal_watch_report_service as svc
from app.modules.employee.contact_model import EmployeeFamily
from app.modules.employee.legal_watch_retirement import add_months, end_of_month, retirement_age_months, retirement_date
from app.modules.employee.model import Employee
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine, LeaveRequestPeriod
from app.modules.report_access.model import ReportAccess

NAM, NU = 1, 2
TODAY = vn_today()
SUM = "/api/legal-watch/summary"
QS = {"preset": "custom", "date_from": (TODAY - timedelta(days=30)).isoformat(),
      "date_to": (TODAY + timedelta(days=60)).isoformat(), "compare": "none"}     # as_of = hôm nay
_n = {"v": 0}

#  Tuổi nghỉ hưu (tháng) từng năm theo Nghị định 135/2020.
MALE_MONTHS = {2021: 723, 2022: 726, 2023: 729, 2024: 732, 2025: 735, 2026: 738, 2027: 741}
FEMALE_MONTHS = {2021: 664, 2022: 668, 2023: 672, 2024: 676, 2025: 680, 2026: 684, 2027: 688, 2028: 692,
                 2029: 696, 2030: 700, 2031: 704, 2032: 708, 2033: 712, 2034: 716, 2035: 720}


# ── Hàm thuần: tuổi nghỉ hưu ────────────────────────────────────────────────

@pytest.mark.parametrize("year", range(2021, 2036))
def test_tuoi_nghi_huu_tung_nam_nam_va_nu(year):
    assert retirement_age_months(year, NAM) == MALE_MONTHS.get(year, 744)       # 62 tuổi từ 2028
    assert retirement_age_months(year, NU) == FEMALE_MONTHS[year]               # 60 tuổi năm 2035


def test_tuoi_truoc_lo_trinh_va_sau_tran_va_gioi_tinh_la():
    assert retirement_age_months(2020, NAM) == 720 and retirement_age_months(2020, NU) == 660
    assert retirement_age_months(2050, NAM) == 744 and retirement_age_months(2050, NU) == 720
    assert retirement_age_months(2026, 0) is None and retirement_age_months(2026, 3) is None
    assert retirement_date(date(1980, 1, 1), 0) is None


@pytest.mark.parametrize("gender", [NAM, NU])
@pytest.mark.parametrize("year", range(2021, 2036))
def test_ngay_nghi_huu_roi_dung_nam_nghi_huu(year, gender):
    #  Dựng ngày sinh sao cho người đó đủ tuổi vào 15/06/<year> -> hàm phải trả đúng ngày đó.
    dob = add_months(date(year, 6, 15), -retirement_age_months(year, gender))
    assert retirement_date(dob, gender) == date(year, 6, 30)      # nghỉ hưu vào CUỐI tháng đủ tuổi


@pytest.mark.parametrize("dob, gender, expected", [
    (date(1961, 1, 1), NAM, date(2021, 4, 30)),            # 60 tuổi 3 tháng
    (date(1960, 12, 31), NAM, date(2020, 12, 31)),        # đủ 60 trước 2021: luật cũ
    (date(1961, 12, 31), NAM, date(2022, 6, 30)),         # 2021 không kịp -> 2022: 60 tuổi 6 tháng, ngày 31 lùi về 30
    (date(1964, 2, 29), NAM, date(2025, 5, 31)),          # sinh 29/02
    (date(1966, 1, 1), NU, date(2021, 5, 31)),             # 55 tuổi 4 tháng
    (date(1965, 12, 31), NU, date(2020, 12, 31)),
    (date(1966, 12, 31), NU, date(2022, 8, 31)),
    (date(1970, 1, 1), NU, date(2027, 5, 31)),
    (date(1976, 1, 1), NU, date(2036, 1, 31)),             # quá năm trần: đủ 60 tuổi
    (date(1966, 1, 1), NAM, date(2027, 10, 31)),           # nam sinh 1966: 2026 chưa kịp, 2027 -> 61 tuổi 9 tháng
])
def test_ngay_nghi_huu_moc_bien(dob, gender, expected):
    assert retirement_date(dob, gender) == expected


# ── Báo cáo ────────────────────────────────────────────────────────────────

@pytest.fixture
def client_as(db):
    def make_client(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make_client
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _emp(db, world, tag, **kw) -> Employee:
    base = dict(code=f"L{tag}", full_name=f"Người {tag}", company_id=world.co["B"],
                department_id=world.dept["B.hc"], is_active=True, gender=NU)
    base.update(kw)
    e = Employee(**base)
    db.add(e)
    db.flush()
    return e


def _dob_retiring_in(days: int, gender: int) -> date:
    """Ngày sinh để ngày đủ tuổi nghỉ hưu rơi KHOẢNG `days` ngày kể từ hôm nay (lệch tối đa 150 ngày về phía xa
    hôm nay: lộ trình tăng tuổi làm có những khoảng ngày không ai nghỉ hưu, vd nữ sinh 01-04/1970 nghỉ 05/2027)."""
    step = -1 if days < 0 else 1
    for extra in range(0, 150):
        goal = end_of_month(TODAY + timedelta(days=days + step * extra))
        for year in range(goal.year, goal.year - 3, -1):         # năm nghỉ hưu có thể sớm hơn năm mốc
            dob = add_months(goal, -retirement_age_months(year, gender))
            if abs((retirement_date(dob, gender) - goal).days) <= 3:
                return dob
    raise AssertionError("không dựng được ngày sinh")


def _leave(db, emp, mat, *, status=3, start=-30, end=60, header_type=None, line_type=None, periods=()):
    _n["v"] += 1
    r = LeaveRequest(code=f"NP-T-{_n['v']}", employee_id=emp.id, company_id=emp.company_id,
                     department_id=emp.department_id, leave_type_id=header_type or mat.id, status=status,
                     from_date=TODAY + timedelta(days=start), to_date=TODAY + timedelta(days=end))
    db.add(r)
    db.flush()
    if line_type:
        db.add(LeaveRequestLine(request_id=r.id, leave_type_id=line_type, days=5))
    for a, b in periods:
        db.add(LeaveRequestPeriod(request_id=r.id, from_date=TODAY + timedelta(days=a), to_date=TODAY + timedelta(days=b)))
    db.flush()


def _child(db, emp, days_old, relation=6):
    db.add(EmployeeFamily(employee_id=emp.id, full_name="Bé", relation=relation, date_of_birth=TODAY - timedelta(days=days_old)))


DOBS: dict[str, date] = {}


def _dataset(db, world):
    mat = LeaveType(code="maternity", name="Nghỉ thai sản")
    annual = LeaveType(code="annual", name="Phép năm")
    db.add_all([mat, annual])
    db.flush()
    DOBS["nam_gan"] = _dob_retiring_in(180, NAM)
    DOBS["nu_gan"] = _dob_retiring_in(200, NU)
    _emp(db, world, "namgan", gender=NAM, date_of_birth=DOBS["nam_gan"])
    _emp(db, world, "nugan", gender=NU, date_of_birth=DOBS["nu_gan"])
    _emp(db, world, "namxa", gender=NAM, date_of_birth=_dob_retiring_in(800, NAM))
    _emp(db, world, "nam_hqua", gender=NAM, date_of_birth=_dob_retiring_in(-45, NAM))   # đã qua thời điểm nghỉ hưu -> past_retirement
    _emp(db, world, "khonggt", gender=0, date_of_birth=DOBS["nam_gan"])
    _emp(db, world, "khongdob", gender=NAM)
    _emp(db, world, "nghi", gender=NAM, date_of_birth=DOBS["nam_gan"], status="resigned")
    #  thai sản
    _leave(db, _emp(db, world, "ts1"), mat)                                        # đang nghỉ, về sau 60 ngày + 1
    _leave(db, _emp(db, world, "ts2"), mat, header_type=annual.id, line_type=mat.id)   # loại thai sản ở dòng
    _leave(db, _emp(db, world, "tspending"), mat, status=2)                        # chưa duyệt
    _leave(db, _emp(db, world, "tshet"), mat, start=-90, end=-1)                   # đã hết
    _leave(db, _emp(db, world, "tskhe"), mat, periods=[(-30, -5), (5, 30)])        # hôm nay nằm trong khe
    _leave(db, _emp(db, world, "tsphep"), mat, header_type=annual.id)              # đơn phép năm thường: không phải
    _leave(db, _emp(db, world, "tsnghi", status="resigned"), mat)
    #  con nhỏ
    _child(db, _emp(db, world, "con1"), 100)
    c2 = _emp(db, world, "con2")
    _child(db, c2, 300)
    _child(db, c2, 30, relation=7)                                                 # con nhỏ nhất quyết định mốc
    _child(db, _emp(db, world, "con400"), 400)
    _child(db, _emp(db, world, "connam", gender=NAM), 100)
    _child(db, _emp(db, world, "conme"), 100, relation=3)                          # quan hệ mẹ, không phải con
    db.commit()


def _actor(db, world, client_as, *, sensitive=True, leave=True, scope="all", report=True, key="a1"):
    world.grant(key, "employee", scope, actions=("read", "export"))
    if sensitive:
        world.grant(key, "employee_sensitive", "all", actions=("read",))
    if leave:
        world.grant(key, "leave_request", "all", actions=("read",))
    actor = world.actor(key)
    if report:
        db.add(ReportAccess(report_key=int(ReportKey.LEGAL_WATCH), subject_kind=SUBJECT_EMPLOYEE,
                            subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
        db.commit()
    return actor, client_as(actor.user)


def _get(client, path=SUM, **extra):
    return client.get(path, params={**QS, "department_id": extra.pop("department_id", ""), **extra})


def _codes(client, metric, **kw):
    r = _get(client, SUM + "/rows", metric=metric, **kw)
    assert r.status_code == 200, r.text
    return {x["employee_code"]: x for x in r.json()["data"]["rows"]}


def test_ba_loai_doi_tuong_dem_dung(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    resp = _get(client, department_id=world.dept["B.hc"])
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    cur = data["totals"]["current"]
    assert cur["retire_12m"] == 2 and cur["maternity_now"] == 2 and cur["child_under_12m"] == 2
    assert cur["past_retirement"] == 1
    assert data["meta"]["drilldown_metrics"] == ["retire_12m", "past_retirement", "maternity_now", "child_under_12m"]
    assert data["trend"] == [] and data["totals"]["compare"] is None
    assert cur["people"] == 7
    for dob in DOBS.values():
        assert dob.isoformat() not in resp.text


def test_rows_moc_va_khong_in_ngay_sinh(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    dept = world.dept["B.hc"]
    retire = _codes(client, "retire_12m", department_id=dept)
    assert set(retire) == {"Lnamgan", "Lnugan"}
    assert retire["Lnamgan"]["milestone"] == retirement_date(DOBS["nam_gan"], NAM).isoformat()
    assert retire["Lnugan"]["milestone"] == retirement_date(DOBS["nu_gan"], NU).isoformat()
    mat = _codes(client, "maternity_now", department_id=dept)
    assert set(mat) == {"Lts1", "Lts2"}
    assert mat["Lts1"]["milestone"] == (TODAY + timedelta(days=61)).isoformat()         # ngày đi làm lại
    child = _codes(client, "child_under_12m", department_id=dept)
    assert set(child) == {"Lcon1", "Lcon2"}
    assert child["Lcon1"]["milestone"] == add_months(TODAY - timedelta(days=100), 12).isoformat()
    assert child["Lcon2"]["milestone"] == add_months(TODAY - timedelta(days=30), 12).isoformat()
    body = _get(client, SUM + "/rows", metric="retire_12m", department_id=dept)
    assert "date_of_birth" not in body.text and all(d.isoformat() not in body.text for d in DOBS.values())
    assert [c["key"] for c in body.json()["data"]["columns"]] == ["employee_code", "employee_name", "department", "kind", "milestone"]


def test_xem_theo_loai_va_phong(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    by_kind = _get(client, group_by="kind", department_id=world.dept["B.hc"]).json()["data"]
    assert {g["key"]: g["current"]["people"] for g in by_kind["groups"]} == {
        "retire_12m": 2, "past_retirement": 1, "maternity_now": 2, "child_under_12m": 2}
    assert _get(client, group_by="department").status_code == 200
    grp = _codes(client, "child_under_12m", group_by="kind", group_key="child_under_12m")
    assert set(grp) == {"Lcon1", "Lcon2"}


@pytest.mark.parametrize("suffix", ["", "/export", "/rows"])
def test_thieu_quyen_nhay_cam_403_cau_de_hieu(db, world, client_as, suffix):
    _dataset(db, world)
    _, client = _actor(db, world, client_as, sensitive=False)
    resp = _get(client, SUM + suffix, metric="retire_12m")
    assert resp.status_code == 403
    assert "nhạy cảm" in resp.text and "employee_sensitive" not in resp.text


def test_thieu_quyen_don_nghi_phep_thai_san_chi_con_nhanh_ho_so(db, world, client_as):
    #  CR-689 N3: thai sản đếm cả theo hồ sơ nên không còn ẩn khi thiếu quyền xem đơn; chỉ mất nhánh đơn.
    _dataset(db, world)
    _emp(db, world, "tshs", status="maternity_leave")
    _, client = _actor(db, world, client_as, leave=False)
    data = _get(client, department_id=world.dept["B.hc"]).json()["data"]
    assert data["totals"]["current"]["maternity_now"] == 1
    assert data["meta"]["drilldown_metrics"] == ["retire_12m", "past_retirement", "maternity_now", "child_under_12m"]
    assert set(_codes(client, "maternity_now", department_id=world.dept["B.hc"])) == {"Ltshs"}


def test_thai_san_hop_don_va_ho_so_dem_mot_lan_va_nguoi_khong_don_khong_co_moc(db, world, client_as):
    _dataset(db, world)
    _emp(db, world, "tshs", status="maternity_leave")                       # chỉ hồ sơ, không đơn
    both = _emp(db, world, "tsca", status="maternity_leave")                # hồ sơ + đơn → đếm 1 lần, mốc theo đơn
    _leave(db, both, db.query(LeaveType).filter_by(code="maternity").one())
    _emp(db, world, "tshsnghi", status="resigned")                          # đã nghỉ việc: không tính
    db.commit()
    _, client = _actor(db, world, client_as)
    dept = world.dept["B.hc"]
    assert _get(client, department_id=dept).json()["data"]["totals"]["current"]["maternity_now"] == 4
    mat = _codes(client, "maternity_now", department_id=dept)
    assert set(mat) == {"Lts1", "Lts2", "Ltshs", "Ltsca"}
    assert mat["Ltshs"]["milestone"] is None
    assert mat["Ltsca"]["milestone"] == (TODAY + timedelta(days=61)).isoformat()
    notes = " ".join(_get(client, department_id=dept).json()["data"]["notes"])
    assert "hồ sơ nhân sự" in notes


def test_thai_san_ky_qua_khu_chi_theo_don_va_co_ghi_chu(db, world, client_as):
    _dataset(db, world)
    _emp(db, world, "tshs", status="maternity_leave")
    _, client = _actor(db, world, client_as)
    past = {"preset": "custom", "date_from": (TODAY - timedelta(days=100)).isoformat(),
            "date_to": (TODAY - timedelta(days=10)).isoformat(), "compare": "none"}
    data = client.get(SUM, params={**past, "department_id": world.dept["B.hc"]}).json()["data"]
    #  Mốc 10 ngày trước: ts1/ts2/tshet/tskhe có đơn phủ; tspending không; hồ sơ tshs bị bỏ vì là trạng thái hiện tại.
    assert data["totals"]["current"]["maternity_now"] == 4
    assert any("kỳ đã qua" in n for n in data["notes"])
    rows = client.get(SUM + "/rows", params={**past, "metric": "maternity_now", "department_id": world.dept["B.hc"]})
    assert {x["employee_code"] for x in rows.json()["data"]["rows"]} == {"Lts1", "Lts2", "Ltshet", "Ltskhe"}


def test_422_va_export(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    assert _get(client, SUM + "/rows", metric="people").status_code == 422
    assert _get(client, SUM + "/rows", metric="retire_12m", group_by="kind", group_key="__other__").status_code == 422
    assert _get(client, group_by="khong-co").status_code == 422
    assert _get(client, department_id="abc").status_code == 422
    resp = _get(client, SUM + "/export", department_id=world.dept["B.hc"])
    assert resp.status_code == 200 and resp.content[:2] == b"PK"


def test_pham_vi_va_department_chi_thu_hep(db, world, client_as):
    _emp(db, world, "pvB", gender=NAM, date_of_birth=_dob_retiring_in(100, NAM))
    _emp(db, world, "pvA", gender=NAM, date_of_birth=_dob_retiring_in(100, NAM), company_id=world.co["A"],
         department_id=world.dept["A.kt"])
    db.commit()
    _, client = _actor(db, world, client_as, scope="dept")
    assert set(_codes(client, "retire_12m")) == {"LpvA"}
    assert set(_codes(client, "retire_12m", department_id=world.dept["B.hc"])) == set()


@pytest.mark.parametrize("suffix", ["", "/export", "/rows"])
def test_chua_giao_bao_cao_403_ca_ba_duong(db, world, client_as, suffix):
    _, client = _actor(db, world, client_as, report=False)
    assert _get(client, SUM + suffix, metric="retire_12m").status_code == 403


def test_so_truy_van_khong_tang_theo_so_nhan_su(db, world):
    world.grant("a1", "employee", "all", actions=("read",))
    actor = world.actor("a1")
    prof = actor.profile()
    period = parse_period(QS)
    db.add(LeaveType(code="maternity", name="Nghỉ thai sản"))
    db.commit()

    def count() -> int:
        stmts: list[str] = []
        listener = lambda conn, cur, stmt, *a: stmts.append(stmt)               # noqa: E731
        engine = db.get_bind()
        event.listen(engine, "before_cursor_execute", listener)
        try:
            q = apply_scope(db.query(Employee), Employee, "employee", actor.user, prof)
            svc.build_summary(db, q, period, "department", leave_q=db.query(LeaveRequest))
            svc.build_rows(db, q, period, "retire_12m", "department", None, leave_q=db.query(LeaveRequest))
        finally:
            event.remove(engine, "before_cursor_execute", listener)
        return len(stmts)

    def add(n, start):
        mat = db.query(LeaveType).filter_by(code="maternity").one()
        for i in range(n):
            e = _emp(db, world, f"q{start + i}", gender=NU, date_of_birth=_dob_retiring_in(100 + i, NU))
            _leave(db, e, mat)
            _child(db, e, 50 + i)
        db.commit()

    add(3, 0)
    c3 = count()
    add(12, 3)
    assert count() == c3


def test_qua_tuoi_nghi_huu_van_dang_lam_co_danh_sach_bam_so(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    past = _codes(client, "past_retirement", department_id=world.dept["B.hc"])
    assert set(past) == {"Lnam_hqua"}                       # người đã nghỉ việc / thiếu giới tính không vào
    assert date.fromisoformat(past["Lnam_hqua"]["milestone"]) < TODAY
    assert past["Lnam_hqua"]["milestone"] == end_of_month(date.fromisoformat(past["Lnam_hqua"]["milestone"])).isoformat()


def test_thai_san_theo_pham_vi_don_nghi_phep(db, world, client_as):
    mat = LeaveType(code="maternity", name="Nghỉ thai sản")
    db.add(mat)
    db.flush()
    other = _emp(db, world, "tsother")
    _leave(db, other, mat)
    _leave(db, world.actor("a1").employee, mat)             # đơn của CHÍNH người xem: thấy
    db.commit()
    world.grant("a1", "employee", "all", actions=("read", "export"))
    world.grant("a1", "employee_sensitive", "all", actions=("read",))
    world.grant("a1", "leave_request", "own", actions=("read",))
    actor = world.actor("a1")
    db.add(ReportAccess(report_key=int(ReportKey.LEGAL_WATCH), subject_kind=SUBJECT_EMPLOYEE,
                        subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
    db.commit()
    client = client_as(actor.user)
    assert set(_codes(client, "maternity_now")) == {actor.employee.code}   # đơn người khác ngoài phạm vi `own`
    assert _get(client).json()["data"]["totals"]["current"]["maternity_now"] == 1


def test_bao_cao_doi_tuong_luat_khong_vao_bo_nho_dem():
    from app.core.report_cache import REPORT_SUMMARY_PATHS
    assert SUM not in REPORT_SUMMARY_PATHS          # ngày sinh / thai sản: thu hồi quyền phải có hiệu lực ngay
