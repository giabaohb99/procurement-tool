"""duoc-CR-689 — báo cáo E2 «Yêu cầu sửa hồ sơ» (khóa 27): `/api/profile-change-report/summary`.

Canh: định nghĩa từng chỉ số (yêu cầu · chờ · chờ quá 2 ngày · duyệt · từ chối · tỷ lệ từ chối · giờ xử lý),
chiều «Trường bị xin sửa» (một yêu cầu nhiều trường), KHÔNG lộ giá trị cũ / mới ở cả summary lẫn rows,
phạm vi dữ liệu, gác khóa báo cáo ở CẢ ba đường, 422, xlsx và số truy vấn CỐ ĐỊNH.
"""
import uuid
from datetime import date, datetime, timedelta

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
from app.modules.employee import change_request_report_service as svc
from app.modules.employee.change_request_model import EmployeeChangeRequest as Req
from app.modules.employee.model import Employee
from app.modules.report_access.model import ReportAccess
from app.modules.user.model import User

TODAY = vn_today()
SUM = "/api/profile-change-report/summary"
SECRET_OLD, SECRET_NEW = "OLD-SECRET-079090123456", "NEW-SECRET-079090999999"
QS = {"preset": "custom", "date_from": (TODAY - timedelta(days=30)).isoformat(), "date_to": TODAY.isoformat(),
      "compare": "none"}
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


def _emp(db, world, tag, **kw) -> Employee:
    base = dict(code=f"Y{tag}", full_name=f"Người {tag}", company_id=world.co["B"],
                department_id=world.dept["B.hc"], is_active=True)
    base.update(kw)
    e = Employee(**base)
    db.add(e)
    db.flush()
    return e


def _item(field, group="documents"):
    return {"group": group, "field": field, "before": SECRET_OLD, "after": SECRET_NEW}


def _req(db, emp, status, days_ago, fields, *, hours=None, families=False, decided_by=0) -> Req:
    created = datetime.utcnow() - timedelta(days=days_ago)
    r = Req(employee_id=emp.id, status=status, changes=[_item(f) for f in fields],
            families={"before": [{"full_name": SECRET_OLD}], "after": [{"full_name": SECRET_NEW}]} if families else None,
            created_at=created, decided_at=created + timedelta(hours=hours) if hours is not None else None,
            decided_by=decided_by)
    db.add(r)
    db.flush()
    return r


def _dataset(db, world):
    e1, e2, e3, e4, e5, e6 = (_emp(db, world, i) for i in range(1, 7))
    boss = User(email="duyet@t.vn", employee_id=_emp(db, world, "boss", full_name="Chị Duyệt").id,
                password_hash="x", is_active=True)
    db.add(boss)
    db.flush()
    _req(db, e1, 1, 0, ["date_of_birth", "bank_account_no"])                       # chờ, mới gửi
    _req(db, e2, 1, 5, ["id_number"], families=True)                               # chờ quá 2 ngày, 2 khóa
    _req(db, e3, 2, 3, ["tax_code"], hours=24, decided_by=boss.id)                 # duyệt sau 24 giờ
    _req(db, e4, 3, 4, ["bank_account_no"], hours=48, decided_by=boss.id)          # từ chối sau 48 giờ
    _req(db, e5, 4, 2, ["tax_code"])                                               # rút lại
    _req(db, e6, 2, 100, ["tax_code"], hours=1)                                    # ngoài kỳ
    db.commit()


def _actor(db, world, client_as, *, scope="all", report=True, key="a1", actions=("read", "write", "export")):
    world.grant(key, "employee", scope, actions=actions)
    actor = world.actor(key)
    if report:
        db.add(ReportAccess(report_key=int(ReportKey.PROFILE_CHANGES), subject_kind=SUBJECT_EMPLOYEE,
                            subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
        db.commit()
    return actor, client_as(actor.user)


def _get(client, path=SUM, **extra):
    return client.get(path, params={**QS, "department_id": extra.pop("department_id", ""), **extra})


def test_chi_so_dinh_nghia_dung(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    resp = _get(client, department_id=world.dept["B.hc"])
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    cur = data["totals"]["current"]
    assert cur["requests"] == 5 and cur["pending"] == 2 and cur["pending_over_2d"] == 1
    assert cur["approved"] == 1 and cur["rejected"] == 1
    assert cur["reject_rate"] == pytest.approx(50.0) and cur["turnaround_hours"] == pytest.approx(36.0)
    assert data["meta"]["drilldown_metrics"] == ["requests", "pending", "pending_over_2d", "approved", "rejected"]
    derived = {m["key"]: m["kind"] for m in data["meta"]["metrics"]}
    assert derived["turnaround_hours"] == "hours" and derived["reject_rate"] == "percent"
    assert SECRET_OLD not in resp.text and SECRET_NEW not in resp.text


def test_xem_theo_truong_va_trang_thai(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    by_field = _get(client, group_by="field", department_id=world.dept["B.hc"]).json()["data"]
    got = {g["label"]: g["current"]["requests"] for g in by_field["groups"]}
    assert got["Số tài khoản"] == 2 and got["Mã số thuế"] == 2 and got["Ngày sinh"] == 1
    assert got["Số CCCD"] == 1 and got["Hộ gia đình"] == 1                       # 1 yêu cầu nhiều khóa
    assert by_field["totals"]["current"]["requests"] == 5                         # tổng vẫn đếm một lần
    by_status = _get(client, group_by="status", department_id=world.dept["B.hc"]).json()["data"]
    assert {g["label"]: g["current"]["requests"] for g in by_status["groups"]} == {
        "Chờ duyệt": 2, "Đã duyệt": 1, "Từ chối": 1, "Đã rút lại": 1}
    assert _get(client, group_by="department").status_code == 200
    assert _get(client, group_by="khong-co").status_code == 422


def test_rows_khong_tra_gia_tri_va_khop_con_so(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    resp = _get(client, SUM + "/rows", metric="pending", department_id=world.dept["B.hc"])
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert [c["key"] for c in data["columns"]] == ["employee_code", "employee_name", "department", "created_date",
                                                    "status", "field_count", "decided_by_name", "decided_date"]
    assert data["total"] == 2 and {r["employee_code"] for r in data["rows"]} == {"Y1", "Y2"}
    assert {r["field_count"] for r in data["rows"]} == {2}                       # Y1: 2 trường · Y2: 1 trường + hộ GĐ
    assert SECRET_OLD not in resp.text and SECRET_NEW not in resp.text
    done = _get(client, SUM + "/rows", metric="approved", department_id=world.dept["B.hc"]).json()["data"]["rows"]
    assert done[0]["decided_by_name"] == "Chị Duyệt" and done[0]["decided_date"] and done[0]["status"] == "Đã duyệt"
    over = _get(client, SUM + "/rows", metric="pending_over_2d", department_id=world.dept["B.hc"]).json()["data"]
    assert [r["employee_code"] for r in over["rows"]] == ["Y2"]
    grp = _get(client, SUM + "/rows", metric="requests", group_by="field", group_key="tax_code",
               department_id=world.dept["B.hc"]).json()["data"]
    assert grp["total"] == 2


def test_rows_422(db, world, client_as):
    _, client = _actor(db, world, client_as)
    assert _get(client, SUM + "/rows", metric="khong-co").status_code == 422
    assert _get(client, SUM + "/rows").status_code == 422
    assert _get(client, SUM + "/rows", metric="requests", group_by="field", group_key="__other__").status_code == 422
    assert _get(client, department_id="abc").status_code == 422


def test_export_xlsx(db, world, client_as):
    _dataset(db, world)
    _, client = _actor(db, world, client_as)
    resp = _get(client, SUM + "/export", department_id=world.dept["B.hc"])
    assert resp.status_code == 200 and resp.content[:2] == b"PK"
    assert "spreadsheetml" in resp.headers["content-type"]


def test_pham_vi_va_department_chi_thu_hep(db, world, client_as):
    b = _emp(db, world, "pvB")
    a = _emp(db, world, "pvA", company_id=world.co["A"], department_id=world.dept["A.kt"])
    _req(db, b, 1, 1, ["tax_code"])
    _req(db, a, 1, 1, ["tax_code"])
    db.commit()
    _, client = _actor(db, world, client_as, scope="dept")                      # a1 thuộc A.kt
    codes = lambda **kw: {r["employee_code"] for r in _get(                      # noqa: E731
        client, SUM + "/rows", metric="requests", **kw).json()["data"]["rows"]}
    assert codes() == {"YpvA"}
    assert codes(department_id=world.dept["B.hc"]) == set()                      # chỉ thu hẹp, không mở sang B.hc


@pytest.mark.parametrize("suffix, actions, status", [
    ("", ("read", "export"), 403), ("/export", ("read", "export"), 403), ("/rows", ("read", "export"), 403),
    ("", ("write",), 200), ("/rows", ("write",), 200), ("/export", ("write",), 403),     # xuất cần thêm export
    ("/export", ("write", "export"), 200),
])
def test_chi_nguoi_duyet_ho_so_moi_xem_duoc_bao_cao(db, world, client_as, suffix, actions, status):
    """Yêu cầu sửa hồ sơ chứa giá trị cũ / mới — cùng khóa `employee.write` với màn duyệt (đường xuất cần thêm export)."""
    _, client = _actor(db, world, client_as, actions=actions)
    assert _get(client, SUM + suffix, metric="requests").status_code == status


def test_pham_vi_theo_hanh_dong_write_nhu_man_duyet(db, world, client_as):
    b = _emp(db, world, "wB")
    a = _emp(db, world, "wA", company_id=world.co["A"], department_id=world.dept["A.kt"])
    _req(db, b, 1, 1, ["tax_code"])
    _req(db, a, 1, 1, ["tax_code"])
    db.commit()
    world.grant("a1", "employee", "all", actions=("read", "export"))                # đọc được cả hai, nhưng KHÔNG duyệt
    world.grant("a1", "employee", "dept", actions=("write", "export"))              # duyệt trong phòng mình
    actor = world.actor("a1")
    db.add(ReportAccess(report_key=int(ReportKey.PROFILE_CHANGES), subject_kind=SUBJECT_EMPLOYEE,
                        subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
    db.commit()
    client = client_as(actor.user)
    rows = _get(client, SUM + "/rows", metric="requests").json()["data"]["rows"]
    assert {r["employee_code"] for r in rows} == {"YwA"}


@pytest.mark.parametrize("suffix", ["", "/export", "/rows"])
def test_chua_giao_bao_cao_403_ca_ba_duong(db, world, client_as, suffix):
    _, client = _actor(db, world, client_as, report=False)
    assert _get(client, SUM + suffix, metric="requests").status_code == 403


def test_so_truy_van_khong_tang_theo_so_yeu_cau(db, world):
    world.grant("a1", "employee", "all", actions=("read",))
    actor = world.actor("a1")
    prof = actor.profile()
    period = parse_period(QS)

    def count() -> int:
        stmts: list[str] = []
        listener = lambda conn, cur, stmt, *a: stmts.append(stmt)               # noqa: E731
        engine = db.get_bind()
        event.listen(engine, "before_cursor_execute", listener)
        try:
            q = apply_scope(db.query(Employee), Employee, "employee", actor.user, prof)
            svc.build_summary(db, q, period, "field")
            svc.build_rows(db, q, period, "requests", "department", None)
        finally:
            event.remove(engine, "before_cursor_execute", listener)
        return len(stmts)

    def add(n, start):
        for i in range(n):
            _req(db, _emp(db, world, f"q{start + i}"), 1 + i % 3, i % 5, ["tax_code", "id_number"], hours=3)
        db.commit()

    add(3, 0)
    c3 = count()
    add(12, 3)
    assert count() == c3
