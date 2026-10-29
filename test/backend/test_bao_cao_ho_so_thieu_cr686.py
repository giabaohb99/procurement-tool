"""duoc-CR-686 — báo cáo «Hồ sơ & tài khoản còn thiếu» (khóa 18): `/api/employees/profile-gaps/summary`.

Canh: định nghĩa từng chỉ số, nhóm nhạy cảm / tài khoản CHỈ hiện khi có quyền (vắng khỏi `meta`,
không rò giá trị), phạm vi dữ liệu, `department_id` chỉ thu hẹp, gác khóa báo cáo ở CẢ ba đường,
422, xlsx và số truy vấn CỐ ĐỊNH. Phòng B.hc của thế giới mẫu không có ai -> số liệu cô lập.
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
from app.modules.employee import profile_gaps_report_service as svc
from app.modules.employee.model import Employee
from app.modules.report_access.model import ReportAccess
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole

TODAY = vn_today()
SUM = "/api/employees/profile-gaps/summary"
QS = {"preset": "this_month", "compare": "previous"}   # kỳ so sánh phải bị bỏ qua
_n = {"v": 0}


@pytest.fixture
def client_as(db):
    def make_client(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make_client
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _emp(db, world, tag, *, full=True, sensitive=True, **kw) -> Employee:
    base = dict(code=f"G{tag}", full_name=f"Người {tag}", company_id=world.co["B"],
                department_id=world.dept["B.hc"], is_active=True)
    if full:
        base.update(hire_date=date(2024, 1, 1), position_id=1, manager_id=1, position="Chuyên viên")
    if sensitive:
        base.update(date_of_birth=date(1990, 1, 1), id_number="079090123456", tax_code="8000000001",
                    social_insurance_no="7900000001", bank_account_no="1234567890")
    base.update(kw)
    e = Employee(**base)
    db.add(e)
    db.flush()
    return e


def _user(db, emp, *, active=True, role=False) -> User:
    _n["v"] += 1
    u = User(email=f"g{_n['v']}@t.vn", employee_id=emp.id, password_hash="x", is_active=active)
    db.add(u)
    db.flush()
    if role:
        r = Role(code=f"GR{_n['v']}", name="Vai trò thử")
        db.add(r)
        db.flush()
        db.add(UserRole(user_id=u.id, role_id=r.id))
        db.flush()
    return u


def _dataset(db, world):
    _emp(db, world, "ok", id_expiry_date=TODAY + timedelta(days=500))           # đủ mọi thứ
    _emp(db, world, "nohire", full=False)
    _emp(db, world, "nodept", department_id=0)                                 # ngoài mọi bộ lọc phòng
    _emp(db, world, "nosens", sensitive=False)
    _emp(db, world, "exp30", id_expiry_date=TODAY + timedelta(days=30))
    _emp(db, world, "expired", id_expiry_date=TODAY - timedelta(days=10))
    _emp(db, world, "exp200", id_expiry_date=TODAY + timedelta(days=200))
    a = _emp(db, world, "acc"); _user(db, a, role=True)
    b = _emp(db, world, "norole"); _user(db, b, role=False)
    r = _emp(db, world, "resigned", status="resigned"); _user(db, r, role=True)
    c = _emp(db, world, "resignedlocked", status="resigned"); _user(db, c, active=False)
    db.commit()


def _actor(db, world, client_as, *, sensitive=False, account=False, scope="all", report=True, key="a1"):
    world.grant(key, "employee", scope, actions=("read", "export"))
    if sensitive:
        world.grant(key, "employee_sensitive", "all", actions=("read",))
    if account:
        world.grant(key, "user", "all", actions=("read",))
    actor = world.actor(key)
    if report:
        db.add(ReportAccess(report_key=int(ReportKey.HR_PROFILE_GAPS), subject_kind=SUBJECT_EMPLOYEE,
                            subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
        db.commit()
    return actor, client_as(actor.user)


def _get(client, path=SUM, **extra):
    dept = extra.pop("department_id", "")
    return client.get(path, params={**QS, "department_id": dept, **extra})


def test_khong_quyen_nhay_cam_khong_quyen_tai_khoan(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    resp = _get(client, department_id=world.dept["B.hc"])
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    cur = data["totals"]["current"]
    keys = {m["key"] for m in data["meta"]["metrics"]}
    assert not keys & set(svc.SENSITIVE_GAPS) and not keys & set(svc.ACCOUNT_GAPS)
    assert "complete" in keys and "complete_rate" in keys                      # helper vẫn nằm trong meta
    assert [m["key"] for m in data["meta"]["metrics"] if m.get("helper")] == ["complete", "gap_rows"]
    assert cur["active_total"] == 8                                            # 10 người, 2 đã nghỉ
    assert cur["missing_hire_date"] == 1 and cur["missing_position"] == 1
    assert cur["missing_manager"] == 1 and cur["missing_department"] == 0
    assert "missing_dob" not in cur and "no_account" not in cur
    assert data["totals"]["compare"] is None and data["trend"] == []
    assert data["period"]["compare"] == "previous"                              # period vẫn trả như đã gửi
    assert any("quyền xem dữ liệu nhạy cảm" in n for n in data["notes"])
    assert any("quyền xem tài khoản" in n for n in data["notes"])
    assert data["meta"]["drilldown_metrics"] == ["active_total", *svc.BASE_GAPS]
    #  hồ sơ đủ = đủ 4 trường cơ bản (không xét nhạy cảm vì không có quyền): chỉ "nohire" thiếu
    assert cur["complete"] == 7 and cur["complete_rate"] == pytest.approx(87.5, abs=0.1)
    assert "079090123456" not in resp.text and "8000000001" not in resp.text


def test_co_quyen_nhay_cam_va_tai_khoan(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as, sensitive=True, account=True)
    resp = _get(client, department_id=world.dept["B.hc"])
    data = resp.json()["data"]
    cur = data["totals"]["current"]
    assert cur["active_total"] == 8                                            # 8 đang làm (2 đã nghỉ)
    assert cur["missing_dob"] == cur["missing_id_number"] == cur["missing_tax_code"] == 1   # nosens
    assert cur["missing_social_insurance"] == cur["missing_bank"] == 1
    assert cur["id_expiring_90"] == 2                                          # exp30 + expired (exp200 không)
    assert cur["no_account"] == 6 and cur["account_no_role"] == 1
    assert cur["resigned_active_account"] == 1                                 # tài khoản bị khóa không tính
    assert cur["complete"] == 6                                                # nohire, nosens thiếu trường
    assert data["meta"]["drilldown_metrics"] == ["active_total", *svc.BASE_GAPS, *svc.SENSITIVE_GAPS,
                                                 *svc.ACCOUNT_GAPS]
    assert "079090123456" not in resp.text
    g = _get(client, department_id=world.dept["B.hc"], group_by="gap_kind")      # gap_kind là breakdown, không phải nhóm
    assert g.status_code == 422
    bd = data["breakdowns"]["gap_kind"]
    assert {b["key"] for b in bd} >= {"no_account", "id_expiring_90", "missing_dob"}
    assert next(b["value"] for b in bd if b["key"] == "no_account") == 6


def test_nhom_theo_cong_ty_va_phong_ban(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    data = _get(client, group_by="department").json()["data"]
    assert any(g["key"] == str(world.dept["B.hc"]) for g in data["groups"])
    data = _get(client, group_by="company").json()["data"]
    assert any(g["label"] == "Công ty B" for g in data["groups"])


def test_rows_khop_va_cot_cmnd_chi_voi_quyen(db, world, client_as):
    _dataset(db, world)
    actor, client = _actor(db, world, client_as, sensitive=True, account=True)
    dept = world.dept["B.hc"]
    body = _get(client, SUM + "/rows", department_id=dept, metric="id_expiring_90").json()["data"]
    assert body["total"] == 2
    assert [c["key"] for c in body["columns"]] == ["employee_code", "employee_name", "company", "department",
                                                  "position", "hire_date", "id_expiry_date"]
    assert {r["employee_code"] for r in body["rows"]} == {"Gexp30", "Gexpired"}
    assert "079090123456" not in str(body) and body["rows"][0]["link"].startswith("/hr/employees/")
    body = _get(client, SUM + "/rows", department_id=dept, metric="missing_manager").json()["data"]
    assert [r["employee_code"] for r in body["rows"]] == ["Gnohire"]
    assert "id_expiry_date" not in {c["key"] for c in body["columns"]}
    body = _get(client, SUM + "/rows", department_id=dept, metric="resigned_active_account").json()["data"]
    assert [r["employee_code"] for r in body["rows"]] == ["Gresigned"]
    # lọc theo nhóm
    body = _get(client, SUM + "/rows", metric="active_total", group_by="department",
                group_key=str(dept)).json()["data"]
    assert body["total"] == 8
    body = _get(client, SUM + "/rows", metric="missing_department", group_by="department",
                group_key="").json()["data"]
    assert "Gnodept" in {r["employee_code"] for r in body["rows"]}              # nhóm «(Chưa gắn)»


@pytest.mark.parametrize("metric", ["missing_dob", "no_account", "complete", "complete_rate", "salary", ""])
def test_rows_chi_so_khong_co_quyen_hoac_la_422(db, world, client_as, metric):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)      # không nhạy cảm, không tài khoản
    assert _get(client, SUM + "/rows", metric=metric).status_code == 422


def test_rows_nhom_gop_422(db, world, client_as):
    _, client = _actor(db, world, client_as)
    r = _get(client, SUM + "/rows", metric="active_total", group_by="department", group_key="__other__")
    assert r.status_code == 422


def test_department_id_rac_422_va_export_xlsx(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as, sensitive=True, account=True)
    assert _get(client, department_id="abc").status_code == 422
    resp = _get(client, SUM + "/export", department_id=world.dept["B.hc"])
    assert resp.status_code == 200 and resp.content[:2] == b"PK"
    assert "spreadsheetml" in resp.headers["content-type"]


def test_pham_vi_dept_va_department_id_chi_thu_hep(db, world, client_as):
    _emp(db, world, "pvB")                                                     # phòng B.hc
    _emp(db, world, "pvA", company_id=world.co["A"], department_id=world.dept["A.kt"])
    db.commit()
    _, client = _actor(db, world, client_as, scope="dept")                     # a1 thuộc A.kt
    codes = lambda **kw: {r["employee_code"] for r in _get(                      # noqa: E731
        client, SUM + "/rows", metric="active_total", **kw).json()["data"]["rows"]}
    got = codes()
    assert "GpvA" in got and "GpvB" not in got
    assert "GpvA" not in codes(department_id=world.dept["B.hc"])               # chỉ thu hẹp, không mở sang B.hc


@pytest.mark.parametrize("suffix", ["", "/export", "/rows"])
def test_chua_giao_bao_cao_403_ca_ba_duong(db, world, client_as, suffix):
    _, client = _actor(db, world, client_as, report=False)
    assert _get(client, SUM + suffix, metric="active_total").status_code == 403


def test_so_truy_van_khong_tang_theo_so_nhan_su(db, world):
    world.grant("a1", "employee", "all", actions=("read",))
    world.grant("a1", "employee_sensitive", "all", actions=("read",))
    world.grant("a1", "user", "all", actions=("read",))
    actor = world.actor("a1")
    prof = actor.profile()
    period = parse_period({"preset": "this_month", "compare": "previous"})

    def count() -> int:
        stmts: list[str] = []

        def listener(conn, cur, stmt, *args):
            stmts.append(stmt)

        engine = db.get_bind()
        event.listen(engine, "before_cursor_execute", listener)
        try:
            svc.build_summary(db, apply_scope(db.query(Employee), Employee, "employee", actor.user, prof),
                              period, "department", with_sensitive=True, with_account=True)
        finally:
            event.remove(engine, "before_cursor_execute", listener)
        return len(stmts)

    def add(n, start):
        for i in range(n):
            e = _emp(db, world, f"q{start + i}")
            _user(db, e, role=(i % 2 == 0))
        db.commit()

    add(5, 0)
    c5 = count()
    add(45, 5)
    c50 = count()
    assert c5 > 0 and c5 == c50, (c5, c50)
