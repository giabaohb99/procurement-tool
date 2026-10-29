"""duoc-CR-688 — báo cáo A5 «Quỹ lương theo pháp nhân» (khóa 21): `/api/payroll-fund/summary` (+ export, rows).

Canh: chọn HĐ tại mốc (đã ký, còn hiệu lực, người còn làm, mỗi người một HĐ), chỉ số + thấp/cao nhất,
phạm vi, che nhóm < 3 người (kể cả với người xem mọi phạm vi) + che phụ hai kỳ, xu hướng theo tháng,
danh sách (403 với nhóm bị che), gác khóa báo cáo ở cả ba đường, xlsx và số truy vấn CỐ ĐỊNH.
"""
import uuid
from datetime import date, timedelta
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
from app.modules.labor_contract.model import LaborContract
from app.modules.report_access.model import ReportAccess

SIGNED, DRAFT, TERMINATED = 2, 1, 4
FIXED = 2
BASE = "/api/payroll-fund/summary"
P = {"preset": "custom", "date_from": "2026-06-01", "date_to": "2026-08-31", "compare": "none"}
_seq = {"n": 0}


def d(s: str) -> date:
    return date.fromisoformat(s)


@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _emp(db, world, tag, dept="B.hc", co="B", **kw) -> Employee:
    e = Employee(code=f"Q{tag}", full_name=f"Người {tag}", company_id=world.co[co],
                 department_id=world.dept[dept], is_active=True, **kw)
    db.add(e)
    db.flush()
    return e


def _hd(db, world, emp, *, start="2026-05-01", end=None, status=SIGNED, dept="B.hc", co="B",
        base=10_000_000, allow=1_000_000, ins=8_000_000, **kw) -> LaborContract:
    _seq["n"] += 1
    c = LaborContract(code=f"QL{_seq['n']:05d}", employee_id=emp.id, company_id=world.co[co],
                      department_id=world.dept[dept], contract_type=FIXED, status=status,
                      start_date=d(start), end_date=d(end) if end else None, signed_file_id=1,
                      base_salary=base, allowance=allow, insurance_salary=ins, **kw)
    db.add(c)
    db.flush()
    return c


def _people(db, world, n, prefix, pos="", **hd):
    out = []
    for i in range(n):
        e = _emp(db, world, f"{prefix}{i}", position=pos)
        _hd(db, world, e, **hd)
        out.append(e)
    return out


def _actor(db, world, client_as, scope="all", report=True):
    world.grant("a1", "labor_contract", scope, actions=("read", "export"))
    actor = world.actor("a1")
    if report:
        db.add(ReportAccess(report_key=int(ReportKey.PAYROLL_FUND), subject_kind=SUBJECT_EMPLOYEE,
                            subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
        db.commit()
    return actor, client_as(actor.user)


def _get(client, path=BASE, **extra):
    return client.get(path, params={**P, "department_id": extra.pop("department_id", ""), **extra})


def test_chon_hd_tai_moc_va_chi_so(db, world, client_as):
    _people(db, world, 3, "ok")                                           # 3 người đủ điều kiện
    over = _emp(db, world, "over"); _hd(db, world, over, base=20_000_000, allow=0, ins=0)
    # loại: nháp · hết hạn trước mốc · chưa bắt đầu · người nghỉ việc
    _hd(db, world, _emp(db, world, "dr"), status=DRAFT)
    _hd(db, world, _emp(db, world, "exp"), end="2026-07-01")
    _hd(db, world, _emp(db, world, "fut"), start="2026-09-15")
    _hd(db, world, _emp(db, world, "res", status="resigned"))
    # HĐ chấm dứt SAU mốc (31/08) vẫn tính; chấm dứt TRƯỚC mốc thì không
    _hd(db, world, _emp(db, world, "tafter"), status=TERMINATED, terminated_date=d("2026-09-10"),
        base=5_000_000, allow=0, ins=0)
    _hd(db, world, _emp(db, world, "tbefore"), status=TERMINATED, terminated_date=d("2026-08-10"))
    # Hai HĐ chồng nhau của cùng một người: chỉ lấy HĐ bắt đầu muộn hơn
    dup = _emp(db, world, "dup")
    _hd(db, world, dup, start="2026-01-01", base=1_000_000, allow=0, ins=0)
    _hd(db, world, dup, start="2026-06-01", base=2_000_000, allow=0, ins=0)
    db.commit()
    _, client = _actor(db, world, client_as)
    resp = _get(client, department_id=world.dept["B.hc"])
    assert resp.status_code == 200, resp.text
    cur = resp.json()["data"]["totals"]["current"]
    assert cur["people_paid"] == 6
    assert cur["base_total"] == 3 * 10_000_000 + 20_000_000 + 5_000_000 + 2_000_000
    assert cur["allowance_total"] == 3_000_000
    assert cur["payroll_total"] == cur["base_total"] + cur["allowance_total"]
    assert cur["insurance_total"] == 3 * 8_000_000     # chỉ 3 người đầu có lương BHXH
    assert cur["avg_payroll"] == round(cur["payroll_total"] / 6)
    assert cur["base_min"] == 2_000_000 and cur["base_max"] == 20_000_000
    keys = [m["key"] for m in resp.json()["data"]["meta"]["metrics"]]
    assert keys == ["people_paid", "base_total", "allowance_total", "payroll_total", "insurance_total",
                    "avg_payroll", "base_min", "base_max"]


def test_nhom_theo_phap_nhan_va_chieu_khac(db, world, client_as):
    _people(db, world, 3, "b", pos="Kế toán")
    _people(db, world, 4, "a", dept="A.kt", co="A", pos="Kỹ thuật")
    db.commit()
    _, client = _actor(db, world, client_as)
    for gb in ("company", "department", "position", "job_category", "contract_type"):
        r = _get(client, group_by=gb)
        assert r.status_code == 200, (gb, r.text)
        assert sum(g["current"]["people_paid"] or 0 for g in r.json()["data"]["groups"]) == 7
    groups = {g["key"]: g for g in _get(client, group_by="company").json()["data"]["groups"]}
    gb = groups[str(world.co["B"])]["current"]
    assert gb["people_paid"] == 3 and gb["base_min"] == gb["base_max"] == 10_000_000
    assert _get(client, group_by="bogus").status_code == 422


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
    data = _get(client, group_by="position").json()["data"]
    assert data["groups"] == [] and data["totals"]["current"]["people_paid"] == 2
    assert any("Không đủ người để xem theo Chức vụ" in n for n in data["notes"])
    r = _get(client, BASE + "/rows", metric="people_paid", group_by="position", group_key="Hai")
    assert r.status_code == 403


def test_hai_nhom_1_nguoi_bo_ca_bang_nhom(db, world, client_as):
    _people(db, world, 1, "one", pos="Một")
    _people(db, world, 1, "uno", pos="Nhất")
    db.commit()
    _, client = _actor(db, world, client_as)
    assert _get(client, group_by="position").json()["data"]["groups"] == []


def test_nguoi_co_hd_o_hai_phap_nhan_tinh_o_ca_hai(db, world, client_as):
    p = _emp(db, world, "two", co="B")
    _hd(db, world, p, co="B", base=10_000_000, allow=0, ins=0)
    _hd(db, world, p, co="A", dept="A.kt", base=4_000_000, allow=0, ins=0)
    _hd(db, world, p, co="A", dept="A.kt", start="2026-02-01", base=1_000_000, allow=0, ins=0)  # cùng pháp nhân: giữ HĐ mới
    db.commit()
    _, client = _actor(db, world, client_as)
    data = _get(client, department_id="", group_by="company").json()["data"]
    assert data["totals"]["current"]["people_paid"] == 2 and data["totals"]["current"]["base_total"] == 14_000_000
    assert any("hai pháp nhân" in n for n in data["notes"])


def test_che_phu_khi_chi_mot_nhom_nho(db, world, client_as):
    _people(db, world, 6, "big", pos="Lớn")
    _people(db, world, 3, "mid", pos="Vừa")
    _people(db, world, 1, "one", pos="Một")
    db.commit()
    _, client = _actor(db, world, client_as)
    g = {x["label"]: x for x in _get(client, group_by="position").json()["data"]["groups"]}
    assert g["Một"]["suppressed"] and g["Vừa"]["suppressed"]       # che thêm nhóm nhỏ nhất còn hiện
    assert g["Lớn"]["current"]["people_paid"] == 6


def test_che_phu_xet_rieng_ky_so_sanh(db, world, client_as):
    """Kỳ này 'Một' và 'Bốn' đều đủ lớn; kỳ trước 'Một' chỉ có 1 người -> che cả nhóm ở CẢ HAI kỳ và che
    phụ theo kỳ trước (nếu chỉ xét kỳ này, Tổng kỳ trước trừ nhóm hiện vẫn lộ lương người đó)."""
    _people(db, world, 5, "big", pos="Lớn", start="2026-01-01")
    _people(db, world, 3, "mid", pos="Vừa", start="2026-01-01")
    # 'Một': 3 người kỳ này (tháng 8) nhưng chỉ 1 người đã có HĐ từ trước tháng 7
    _people(db, world, 1, "old", pos="Một", start="2026-01-01")
    _people(db, world, 2, "new", pos="Một", start="2026-08-10")
    db.commit()
    _, client = _actor(db, world, client_as)
    q = {"preset": "custom", "date_from": "2026-08-01", "date_to": "2026-08-31", "compare": "previous"}
    data = client.get(BASE, params={**q, "group_by": "position", "department_id": ""}).json()["data"]
    g = {x["label"]: x for x in data["groups"]}
    assert data["totals"]["compare"]["people_paid"] == 9 and data["totals"]["current"]["people_paid"] == 11
    assert g["Một"]["suppressed"] and all(v is None for v in g["Một"]["current"].values())
    assert g["Một"]["compare"] is not None and all(v is None for v in g["Một"]["compare"].values())
    #  kỳ trước: nhóm bị che chỉ có 1 người -> che thêm 'Vừa' (nhỏ nhất còn hiện) ở cả hai kỳ
    assert g["Vừa"]["suppressed"] is True and not g["Lớn"].get("suppressed")


def test_xu_huong_theo_thang_tu_mot_lan_nap(db, world, client_as):
    _people(db, world, 3, "a", start="2026-05-01")
    _hd(db, world, _emp(db, world, "jul"), start="2026-07-15")
    _hd(db, world, _emp(db, world, "aug"), start="2026-08-20")
    db.commit()
    _, client = _actor(db, world, client_as)
    trend = _get(client).json()["data"]["trend"]
    assert [t["key"] for t in trend] == ["2026-06", "2026-07", "2026-08"]
    assert [t["current"]["people_paid"] for t in trend] == [3, 4, 5]
    assert [t["current"]["payroll_total"] for t in trend] == [33_000_000, 44_000_000, 55_000_000]
    assert all(t["compare"] is None for t in trend)
    cmp = client.get(BASE, params={**P, "compare": "previous", "department_id": ""}).json()["data"]["trend"]
    #  kỳ trước lùi 92 ngày: cuối tháng 8 -> 31/05 (3 người), tháng 7 -> 30/04 và tháng 6 -> 30/03 (chưa ai có HĐ)
    assert [t["compare"]["people_paid"] for t in cmp] == [0, 0, 3]


def test_rows_khop_so_va_403_nhom_bi_che(db, world, client_as):
    _people(db, world, 4, "big", pos="Lớn")
    _people(db, world, 1, "one", pos="Một")
    _people(db, world, 2, "two", pos="Hai")
    db.commit()
    _, client = _actor(db, world, client_as)
    rows = _get(client, BASE + "/rows", metric="people_paid").json()["data"]
    assert rows["total"] == 7 and [c["key"] for c in rows["columns"]][-3:] == [
        "base_salary", "allowance", "insurance_salary"]
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


def test_export_xlsx_nhom_bi_che_de_trong(db, world, client_as):
    _people(db, world, 5, "big", pos="Lớn")
    _people(db, world, 1, "one", pos="Một")
    _people(db, world, 2, "two", pos="Hai")
    db.commit()
    _, client = _actor(db, world, client_as)
    r = _get(client, BASE + "/export", group_by="position")
    assert r.status_code == 200 and "spreadsheetml" in r.headers["content-type"]
    ws = load_workbook(BytesIO(r.content)).active
    rows = {row[0].value: [c.value for c in row[1:]] for row in ws.iter_rows(min_row=2)}
    assert all(v is None for v in rows["Một"]) and all(v is None for v in rows["Hai"])
    assert any(v not in (None, "", 0) for v in rows["Tổng"])


def test_so_truy_van_khong_tang_theo_so_hop_dong(db, world):
    world.grant("a1", "labor_contract", "all", actions=("read",))
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
            service.build_summary(
                db, apply_scope(db.query(LaborContract), LaborContract, "labor_contract", actor.user, prof),
                period, "department")
        finally:
            event.remove(eng, "before_cursor_execute", listener)
        return len(stmts)

    def add(n, start):
        for i in range(n):
            _hd(db, world, _emp(db, world, f"q{start + i}", position=f"CV{i % 3}"), end="2026-12-31")
        db.commit()

    add(5, 0)
    c5 = count()
    add(45, 5)
    assert c5 > 0 and c5 == count()
