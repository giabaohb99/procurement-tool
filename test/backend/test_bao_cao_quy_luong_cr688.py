"""duoc-CR-688 / CR-693 — báo cáo A5 «Quỹ lương theo pháp nhân» (khóa 21): `/api/payroll-fund/summary` (+ export, rows).

Từ duoc-CR-693 nguồn số là Ô LƯƠNG TRÊN HỒ SƠ nhân sự (không đọc hợp đồng nữa). Canh: chọn người (đang làm, có lương),
chỉ số, phạm vi theo `employee`, che nhóm < 3 người (kể cả với người xem mọi phạm vi) + che phụ + che Tổng 1–2 người,
ảnh chụp (không kỳ so sánh, không xu hướng), danh sách KHÔNG có cột tiền (403 với nhóm bị che), gác khóa báo cáo ở cả
ba đường, xlsx không lộ lương từng người, số truy vấn CỐ ĐỊNH.
"""
import uuid
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import event

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.scoping import apply_scope
from app.core.subject_match import SUBJECT_EMPLOYEE
from app.main import app
from app.modules.employee.model import Employee
from app.modules.labor_contract import payroll_report_service as service
from app.modules.report_access.model import ReportAccess

BASE = "/api/payroll-fund/summary"
P = {"preset": "custom", "date_from": "2026-06-01", "date_to": "2026-08-31", "compare": "none"}


@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _emp(db, world, tag, dept="B.hc", co="B", salary=10_000_000, allow=1_000_000, **kw) -> Employee:
    kw.setdefault("is_active", True)
    e = Employee(code=f"Q{tag}", full_name=f"Người {tag}", company_id=world.co[co],
                 department_id=world.dept[dept], salary_monthly=salary, allowance_monthly=allow, **kw)
    db.add(e)
    db.flush()
    return e


def _people(db, world, n, prefix, pos="", **kw):
    return [_emp(db, world, f"{prefix}{i}", position=pos, **kw) for i in range(n)]


def _actor(db, world, client_as, scope="all", report=True, entity="employee"):
    world.grant("a1", entity, scope, actions=("read", "export"))
    actor = world.actor("a1")
    if report:
        db.add(ReportAccess(report_key=int(ReportKey.PAYROLL_FUND), subject_kind=SUBJECT_EMPLOYEE,
                            subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
        db.commit()
    return actor, client_as(actor.user)


def _get(client, path=BASE, **extra):
    return client.get(path, params={**P, "department_id": extra.pop("department_id", ""), **extra})


def test_chon_nguoi_va_chi_so(db, world, client_as):
    _people(db, world, 3, "ok")                                           # 3 người đủ điều kiện
    _emp(db, world, "over", salary=20_000_000, allow=0)
    _emp(db, world, "onlyallow", salary=0, allow=2_000_000)               # chỉ có phụ cấp vẫn là «có lương»
    # loại khỏi quỹ: người nghỉ việc · ngừng hoạt động
    _emp(db, world, "res", status="resigned")
    _emp(db, world, "off", is_active=False)
    # đang làm nhưng CHƯA nhập lương: không tính vào quỹ lương, đếm riêng
    _emp(db, world, "nosal1", salary=0, allow=0)
    _emp(db, world, "nosal2", salary=0, allow=0)
    db.commit()
    _, client = _actor(db, world, client_as)
    resp = _get(client, department_id=world.dept["B.hc"])
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    cur = data["totals"]["current"]
    assert cur["people_paid"] == 5
    assert cur["base_total"] == 3 * 10_000_000 + 20_000_000
    assert cur["allowance_total"] == 3 * 1_000_000 + 2_000_000
    assert cur["payroll_total"] == cur["base_total"] + cur["allowance_total"]
    assert cur["avg_payroll"] == round(cur["payroll_total"] / 5)
    assert data["meta"]["people_without_salary"] == 2
    assert any("2 người còn làm chưa nhập lương" in n for n in data["notes"])
    assert [m["key"] for m in data["meta"]["metrics"]] == [
        "people_paid", "base_total", "allowance_total", "payroll_total", "avg_payroll"]


def test_nguon_la_o_ho_so_khong_phai_hop_dong(db, world, client_as):
    """Hợp đồng đã ký mà ô hồ sơ chưa có lương -> KHÔNG vào quỹ lương."""
    from app.modules.labor_contract.model import LaborContract
    from datetime import date
    e = _emp(db, world, "hd", salary=0, allow=0)
    db.add(LaborContract(code="QLX1", employee_id=e.id, company_id=e.company_id, department_id=e.department_id,
                         contract_type=2, status=2, start_date=date(2026, 1, 1), base_salary=99_000_000,
                         allowance=1, insurance_salary=0))
    db.commit()
    _, client = _actor(db, world, client_as)
    cur = _get(client, department_id=world.dept["B.hc"]).json()["data"]["totals"]["current"]
    assert cur["people_paid"] == 0 and cur["payroll_total"] == 0


def test_nhom_theo_chieu(db, world, client_as):
    _people(db, world, 3, "b", pos="Kế toán")
    _people(db, world, 4, "a", dept="A.kt", co="A", pos="Kỹ thuật")
    db.commit()
    _, client = _actor(db, world, client_as)
    for gb in ("company", "department", "position", "job_category"):
        r = _get(client, group_by=gb)
        assert r.status_code == 200, (gb, r.text)
        assert sum(g["current"]["people_paid"] or 0 for g in r.json()["data"]["groups"]) == 7
    assert _get(client, group_by="bogus").status_code == 422
    assert _get(client, group_by="contract_type").status_code == 422      # chiều «Loại HĐ» đã bỏ
    groups = {g["key"]: g for g in _get(client, group_by="company").json()["data"]["groups"]}
    assert groups[str(world.co["B"])]["current"]["payroll_total"] == 3 * 11_000_000


def test_tong_bang_cong_cac_nhom(db, world, client_as):
    _people(db, world, 3, "hc")
    _people(db, world, 3, "kt", dept="B.kt", salary=12_000_000)
    _people(db, world, 4, "ak", dept="A.kt", co="A", salary=8_000_000)
    db.commit()
    _, client = _actor(db, world, client_as)
    total = _get(client).json()["data"]["totals"]["current"]
    assert total["people_paid"] == 10
    assert total["payroll_total"] == 3 * 11_000_000 + 3 * 13_000_000 + 4 * 9_000_000
    for gb in ("department", "company"):
        groups = _get(client, group_by=gb).json()["data"]["groups"]
        assert sum(g["current"]["payroll_total"] for g in groups) == total["payroll_total"]


def test_pham_vi_dept_va_department_id_chi_thu_hep(db, world, client_as):
    _people(db, world, 2, "own", dept="A.kt", co="A")
    _people(db, world, 2, "oth")
    db.commit()
    _, client = _actor(db, world, client_as, scope="dept")
    assert _get(client).json()["data"]["totals"]["current"]["people_paid"] == 2
    assert _get(client, department_id=world.dept["B.hc"]).json()["data"]["totals"]["current"]["people_paid"] == 0
    assert _get(client, department_id="abc").status_code == 422


def test_che_nhom_nho_ca_voi_nguoi_xem_moi_pham_vi(db, world, client_as):
    _people(db, world, 5, "big", pos="Lớn")
    _people(db, world, 1, "one", pos="Một")
    _people(db, world, 2, "two", pos="Hai")
    db.commit()
    _, client = _actor(db, world, client_as, scope="all")
    data = _get(client, group_by="position").json()["data"]
    g = {x["label"]: x for x in data["groups"]}
    for name in ("Một", "Hai"):
        assert g[name]["suppressed"] is True and all(v is None for v in g[name]["current"].values())
    assert g["Lớn"]["current"]["people_paid"] == 5 and not g["Lớn"].get("suppressed")
    assert data["totals"]["current"]["people_paid"] == 8
    assert any("dưới 3 người" in n for n in data["notes"])
    assert not any("che thêm" in n for n in data["notes"])    # 2 nhóm, 3 người: đủ, không che phụ


def test_chi_con_mot_nhom_nho_bo_ca_bang_nhom_va_403_danh_sach(db, world, client_as):
    _people(db, world, 2, "two", pos="Hai")
    db.commit()
    _, client = _actor(db, world, client_as)
    data = _get(client, group_by="position", department_id=world.dept["B.hc"]).json()["data"]
    assert data["groups"] == [] and data["totals"]["current"]["people_paid"] == 2
    assert any("Không đủ người để xem theo Chức vụ" in n for n in data["notes"])
    r = _get(client, BASE + "/rows", metric="people_paid", group_by="position", group_key="Hai",
             department_id=world.dept["B.hc"])
    assert r.status_code == 403


def test_tong_chi_1_2_nguoi_che_so_tien(db, world, client_as):
    _people(db, world, 2, "two")
    db.commit()
    _, client = _actor(db, world, client_as)
    data = _get(client, department_id=world.dept["B.hc"]).json()["data"]
    cur = data["totals"]["current"]
    assert cur["people_paid"] == 2
    assert all(cur[k] is None for k in ("base_total", "allowance_total", "payroll_total", "avg_payroll"))
    assert any("dưới 3 người có lương" in n for n in data["notes"])


def test_che_phu_khi_chi_mot_nhom_nho(db, world, client_as):
    _people(db, world, 6, "big", pos="Lớn")
    _people(db, world, 3, "mid", pos="Vừa")
    _people(db, world, 1, "one", pos="Một")
    db.commit()
    _, client = _actor(db, world, client_as)
    g = {x["label"]: x for x in _get(client, group_by="position").json()["data"]["groups"]}
    assert g["Một"]["suppressed"] and g["Vừa"]["suppressed"]       # che thêm nhóm nhỏ nhất còn hiện
    assert g["Lớn"]["current"]["people_paid"] == 6


def test_anh_chup_khong_ky_so_sanh_khong_xu_huong(db, world, client_as):
    _people(db, world, 3, "a")
    db.commit()
    _, client = _actor(db, world, client_as)
    data = client.get(BASE, params={**P, "compare": "previous", "department_id": ""}).json()["data"]
    assert data["totals"]["compare"] is None and data["trend"] == []
    assert data["period"]["date_from"] == "2026-06-01"          # kỳ vẫn được trả lại
    assert any("ảnh chụp" in n for n in data["notes"])


def test_rows_khong_co_cot_tien_va_khop_so(db, world, client_as):
    _people(db, world, 4, "big", pos="Lớn", salary=12_345_678, allow=777_000)
    _people(db, world, 1, "one", pos="Một")
    _people(db, world, 2, "two", pos="Hai")
    _emp(db, world, "none", salary=0, allow=0)                   # chưa nhập lương: không nằm trong danh sách
    db.commit()
    _, client = _actor(db, world, client_as)
    resp = _get(client, BASE + "/rows", metric="people_paid", department_id=world.dept["B.hc"])
    rows = resp.json()["data"]
    assert rows["total"] == 7
    assert [c["key"] for c in rows["columns"]] == ["employee_code", "employee_name", "company", "department", "position"]
    assert "12345678" not in resp.text and "777000" not in resp.text      # không số tiền nào lọt
    assert all(set(r) == {"employee_code", "employee_name", "company", "department", "position", "link"}
               for r in rows["rows"])
    assert all(r["link"].startswith("/hr/employees/") for r in rows["rows"])
    ok = _get(client, BASE + "/rows", metric="people_paid", group_by="position", group_key="Lớn")
    assert ok.status_code == 200 and ok.json()["data"]["total"] == 4
    for key in ("Một", "Hai"):
        r = _get(client, BASE + "/rows", metric="people_paid", group_by="position", group_key=key)
        assert r.status_code == 403
    for bad in ({"metric": "payroll_total"}, {},
                {"metric": "people_paid", "group_by": "position", "group_key": "__other__"},
                {"metric": "people_paid", "group_by": "bogus", "group_key": "1"}):
        assert _get(client, BASE + "/rows", **bad).status_code == 422


@pytest.mark.parametrize("suffix", ["", "/export", "/rows"])
def test_chua_giao_bao_cao_403_ca_ba_duong(db, world, client_as, suffix):
    _, client = _actor(db, world, client_as, report=False)
    assert _get(client, BASE + suffix, metric="people_paid").status_code == 403


@pytest.mark.parametrize("suffix", ["", "/export", "/rows"])
def test_chi_co_quyen_labor_contract_khong_du_can_employee(db, world, client_as, suffix):
    """Đổi gác sang `employee`: chỉ có `labor_contract` (không có `employee`) -> 403 dù đã được giao báo cáo."""
    _, client = _actor(db, world, client_as, entity="labor_contract")
    assert _get(client, BASE + suffix, metric="people_paid").status_code == 403


def test_export_xlsx_nhom_bi_che_de_trong_va_khong_lo_luong_tung_nguoi(db, world, client_as):
    _people(db, world, 5, "big", pos="Lớn", salary=12_345_678, allow=0)
    _people(db, world, 1, "one", pos="Một", salary=98_765_432, allow=0)
    _people(db, world, 2, "two", pos="Hai", salary=87_654_321, allow=0)
    db.commit()
    _, client = _actor(db, world, client_as)
    r = _get(client, BASE + "/export", group_by="position")
    assert r.status_code == 200 and "spreadsheetml" in r.headers["content-type"]
    ws = load_workbook(BytesIO(r.content)).active
    rows = {row[0].value: [c.value for c in row[1:]] for row in ws.iter_rows(min_row=2)}
    assert all(v is None for v in rows["Một"]) and all(v is None for v in rows["Hai"])
    assert any(v not in (None, "", 0) for v in rows["Tổng"])
    cells = {c.value for row in ws.iter_rows() for c in row}
    assert 98_765_432 not in cells and 87_654_321 not in cells


def test_so_truy_van_khong_tang_theo_so_nhan_su(db, world):
    world.grant("a1", "employee", "all", actions=("read",))
    actor = world.actor("a1")
    prof = actor.profile()
    period = parse_period({**P, "compare": "previous"})

    def count() -> int:
        stmts: list[str] = []

        def listener(conn, cur, stmt, *args):
            stmts.append(stmt)

        eng = db.get_bind()
        event.listen(eng, "before_cursor_execute", listener)
        try:
            service.build_summary(db, apply_scope(db.query(Employee), Employee, "employee", actor.user, prof),
                                  period, "department")
        finally:
            event.remove(eng, "before_cursor_execute", listener)
        return len(stmts)

    def add(n, start):
        for i in range(n):
            _emp(db, world, f"q{start + i}", position=f"CV{i % 3}")
        db.commit()

    add(5, 0)
    c5 = count()
    add(45, 5)
    assert c5 > 0 and c5 == count()
