"""duoc-CR-689 (phase 17) — báo cáo A4 «Định biên kế hoạch so với thực tế» (khóa 25) và cột kế hoạch của A5.

Canh A4: định nghĩa chỉ số (planned · actual · gap · vacancies · over · unplanned · fill_rate), luật chống cộng
đôi giữa dòng «toàn pháp nhân» và dòng phòng, phòng có người mà chưa có kế hoạch, phạm vi, `/rows`, gác khóa báo
cáo + quyền, xlsx, số truy vấn CỐ ĐỊNH. Canh A5: ba cột mới (planned_payroll · payroll_remaining · payroll_use_rate),
ưu tiên dòng «toàn pháp nhân», không hiện khi thiếu quyền xem kế hoạch, che nhóm dưới 3 người vẫn che cả ba cột.
"""
import uuid
from datetime import date, timedelta
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import event

from app.core.auth import get_current_user, get_perm_profile
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.subject_match import SUBJECT_EMPLOYEE
from app.core.vn_time import vn_today
from app.main import app
from app.modules.department.model import Department
from app.modules.employee import headcount_plan_report_service as svc
from app.modules.employee.model import Employee
from app.modules.headcount_plan.model import HeadcountPlan
from app.modules.labor_contract.model import LaborContract
from app.modules.report_access.model import ReportAccess

TODAY = vn_today()
A4 = "/api/headcount-plan-report/summary"
A5 = "/api/payroll-fund/summary"
QS = {"preset": "custom", "date_from": (TODAY - timedelta(days=20)).isoformat(), "date_to": TODAY.isoformat(),
      "compare": "none"}
QS5 = {"preset": "custom", "date_from": "2026-06-01", "date_to": "2026-08-31", "compare": "none"}
_seq = {"n": 0}


@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _emp(db, world, tag, dept="B.hc", **kw) -> Employee:
    dept_id = world.dept[dept] if isinstance(dept, str) else dept
    e = Employee(code=f"P{tag}", full_name=f"Người {tag}", company_id=world.co["B"], department_id=dept_id,
                 is_active=True, hire_date=kw.pop("hire_date", TODAY - timedelta(days=400)), **kw)
    db.add(e)
    db.flush()
    return e


def _plan(db, world, dept, n, pay=0, year=None, co="B"):
    db.add(HeadcountPlan(year=year or TODAY.year, company_id=world.co[co],
                         department_id=world.dept[dept] if dept else 0, planned_headcount=n,
                         planned_payroll_monthly=pay))
    db.commit()


def _dataset(db, world, extra=0):
    """Pháp nhân B: B.kt có b1 (sẵn) · B.hc 4 người · B_NEW 2 người (không kế hoạch) — tổng 7."""
    new = Department(code="B_NEW", name="Phòng Mới", company_id=world.co["B"], is_active=True)
    db.add(new)
    db.flush()
    for i in range(4 + extra):
        _emp(db, world, f"h{i}")
    for i in range(2):
        _emp(db, world, f"n{i}", dept=new.id)
    # người đã nghỉ trước hôm nay và người vào làm SAU hôm nay: không tính
    _emp(db, world, "gone", status="resigned", resign_date=TODAY - timedelta(days=3))
    _emp(db, world, "future", hire_date=TODAY + timedelta(days=30))
    db.commit()
    return new


def _actor(db, world, client_as, *, key="a1", report=True, plan_actions=("read", "export"), scope="all",
           employee=True, rkey=ReportKey.HEADCOUNT_PLAN, **grant_kw):
    world.grant(key, "headcount_plan", scope, actions=plan_actions, **grant_kw)
    if employee:
        world.grant(key, "employee", "all", actions=("read",))
    actor = world.actor(key)
    if report:
        db.add(ReportAccess(report_key=int(rkey), subject_kind=SUBJECT_EMPLOYEE, subject_id=actor.employee.id,
                            effect=1, reason="t", created_by=0, updated_by=0))
        db.commit()
    return actor, client_as(actor.user)


def _get(client, path=A4, qs=QS, **extra):
    return client.get(path, params={**qs, "company_id": extra.pop("company_id", ""),
                                    "department_id": extra.pop("department_id", ""), **extra})


def _cur(resp):
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["totals"]["current"]


def test_dinh_nghia_chi_so_khi_chi_co_dong_phong(db, world, client_as):
    _dataset(db, world)
    _plan(db, world, "B.kt", 1)
    _plan(db, world, "B.hc", 6)
    _, client = _actor(db, world, client_as)
    resp = _get(client, company_id=world.co["B"])
    cur = _cur(resp)
    assert cur["planned"] == 7 and cur["actual"] == 7 and cur["gap"] == 0
    assert cur["vacancies"] == 2 and cur["over"] == 0 and cur["unplanned"] == 2
    assert cur["fill_rate"] == pytest.approx(71.4, abs=0.05)     # (1 + 4) / 7
    data = resp.json()["data"]
    assert data["totals"]["compare"] is None and data["trend"] == []
    assert data["meta"]["drilldown_metrics"] == ["actual", "unplanned"]
    assert [d["key"] for d in data["meta"]["dimensions"]] == ["company", "department"]
    assert not any(m["key"] == "filled" and not m["helper"] for m in data["meta"]["metrics"])


def test_xem_theo_phong_va_phong_chua_co_ke_hoach(db, world, client_as):
    _dataset(db, world)
    _plan(db, world, "B.kt", 1)
    _plan(db, world, "B.hc", 6)
    _, client = _actor(db, world, client_as)
    data = _get(client, company_id=world.co["B"], group_by="department").json()["data"]
    by = {g["label"]: g["current"] for g in data["groups"]}
    assert by["Phòng Hành chính"]["actual"] == 4 and by["Phòng Hành chính"]["vacancies"] == 2
    assert by["Phòng Kế toán"]["planned"] == 1 and by["Phòng Kế toán"]["actual"] == 1
    new = by["Phòng Mới (chưa có kế hoạch)"]
    assert new["planned"] == 0 and new["actual"] == 2 and new["unplanned"] == 2 and new["vacancies"] == 0
    assert any("Phòng Mới" in n and "chưa có kế hoạch" in n for n in data["notes"])
    comp = _get(client, company_id=world.co["B"], group_by="company").json()["data"]["groups"]
    assert len(comp) == 1 and comp[0]["current"]["planned"] == 7


def test_dong_toan_phap_nhan_khong_cong_doi_voi_dong_phong(db, world, client_as):
    _dataset(db, world)
    _plan(db, world, "B.kt", 1)
    _plan(db, world, "B.hc", 6)
    _plan(db, world, None, 5)                                 # cả pháp nhân B: 5, thực tế 7
    _, client = _actor(db, world, client_as)
    cur = _cur(_get(client, company_id=world.co["B"]))
    assert cur["planned"] == 5 and cur["actual"] == 7 and cur["over"] == 2 and cur["vacancies"] == 0
    assert cur["unplanned"] == 0 and cur["fill_rate"] == 100.0
    data = _get(client, company_id=world.co["B"], group_by="department").json()["data"]
    assert data["totals"]["current"]["planned"] == 5          # Tổng KHÔNG cộng 1 + 6 + 5
    labels = {g["label"]: g["current"] for g in data["groups"]}
    whole = next(v for k, v in labels.items() if "Toàn pháp nhân" in k)
    assert whole["planned"] == 5 and whole["actual"] == 7 and whole["over"] == 2
    assert labels["Phòng Hành chính"]["planned"] == 6          # dòng phòng vẫn hiện ở góc nhìn Phòng ban
    comp = _get(client, company_id=world.co["B"], group_by="company").json()["data"]["groups"]
    assert comp[0]["current"]["planned"] == 5


def test_nhieu_phap_nhan_cong_tong_dung_va_department_id_thu_hep(db, world, client_as):
    _dataset(db, world)
    _plan(db, world, "B.hc", 6)
    _plan(db, world, "A.kt", 2, co="A")
    _, client = _actor(db, world, client_as)
    cur = _cur(_get(client))
    assert cur["planned"] == 8
    one = _cur(_get(client, department_id=world.dept["B.hc"]))
    assert one["planned"] == 6 and one["actual"] == 4 and one["vacancies"] == 2


def test_nam_ke_hoach_la_nam_cuoi_ky(db, world, client_as):
    _dataset(db, world)
    _plan(db, world, "B.hc", 6, year=TODAY.year - 1)
    _, client = _actor(db, world, client_as)
    assert _cur(_get(client, company_id=world.co["B"]))["planned"] == 0
    qs = {**QS, "date_from": f"{TODAY.year - 1}-01-01", "date_to": f"{TODAY.year - 1}-06-30"}
    cur = _cur(_get(client, qs=qs, company_id=world.co["B"]))
    assert cur["planned"] == 6        # mốc thực tế vẫn là cuối kỳ: phòng chưa có ai vào làm ở thời điểm đó


def test_pham_vi_theo_phong(db, world, client_as):
    _dataset(db, world)
    _plan(db, world, "B.kt", 1)
    _plan(db, world, "B.hc", 6)
    _plan(db, world, None, 50)
    _, client = _actor(db, world, client_as, scope="dept", inc_dept=("B.hc",))
    cur = _cur(_get(client))
    #  Phạm vi `dept` = phòng của chính mình (A.kt: 3 người, không có kế hoạch) + phòng khai thêm (B.hc).
    #  Không thấy B.kt, B_NEW và dòng «toàn pháp nhân» (50) của B.
    assert cur["planned"] == 6 and cur["actual"] == 4 + 3 and cur["unplanned"] == 3


def test_rows_khop_so_tren_bang(db, world, client_as):
    new = _dataset(db, world)
    _plan(db, world, "B.hc", 6)
    _plan(db, world, "B.kt", 1)
    _, client = _actor(db, world, client_as)
    base = {"company_id": world.co["B"], "group_by": "department"}
    rows = _get(client, f"{A4}/rows", metric="actual", group_key=str(world.dept["B.hc"]), **base).json()["data"]
    assert rows["total"] == 4 and [c["key"] for c in rows["columns"]][:2] == ["code", "name"]
    assert all(r["department"] == "Phòng Hành chính" for r in rows["rows"])
    unp = _get(client, f"{A4}/rows", metric="unplanned", company_id=world.co["B"]).json()["data"]
    assert unp["total"] == 2 and {r["department"] for r in unp["rows"]} == {"Phòng Mới"}
    assert new.id
    whole = _get(client, f"{A4}/rows", metric="actual", group_key=f"c{world.co['B']}", **base).json()["data"]
    assert whole["total"] == 7
    assert _get(client, f"{A4}/rows", metric="vacancies").status_code == 422
    assert _get(client, f"{A4}/rows", metric="actual", group_by="department", group_key="__other__").status_code == 422


def test_rows_unplanned_khop_kpi_khi_co_dong_toan_phap_nhan(db, world, client_as):
    new = _dataset(db, world)
    _plan(db, world, "B.hc", 6)
    _plan(db, world, None, 5)                       # B_NEW nằm dưới dòng «Toàn pháp nhân» -> KPI unplanned = 0
    _, client = _actor(db, world, client_as)
    qs = {"company_id": world.co["B"]}
    for gb in ("company", "department"):
        kpi = _cur(_get(client, group_by=gb, **qs))["unplanned"]
        rows = _get(client, f"{A4}/rows", metric="unplanned", group_by=gb, **qs).json()["data"]
        assert kpi == 0 and rows["total"] == 0, gb
    one = _get(client, f"{A4}/rows", metric="unplanned", group_by="department", group_key=str(new.id), **qs)
    assert one.json()["data"]["total"] == 2         # bấm đúng nhóm Phòng ban «chưa có kế hoạch» vẫn liệt kê


def test_rows_unplanned_khop_kpi_khi_khong_co_dong_toan_phap_nhan(db, world, client_as):
    _dataset(db, world)
    _plan(db, world, "B.hc", 6)
    _, client = _actor(db, world, client_as)
    for gb in ("company", "department"):
        kpi = _cur(_get(client, group_by=gb, company_id=world.co["B"]))["unplanned"]
        rows = _get(client, f"{A4}/rows", metric="unplanned", group_by=gb, company_id=world.co["B"]).json()["data"]
        assert kpi == rows["total"] == 3, gb        # B_NEW 2 + B.kt 1 (b1 sẵn có, chưa có kế hoạch)


def test_rows_doi_them_employee_read(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as, employee=False)
    assert _get(client).status_code == 200
    assert _get(client, f"{A4}/rows", metric="actual").status_code == 403


@pytest.mark.parametrize("suffix", ["", "/export", "/rows"])
def test_chua_giao_bao_cao_hoac_thieu_quyen_403(db, world, client_as, suffix):
    _, client = _actor(db, world, client_as, report=False)
    assert _get(client, f"{A4}{suffix}", metric="actual").status_code == 403


def test_export_can_quyen_export(db, world, client_as):
    _dataset(db, world)
    _plan(db, world, "B.hc", 6)
    _, client = _actor(db, world, client_as)
    resp = _get(client, f"{A4}/export", company_id=world.co["B"], group_by="department")
    assert resp.status_code == 200
    text = " ".join(str(c.value) for ws in load_workbook(BytesIO(resp.content)) for row in ws.iter_rows() for c in row)
    assert "Định biên kế hoạch" in text and "Phòng Hành chính" in text
    _, ro = _actor(db, world, client_as, key="a2", plan_actions=("read",))
    assert _get(ro, f"{A4}/export").status_code == 403


def test_so_truy_van_co_dinh(db, world):
    world.grant("a1", "headcount_plan", scope="all", actions=("read",))
    actor = world.actor("a1")
    prof = get_perm_profile(db, actor.user)
    period = parse_period(QS)
    _dataset(db, world)
    _plan(db, world, "B.hc", 6)

    def count():
        stmts, eng = [], db.get_bind()

        def on(conn, cursor, statement, *a):
            stmts.append(statement)
        event.listen(eng, "before_cursor_execute", on)
        try:
            svc.build_summary(db, actor.user, prof, period, "department")
        finally:
            event.remove(eng, "before_cursor_execute", on)
        return len(stmts)

    c = count()
    for i in range(30):
        _emp(db, world, f"more{i}")
    for dept in ("B.kt", "A.kt", "A.mua"):
        _plan(db, world, dept, 3, year=TODAY.year, co="B" if dept.startswith("B") else "A")
    db.commit()
    assert c > 0 and c == count()


# ── A5: cột kế hoạch ─────────────────────────────────────────────────────────

def _hd(db, world, emp, base=10_000_000, allow=1_000_000):
    _seq["n"] += 1
    db.add(LaborContract(code=f"PL{_seq['n']:05d}", employee_id=emp.id, company_id=world.co["B"],
                         department_id=emp.department_id, contract_type=2, status=2,
                         start_date=date(2026, 5, 1), signed_file_id=1, base_salary=base, allowance=allow,
                         insurance_salary=0))


def _a5_actor(db, world, client_as, *, plan=True, lc_scope="all"):
    world.grant("a1", "labor_contract", lc_scope, actions=("read", "export"))
    if plan:
        world.grant("a1", "headcount_plan", "all", actions=("read", "export"))
    actor = world.actor("a1")
    db.add(ReportAccess(report_key=int(ReportKey.PAYROLL_FUND), subject_kind=SUBJECT_EMPLOYEE,
                        subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
    db.commit()
    return client_as(actor.user)


def test_a5_cot_ke_hoach_theo_phong_va_tong(db, world, client_as):
    for i in range(3):
        _hd(db, world, _emp(db, world, f"s{i}"))
    _plan(db, world, "B.hc", 5, pay=50_000_000, year=2026)
    client = _a5_actor(db, world, client_as)
    resp = _get(client, A5, qs=QS5, company_id=world.co["B"], group_by="department")
    data = resp.json()["data"]
    cur = data["totals"]["current"]
    assert cur["payroll_total"] == 33_000_000 and cur["planned_payroll"] == 50_000_000
    assert cur["payroll_remaining"] == 17_000_000 and cur["payroll_use_rate"] == 66.0
    grp = data["groups"][0]["current"]
    assert grp["planned_payroll"] == 50_000_000 and grp["payroll_use_rate"] == 66.0
    keys = [m["key"] for m in data["meta"]["metrics"]]
    assert keys[-3:] == ["planned_payroll", "payroll_remaining", "payroll_use_rate"]


def test_a5_hdld_pham_vi_phong_khong_thay_quy_luong_ke_hoach(db, world, client_as):
    #  E2E CR-689 B1: HĐLĐ phạm vi phòng vẫn đọc ra quỹ lương kế hoạch cả pháp nhân trong khi màn kế hoạch che.
    for i in range(3):
        _hd(db, world, _emp(db, world, f"s{i}"))
    _plan(db, world, None, 5, pay=90_000_000, year=2026)
    client = _a5_actor(db, world, client_as, lc_scope="dept")
    for gb in ("none", "company"):
        data = _get(client, A5, qs=QS5, group_by=gb).json()["data"]
        assert data["totals"]["current"]["planned_payroll"] is None
        assert all(g["current"]["planned_payroll"] is None for g in data.get("groups") or [])


def test_a5_dong_toan_phap_nhan_uu_tien_va_chi_gan_theo_nhom_phap_nhan_phong(db, world, client_as):
    for i in range(3):
        _hd(db, world, _emp(db, world, f"s{i}"))
    _plan(db, world, "B.hc", 5, pay=50_000_000, year=2026)
    _plan(db, world, None, 5, pay=90_000_000, year=2026)
    client = _a5_actor(db, world, client_as)
    comp = _get(client, A5, qs=QS5, company_id=world.co["B"], group_by="company").json()["data"]
    assert comp["totals"]["current"]["planned_payroll"] == 90_000_000      # không cộng 50 + 90
    assert comp["groups"][0]["current"]["planned_payroll"] == 90_000_000
    dept = _get(client, A5, qs=QS5, company_id=world.co["B"], group_by="department").json()["data"]
    assert dept["groups"][0]["current"]["planned_payroll"] == 50_000_000
    pos = _get(client, A5, qs=QS5, company_id=world.co["B"], group_by="contract_type").json()["data"]
    assert pos["groups"][0]["current"]["planned_payroll"] is None and pos["totals"]["current"]["planned_payroll"] == 90_000_000


def test_a5_khong_co_cot_khi_thieu_quyen_xem_ke_hoach_hoac_chua_khai_luong(db, world, client_as):
    for i in range(3):
        _hd(db, world, _emp(db, world, f"s{i}"))
    _plan(db, world, "B.hc", 5, pay=50_000_000, year=2026)
    client = _a5_actor(db, world, client_as, plan=False)
    keys = [m["key"] for m in _get(client, A5, qs=QS5).json()["data"]["meta"]["metrics"]]
    assert "planned_payroll" not in keys
    db.query(HeadcountPlan).update({"planned_payroll_monthly": 0})
    db.commit()
    client2 = _a5_actor_second(db, world, client_as)
    cur = _cur(_get(client2, A5, qs=QS5, company_id=world.co["B"]))
    assert cur["planned_payroll"] is None and cur["payroll_remaining"] is None and cur["payroll_use_rate"] is None


def _a5_actor_second(db, world, client_as):
    world.grant("a2", "labor_contract", "all", actions=("read",))
    world.grant("a2", "headcount_plan", "all", actions=("read",))
    actor = world.actor("a2")
    db.add(ReportAccess(report_key=int(ReportKey.PAYROLL_FUND), subject_kind=SUBJECT_EMPLOYEE,
                        subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
    db.commit()
    return client_as(actor.user)


def test_a5_nhom_duoi_3_nguoi_bi_che_ca_cot_ke_hoach(db, world, client_as):
    for i in range(3):
        _hd(db, world, _emp(db, world, f"s{i}"))
    for i in range(2):
        _hd(db, world, _emp(db, world, f"k{i}", dept="B.kt"))
    _plan(db, world, "B.hc", 5, pay=50_000_000, year=2026)
    _plan(db, world, "B.kt", 2, pay=20_000_000, year=2026)
    client = _a5_actor(db, world, client_as)
    data = _get(client, A5, qs=QS5, company_id=world.co["B"], group_by="department").json()["data"]
    by = {g["label"]: g for g in data["groups"]}
    hidden = by["Phòng Kế toán"]
    assert hidden.get("suppressed") and hidden["current"]["planned_payroll"] is None
    assert hidden["current"]["payroll_remaining"] is None and hidden["current"]["payroll_use_rate"] is None


def test_a5_nhom_phong_ban_cong_dong_ke_hoach_cua_cung_phong_o_nhieu_phap_nhan(db, world, client_as):
    for i in range(3):
        _hd(db, world, _emp(db, world, f"s{i}"))
    _plan(db, world, "B.hc", 5, pay=50_000_000, year=2026)
    _plan(db, world, "B.hc", 5, pay=30_000_000, year=2026, co="A")   # phòng dùng chung: cùng phòng, pháp nhân khác
    client = _a5_actor(db, world, client_as)
    data = _get(client, A5, qs=QS5, group_by="department").json()["data"]
    hc = next(g for g in data["groups"] if g["label"] == "Phòng Hành chính")
    assert hc["current"]["planned_payroll"] == 80_000_000


def test_a5_phap_nhan_co_ke_hoach_nhung_khong_co_hdld_ra_dong_rieng_va_khop_tong(db, world, client_as):
    #  CR-689 N2: quỹ kế hoạch của pháp nhân không có HĐ nào trong kỳ vẫn ra dòng nhóm, cộng nhóm = Tổng.
    for i in range(3):
        _hd(db, world, _emp(db, world, f"s{i}"))
    _plan(db, world, None, 5, pay=40_000_000, year=2026, co="B")
    _plan(db, world, None, 5, pay=25_000_000, year=2026, co="A")        # A không có HĐ
    client = _a5_actor(db, world, client_as)
    data = _get(client, A5, qs=QS5, group_by="company").json()["data"]
    by = {g["key"]: g for g in data["groups"]}
    assert set(by) == {str(world.co["B"]), str(world.co["A"])}
    a = by[str(world.co["A"])]
    assert a["label"] and not a.get("suppressed")
    cur = a["current"]
    assert cur["people_paid"] == 0 and cur["payroll_total"] == 0 and cur["avg_payroll"] is None
    assert cur["planned_payroll"] == 25_000_000 and cur["payroll_remaining"] == 25_000_000
    assert cur["payroll_use_rate"] == 0
    assert sum(g["current"]["planned_payroll"] for g in data["groups"]) == data["totals"]["current"]["planned_payroll"] == 65_000_000


def test_a5_phong_co_ke_hoach_chua_co_hdld_ra_dong_rieng(db, world, client_as):
    for i in range(3):
        _hd(db, world, _emp(db, world, f"s{i}"))
    _plan(db, world, "B.hc", 5, pay=50_000_000, year=2026)
    _plan(db, world, "B.kt", 2, pay=20_000_000, year=2026)               # Kế toán không có HĐ
    client = _a5_actor(db, world, client_as)
    data = _get(client, A5, qs=QS5, company_id=world.co["B"], group_by="department").json()["data"]
    by = {g["label"]: g for g in data["groups"]}
    kt = by["Phòng Kế toán"]["current"]
    assert kt["people_paid"] == 0 and kt["planned_payroll"] == 20_000_000 and kt["payroll_use_rate"] == 0
    assert sum(g["current"]["planned_payroll"] for g in data["groups"]) == data["totals"]["current"]["planned_payroll"]


def test_a5_khong_co_cot_ke_hoach_thi_khong_them_dong_rieng(db, world, client_as):
    for i in range(3):
        _hd(db, world, _emp(db, world, f"s{i}"))
    _plan(db, world, None, 5, pay=25_000_000, year=2026, co="A")
    client = _a5_actor(db, world, client_as, plan=False)
    data = _get(client, A5, qs=QS5, group_by="company").json()["data"]
    assert [g["key"] for g in data["groups"]] == [str(world.co["B"])]
