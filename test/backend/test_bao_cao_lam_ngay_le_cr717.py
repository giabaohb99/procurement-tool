"""duoc-CR-717 — báo cáo "Làm việc vào ngày lễ, ngày nghỉ" (khóa 30): `/api/holiday-work-report/summary` (+ export, rows).

Canh: nguồn phiếu nghỉ bù (mặc định Đã duyệt; `include_pending` thêm Chờ duyệt; nháp / từ chối / trả về / hủy / xóa
không bao giờ), phân loại ngày lễ ↔ ngày nghỉ theo lịch (ngày lễ riêng pháp nhân khác không áp), phạm vi, gác khóa
báo cáo ở cả ba đường, `/rows`, xuất Excel, trần kỳ 366 ngày và số truy vấn CỐ ĐỊNH.
"""
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.scoping import apply_scope
from app.core.subject_match import SUBJECT_EMPLOYEE
from app.main import app
from app.modules.employee.model import Employee
from app.modules.leave import holiday_work_report_service as service
from app.modules.leave.catalog_model import Holiday
from app.modules.leave.comp_request_model import LeaveCompRequest
from app.modules.leave.constants import LeaveCompStatus as S
from app.modules.report_access.model import ReportAccess

BASE = "/api/holiday-work-report/summary"
P = {"preset": "custom", "date_from": "2026-09-01", "date_to": "2026-09-30", "compare": "none"}
HOLIDAY, SUNDAY, SUNDAY2 = date(2026, 9, 2), date(2026, 9, 6), date(2026, 9, 13)
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


def _emp(db, world, tag, dept="B.hc", co="B") -> Employee:
    e = Employee(code=f"H{tag}", full_name=f"Người {tag}", company_id=world.co[co],
                 department_id=world.dept[dept], is_active=True, hire_date=date(2026, 1, 1))
    db.add(e)
    db.flush()
    return e


def _comp(db, world, emp, day, status=S.APPROVED, days=1.0, dept="B.hc", co="B", deleted=False) -> LeaveCompRequest:
    _seq["n"] += 1
    r = LeaveCompRequest(code=f"NB{_seq['n']:05d}", company_id=world.co[co], department_id=world.dept[dept],
                         employee_id=emp.id, work_date=day, days=days, status=int(status), is_deleted=deleted,
                         active_key=f"{emp.id}:{day}:{_seq['n']}")
    db.add(r)
    db.flush()
    return r


def _actor(db, world, client_as, scope="all", report=True, key="a1"):
    world.grant(key, "leave_comp_request", scope, actions=("read", "export"))
    actor = world.actor(key)
    if report:
        db.add(ReportAccess(report_key=int(ReportKey.HOLIDAY_WORK), subject_kind=SUBJECT_EMPLOYEE,
                            subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
        db.commit()
    return actor, client_as(actor.user)


def _get(client, path=BASE, **extra):
    return client.get(path, params={**P, **extra})


def _setup(db, world):
    """Lễ 02/09 (dùng chung); e1 có phiếu: lễ, CN (nghỉ theo lịch), CN chờ duyệt + 4 phiếu KHÔNG hợp lệ."""
    db.add(Holiday(company_id=0, date=HOLIDAY, name="Quốc khánh", is_recurring=False, is_active=True))
    e1, e2 = _emp(db, world, "1"), _emp(db, world, "2")
    _comp(db, world, e1, HOLIDAY, days=1)
    _comp(db, world, e1, SUNDAY, days=0.5)
    _comp(db, world, e2, HOLIDAY, days=1)
    _comp(db, world, e2, SUNDAY2, S.PENDING)
    for st in (S.DRAFT, S.REJECTED, S.RETURNED, S.CANCELLED):
        _comp(db, world, e2, date(2026, 9, 20), st)
    _comp(db, world, e2, date(2026, 9, 27), S.APPROVED, deleted=True)
    db.commit()
    return e1, e2


def test_phan_loai_va_chi_so_mac_dinh_chi_da_duyet(db, world, client_as):
    _setup(db, world)
    _, client = _actor(db, world, client_as)
    resp = _get(client)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    cur = data["totals"]["current"]
    assert (cur["lines"], cur["holiday_lines"], cur["offday_lines"], cur["people"]) == (3, 2, 1, 2)
    assert cur["comp_days"] == pytest.approx(2.5)
    assert "pending_lines" not in cur and "pending_lines" not in [m["key"] for m in data["meta"]["metrics"]]
    assert data["meta"]["drilldown_metrics"] == ["lines"]
    assert sum(t["current"]["lines"] for t in data["trend"]) == 3


def test_include_pending_them_phieu_cho_duyet_va_chi_so_dang_cho(db, world, client_as):
    _setup(db, world)
    _, client = _actor(db, world, client_as)
    data = _get(client, include_pending="true").json()["data"]
    cur = data["totals"]["current"]
    assert cur["lines"] == 4 and cur["pending_lines"] == 1 and cur["offday_lines"] == 2
    assert cur["comp_days"] == pytest.approx(2.5)                   # ngày bù chỉ tính phiếu Đã duyệt
    assert "pending_lines" in [m["key"] for m in data["meta"]["metrics"]]


def test_day_kind_loc_va_gia_tri_la_422(db, world, client_as):
    _setup(db, world)
    _, client = _actor(db, world, client_as)
    assert _get(client, day_kind=1).json()["data"]["totals"]["current"]["lines"] == 2
    assert _get(client, day_kind=2).json()["data"]["totals"]["current"]["lines"] == 1
    assert _get(client, day_kind=0).json()["data"]["totals"]["current"]["lines"] == 3
    assert _get(client, day_kind=3).status_code == 422


def test_ngay_le_rieng_phap_nhan_khac_khong_ap(db, world, client_as):
    e1, _ = _setup(db, world)
    #  Lễ riêng của pháp nhân A vào 06/09 — e1 thuộc pháp nhân B nên 06/09 vẫn là "ngày nghỉ theo lịch".
    db.add(Holiday(company_id=world.co["A"], date=SUNDAY, name="Lễ riêng A", is_recurring=False, is_active=True))
    db.commit()
    _, client = _actor(db, world, client_as)
    assert _get(client).json()["data"]["totals"]["current"]["holiday_lines"] == 2
    ea = _emp(db, world, "a", dept="A.kt", co="A")
    _comp(db, world, ea, SUNDAY, dept="A.kt", co="A")
    db.commit()
    cur = _get(client).json()["data"]["totals"]["current"]
    assert cur["holiday_lines"] == 3 and cur["offday_lines"] == 1
    names = {g["label"] for g in _get(client, group_by="holiday_name").json()["data"]["groups"]}
    assert {"Quốc khánh", "Lễ riêng A"} <= names


def test_nhom_theo_phong_ban_nhan_su_loai_ngay_va_bo_loc(db, world, client_as):
    _, e2 = _setup(db, world)
    ek = _emp(db, world, "k", dept="B.kt")
    _comp(db, world, ek, HOLIDAY, dept="B.kt")
    db.commit()
    _, client = _actor(db, world, client_as)
    by = {g["label"]: g["current"]["lines"] for g in _get(client, group_by="department").json()["data"]["groups"]}
    assert by == {"Phòng Hành chính": 3, "Phòng Kế toán": 1}
    assert len(_get(client, group_by="employee").json()["data"]["groups"]) == 3
    kinds = {g["label"]: g["current"]["lines"] for g in _get(client, group_by="day_kind").json()["data"]["groups"]}
    assert kinds == {"Ngày lễ": 3, "Ngày nghỉ theo lịch": 1}
    assert _get(client, group_by="company").json()["data"]["groups"][0]["current"]["lines"] == 4
    assert _get(client, group_by="bogus").status_code == 422
    only = _get(client, department_id=world.dept["B.kt"]).json()["data"]["totals"]["current"]["lines"]
    assert only == 1
    assert _get(client, company_id=world.co["A"]).json()["data"]["totals"]["current"]["lines"] == 0


def test_phamvi_dept_khong_thay_phong_khac(db, world, client_as):
    _setup(db, world)
    ea = _emp(db, world, "a", dept="A.kt", co="A")
    _comp(db, world, ea, HOLIDAY, dept="A.kt", co="A")
    db.commit()
    _, client = _actor(db, world, client_as, scope="dept")        # a1 ở A.kt
    assert _get(client).json()["data"]["totals"]["current"]["lines"] == 1


@pytest.mark.parametrize("suffix", ["", "/export", "/rows"])
def test_chua_giao_khoa_30_thi_403_ca_ba_duong(db, world, client_as, suffix):
    _, client = _actor(db, world, client_as, report=False)
    assert _get(client, BASE + suffix, metric="lines").status_code == 403


def test_rows_khop_so_luot_va_loc_theo_nhom(db, world, client_as):
    _setup(db, world)
    ek = _emp(db, world, "k", dept="B.kt")
    _comp(db, world, ek, HOLIDAY, dept="B.kt")
    db.commit()
    _, client = _actor(db, world, client_as)
    rows = _get(client, BASE + "/rows", metric="lines").json()["data"]
    assert [c["key"] for c in rows["columns"]] == [
        "employee_code", "employee_name", "department", "work_date", "weekday", "day_kind", "holiday_name",
        "days", "status", "code"]
    assert rows["total"] == 4 and rows["truncated"] is False
    first = rows["rows"][0]
    assert first["work_date"] == "2026-09-02" and first["day_kind"] == "Ngày lễ" and first["holiday_name"] == "Quốc khánh"
    assert first["weekday"] == "Thứ 4" and first["status"] == "Đã duyệt"
    sunday = next(r for r in rows["rows"] if r["work_date"] == "2026-09-06")
    assert sunday["weekday"] == "Chủ nhật" and sunday["day_kind"] == "Ngày nghỉ theo lịch" and sunday["days"] == 0.5
    grp = _get(client, BASE + "/rows", metric="lines", group_by="department",
               group_key=str(world.dept["B.kt"])).json()["data"]
    assert grp["total"] == 1 and grp["rows"][0]["employee_code"] == "Hk"
    pend = _get(client, BASE + "/rows", metric="lines", include_pending="1").json()["data"]
    assert pend["total"] == 5 and "Chờ duyệt" in {r["status"] for r in pend["rows"]}
    for bad in ({"metric": "people"}, {}, {"metric": "lines", "group_by": "department", "group_key": "__other__"}):
        assert _get(client, BASE + "/rows", **bad).status_code == 422


def test_export_xlsx(db, world, client_as):
    _setup(db, world)
    _, client = _actor(db, world, client_as)
    r = _get(client, BASE + "/export", group_by="department", include_pending="true")
    assert r.status_code == 200 and "spreadsheetml" in r.headers["content-type"]
    import io
    from openpyxl import load_workbook
    ws = load_workbook(io.BytesIO(r.content)).active
    header = [c.value for c in ws[1]]
    assert header[0] == "Phòng ban" and {"Lượt đi làm", "Trong đó ngày lễ", "Ngày nghỉ theo lịch", "Số người",
                                           "Ngày nghỉ bù được duyệt", "Đang chờ duyệt"} <= set(header)


def test_ky_qua_366_ngay_la_422_ca_ba_duong(db, world, client_as):
    _, client = _actor(db, world, client_as)
    long = {"date_from": "2025-01-01", "date_to": "2026-06-30"}
    assert _get(client, **long).status_code == 422
    assert _get(client, BASE + "/rows", metric="lines", **long).status_code == 422
    assert _get(client, BASE + "/export", **long).status_code == 422
    assert _get(client, date_from="2025-09-01", date_to="2026-08-31").status_code == 200   # đúng 365 ngày


def test_so_truy_van_khong_tang_theo_so_phieu_va_phap_nhan(db, world):
    world.grant("a1", "leave_comp_request", "all", actions=("read",))
    actor = world.actor("a1")
    prof = actor.profile()
    period = parse_period({**P, "compare": "previous"})
    db.add(Holiday(company_id=0, date=HOLIDAY, name="Quốc khánh", is_recurring=False, is_active=True))
    db.add(Holiday(company_id=world.co["A"], date=SUNDAY, name="Lễ riêng A", is_recurring=False, is_active=True))
    db.commit()

    def count() -> int:
        stmts: list[str] = []

        def listener(conn, cur, stmt, *args):
            stmts.append(stmt)

        eng = db.get_bind()
        event.listen(eng, "before_cursor_execute", listener)
        try:
            service.build_summary(db, apply_scope(db.query(LeaveCompRequest), LeaveCompRequest, "leave_comp_request",
                                                  actor.user, prof), period, "department", True, 0)
            service.build_rows(db, apply_scope(db.query(LeaveCompRequest), LeaveCompRequest, "leave_comp_request",
                                               actor.user, prof), period, "lines", None, None, True, 0)
        finally:
            event.remove(eng, "before_cursor_execute", listener)
        return len(stmts)

    def add(n, start, cos):
        for i in range(n):
            co = cos[i % len(cos)]
            dept = "A.kt" if co == "A" else "B.hc"
            e = _emp(db, world, f"q{start + i}", dept=dept, co=co)
            _comp(db, world, e, HOLIDAY if i % 2 else SUNDAY, S.APPROVED if i % 3 else S.PENDING, dept=dept, co=co)
        db.commit()

    add(1, 0, ["B"])
    c1 = count()
    add(24, 1, ["A", "B", "A"])
    assert c1 > 0 and c1 == count()
