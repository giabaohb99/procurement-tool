"""duoc-CR-686 — báo cáo Hợp đồng lao động (khóa 17): `/api/labor-contracts/summary` (+ export, rows).

Canh: định nghĩa từng chỉ số (đếm cờ), luật nối tiếp / nghỉ việc dùng chung với chuông cảnh báo,
phạm vi dữ liệu, `department_id` chỉ thu hẹp, gác khóa báo cáo ở CẢ ba đường, 422, xlsx, và số truy
vấn CỐ ĐỊNH. Mọi bài đi qua `TestClient` vì `require_report` gắn ở `dependencies=[...]`.
"""
import uuid
from datetime import timedelta

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
from app.modules.employee.model import Employee
from app.modules.labor_contract import report_service
from app.modules.labor_contract.model import LaborContract
from app.modules.report_access.model import ReportAccess

TODAY = vn_today()
SIGNED, DRAFT, TERMINATED = 2, 1, 4
PROBATION, FIXED, INDEFINITE = 1, 2, 3
SUM = "/api/labor-contracts/summary"
QS = {"preset": "custom", "date_from": str(TODAY - timedelta(days=30)), "date_to": str(TODAY), "compare": "none"}
_seq = {"n": 0}


@pytest.fixture
def client_as(db):
    def make_client(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        #  Token DUY NHẤT mỗi lượt: bộ nhớ đệm `/summary` khóa theo token, một HIT bỏ qua mọi gác.
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make_client
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _emp(db, world, tag, dept="B.hc", co="B", **kw) -> Employee:
    e = Employee(code=f"H{tag}", full_name=f"Người {tag}", company_id=world.co[co],
                 department_id=world.dept[dept], is_active=True, **kw)
    db.add(e)
    db.flush()
    return e


def _hd(db, world, emp, *, ctype=FIXED, status=SIGNED, start=-300, end=None, dept="B.hc", co="B",
        scan=9, **kw) -> LaborContract:
    _seq["n"] += 1
    c = LaborContract(code=f"HD{_seq['n']:05d}", employee_id=emp.id, company_id=world.co[co],
                      department_id=world.dept[dept], contract_type=ctype, status=status,
                      start_date=TODAY + timedelta(days=start),
                      end_date=None if end is None else TODAY + timedelta(days=end),
                      signed_file_id=scan, base_salary=10_000_000, **kw)
    db.add(c)
    db.flush()
    return c


def _dataset(db, world):
    """Mười người trong phòng B.hc (phòng thế giới mẫu không có ai) -> số liệu cô lập."""
    a = _emp(db, world, "act"); _hd(db, world, a, end=20)
    b = _emp(db, world, "e80"); _hd(db, world, b, end=80, scan=0)
    p = _emp(db, world, "prob"); _hd(db, world, p, ctype=PROBATION, start=-60, end=10)
    o = _emp(db, world, "over"); _hd(db, world, o, end=-5)
    s = _emp(db, world, "succ"); _hd(db, world, s, end=10); _hd(db, world, s, status=DRAFT, start=11, end=400)
    r = _emp(db, world, "res", status="resigned"); _hd(db, world, r, end=10)
    _emp(db, world, "none")
    t = _emp(db, world, "two"); _hd(db, world, t, start=-800, end=-400); _hd(db, world, t, start=-300, end=200)
    n = _emp(db, world, "new"); _hd(db, world, n, ctype=INDEFINITE, start=-5)
    x = _emp(db, world, "term"); _hd(db, world, x, status=TERMINATED, start=-200, end=-3,
                                     terminated_date=TODAY - timedelta(days=3))
    db.commit()


def _actor(db, world, client_as, key="a1", scope="all", entities=("labor_contract", "employee"),
           report=True):
    for ent in entities:
        world.grant(key, ent, scope, actions=("read", "export"))
    actor = world.actor(key)
    if report:
        db.add(ReportAccess(report_key=int(ReportKey.LABOR_CONTRACT), subject_kind=SUBJECT_EMPLOYEE,
                            subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
        db.commit()
    return actor, client_as(actor.user)


def _get(client, path=SUM, **extra):
    dept = extra.pop("department_id", "")
    return client.get(path, params={**QS, "department_id": dept, **extra})


def test_dinh_nghia_tung_chi_so(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    resp = _get(client, department_id=world.dept["B.hc"])
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    cur = data["totals"]["current"]
    assert cur == {"active": 6, "expiring_30": 2, "expiring_60": 2, "expiring_90": 3,
                   "probation_expiring_30": 1, "overdue": 1, "no_contract": 1, "missing_scan": 1,
                   "second_fixed_term": 1, "new_contracts": 1, "terminated": 1,
                   "resigned_not_terminated": 1}
    assert data["trend"] == [] and data["totals"]["compare"] is None
    assert data["meta"]["drilldown_metrics"] == list(cur)


def test_nhom_theo_loai_hd_va_phong_ban(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    data = _get(client, department_id=world.dept["B.hc"], group_by="contract_type").json()["data"]
    labels = {g["label"]: g["current"] for g in data["groups"]}
    assert labels["Xác định thời hạn"]["active"] == 4     # act, e80, succ, two (res đã nghỉ)
    assert labels["(Chưa gắn)"]["no_contract"] == 1      # hàng chưa có HĐ không có loại
    assert data["breakdowns"]["contract_type"]
    data = _get(client, group_by="department").json()["data"]
    assert any(g["key"] == str(world.dept["B.hc"]) for g in data["groups"])


def test_rows_khop_con_so_va_co_luong_va_link(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    dept = world.dept["B.hc"]
    resp = _get(client, SUM + "/rows", department_id=dept, metric="expiring_30")
    assert resp.status_code == 200, resp.text
    body = resp.json()["data"]
    assert body["total"] == 2 and not body["truncated"]
    assert [c["key"] for c in body["columns"]][-3:] == ["base_salary", "insurance_salary", "allowance"]
    assert {r["employee_code"] for r in body["rows"]} == {"Hact", "Hprob"}
    assert all(r["link"].startswith("/hr/employees/") and r["link"].endswith("?tab=labor-contracts")
               for r in body["rows"])
    assert body["rows"][0]["base_salary"] == 10_000_000
    ok = _get(client, SUM + "/rows", metric="active", group_by="department", group_key=str(dept))
    assert ok.json()["data"]["total"] == 6
    other = _get(client, SUM + "/rows", metric="active", group_by="department",
                 group_key=str(world.dept["A.mua"]))
    assert other.json()["data"]["total"] == 0
    none = _get(client, SUM + "/rows", department_id=dept, metric="no_contract").json()["data"]
    assert [r["employee_code"] for r in none["rows"]] == ["Hnone"] and none["rows"][0]["contract_code"] == ""


@pytest.mark.parametrize("extra", [{"metric": "salary"}, {},
                                   {"metric": "active", "group_by": "department", "group_key": "__other__"},
                                   {"metric": "active", "group_by": "bogus", "group_key": "1"}])
def test_rows_422(db, world, client_as, extra):
    _, client = _actor(db, world, client_as)
    assert _get(client, SUM + "/rows", **extra).status_code == 422


def test_department_id_rac_422_va_export_xlsx(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    assert _get(client, department_id="abc").status_code == 422
    resp = _get(client, SUM + "/export", department_id=world.dept["B.hc"])
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers["content-type"] and resp.content[:2] == b"PK"


def test_pham_vi_dept_chi_thay_hd_phong_minh_va_department_id_chi_thu_hep(db, world, client_as):
    e1 = _emp(db, world, "pv1", dept="A.kt", co="A"); _hd(db, world, e1, dept="A.kt", co="A", end=200)
    e2 = _emp(db, world, "pv2"); _hd(db, world, e2, end=200)
    db.commit()
    _, client = _actor(db, world, client_as, scope="dept", entities=("labor_contract",))
    cur = _get(client).json()["data"]["totals"]["current"]
    assert cur["active"] == 1                                   # chỉ HĐ phòng A.kt của a1
    assert cur["no_contract"] == 0                              # không có quyền employee -> không thấy ai
    narrowed = _get(client, department_id=world.dept["B.hc"]).json()["data"]["totals"]["current"]
    assert narrowed["active"] == 0                              # chỉ THU HẸP, không mở rộng sang B.hc


@pytest.mark.parametrize("suffix", ["", "/export", "/rows"])
def test_chua_giao_bao_cao_403_ca_ba_duong(db, world, client_as, suffix):
    _, client = _actor(db, world, client_as, report=False)
    assert _get(client, SUM + suffix, metric="active").status_code == 403


def test_so_truy_van_khong_tang_theo_so_hop_dong(db, world):
    world.grant("a1", "labor_contract", "all", actions=("read",))
    world.grant("a1", "employee", "all", actions=("read",))
    actor = world.actor("a1")
    prof = actor.profile()
    period = parse_period(QS)

    def run():
        report_service.build_summary(
            db, apply_scope(db.query(LaborContract), LaborContract, "labor_contract", actor.user, prof),
            apply_scope(db.query(Employee), Employee, "employee", actor.user, prof), period, "department")

    def count() -> int:
        stmts: list[str] = []

        def listener(conn, cur, stmt, *args):
            stmts.append(stmt)

        engine = db.get_bind()
        event.listen(engine, "before_cursor_execute", listener)
        try:
            run()
        finally:
            event.remove(engine, "before_cursor_execute", listener)
        return len(stmts)

    def add(n, start):
        for i in range(n):
            e = _emp(db, world, f"q{start + i}")
            _hd(db, world, e, end=20 + i)
            _emp(db, world, f"nq{start + i}")
        db.commit()

    add(5, 0)
    c5 = count()
    add(45, 5)
    c50 = count()
    assert c5 > 0 and c5 == c50, (c5, c50)


def test_ky_qua_khu_van_thay_hd_chua_cham_dut_tai_thoi_diem_do(db, world, client_as):
    """HĐ chạy từ 300 ngày trước, chấm dứt 5 ngày trước: xem kỳ 60–31 ngày trước PHẢI thấy đang hiệu lực."""
    e = _emp(db, world, "past")
    _hd(db, world, e, status=TERMINATED, start=-300, end=200, terminated_date=TODAY - timedelta(days=5))
    db.commit()
    _, client = _actor(db, world, client_as)
    past = {"preset": "custom", "date_from": str(TODAY - timedelta(days=60)),
            "date_to": str(TODAY - timedelta(days=31)), "compare": "none"}
    cur = client.get(SUM, params={**past, "department_id": world.dept["B.hc"]}).json()["data"]["totals"]["current"]
    assert cur["active"] == 1 and cur["no_contract"] == 0
    now = _get(client, department_id=world.dept["B.hc"]).json()["data"]["totals"]["current"]
    assert now["active"] == 0 and now["terminated"] == 1               # kỳ hiện tại: đã chấm dứt


def test_second_fixed_term_dem_ca_hd_da_cham_dut_nhung_khong_doi_luat_noi_tiep(db, world, client_as):
    e = _emp(db, world, "tw2")
    _hd(db, world, e, status=TERMINATED, start=-800, end=-400, terminated_date=TODAY - timedelta(days=500))
    _hd(db, world, e, start=-300, end=200)
    db.commit()
    _, client = _actor(db, world, client_as)
    cur = _get(client, department_id=world.dept["B.hc"]).json()["data"]["totals"]["current"]
    assert cur["second_fixed_term"] == 1 and cur["active"] == 1
    assert cur["overdue"] == 0 and cur["expiring_90"] == 0


def test_ma_loai_hd_la_khong_gay_500():
    from app.modules.labor_contract.report_data import type_label
    assert type_label(77) == "Khác" and type_label(2) == "Xác định thời hạn"
