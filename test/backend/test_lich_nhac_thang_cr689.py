"""duoc-CR-689 — dữ liệu ô E3 «Lịch nhắc trong tháng»: `GET /api/employees/monthly-reminders?month=YYYY-MM`.

Route chung tiền tố `/api/employees` nên phải include TRƯỚC `employee_router` trong `main.py`. Bài kiểm này dựng
một app riêng chỉ gắn router của nó, nên chạy được dù điều phối chưa nối vào `main.py`.

Canh: phạm vi, che sinh nhật khi thiếu `employee_sensitive.read` (và không lộ năm sinh), kỷ niệm 1/3/5/10 năm,
hợp đồng / thử việc hết hạn trong tháng chỉ khi có `labor_contract.read`, trần 200 dòng mỗi nhóm, `month` sai -> 422,
số truy vấn CỐ ĐỊNH.
"""
import calendar
import uuid
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.vn_time import vn_today
from app.modules.employee.model import Employee
from app.modules.employee.monthly_reminders_controller import parse_month, router
from app.modules.labor_contract.model import LaborContract

TODAY = vn_today()
YEAR, MONTH = TODAY.year, TODAY.month
LAST_DAY = date(YEAR, MONTH, calendar.monthrange(YEAR, MONTH)[1])
URL = "/api/employees/monthly-reminders"
_n = {"v": 0}


@pytest.fixture
def client_as(db):
    local = FastAPI()
    local.include_router(router)

    def make_client(user):
        local.dependency_overrides[get_db] = lambda: db
        local.dependency_overrides[get_current_user] = lambda: user
        return TestClient(local, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make_client


def _emp(db, world, tag, **kw) -> Employee:
    base = dict(code=f"R{tag}", full_name=f"Người {tag}", company_id=world.co["B"],
                department_id=world.dept["B.hc"], is_active=True)
    base.update(kw)
    e = Employee(**base)
    db.add(e)
    db.flush()
    return e


def _contract(db, emp, ctype, end) -> LaborContract:
    _n["v"] += 1
    c = LaborContract(code=f"HDR{_n['v']:04d}", employee_id=emp.id, company_id=emp.company_id,
                      department_id=emp.department_id, contract_type=ctype, status=2,
                      start_date=date(2025, 1, 1), end_date=end)
    db.add(c)
    db.flush()
    return c


def _actor(world, client_as, *, sensitive=True, contract=True, scope="all", key="a1"):
    world.grant(key, "employee", scope, actions=("read",))
    if sensitive:
        world.grant(key, "employee_sensitive", "all", actions=("read",))
    if contract:
        world.grant(key, "labor_contract", "all", actions=("read",))
    return client_as(world.actor(key).user)


def _dataset(db, world):
    _emp(db, world, "sn5", date_of_birth=date(1990, MONTH, 5))
    _emp(db, world, "sn20", date_of_birth=date(1985, MONTH, 20))
    _emp(db, world, "snkhac", date_of_birth=date(1990, MONTH % 12 + 1, 5))                  # tháng khác
    _emp(db, world, "snnghi", date_of_birth=date(1990, MONTH, 6), status="resigned")        # đã nghỉ
    for years in (1, 2, 3, 5, 10):
        _emp(db, world, f"kn{years}", hire_date=date(YEAR - years, MONTH, 15))
    _emp(db, world, "kn3thangkhac", hire_date=date(YEAR - 3, MONTH % 12 + 1, 15))
    hd = _emp(db, world, "hd")
    _contract(db, hd, 2, LAST_DAY)
    tv = _emp(db, world, "tv")
    _contract(db, tv, 1, LAST_DAY)
    _contract(db, _emp(db, world, "hdsau"), 2, date(YEAR + (MONTH // 12), MONTH % 12 + 1, 28))   # tháng sau
    db.commit()


def test_du_bon_nhom_dung_noi_dung(db, world, client_as):
    _dataset(db, world)
    resp = _actor(world, client_as).get(URL, params={"month": f"{YEAR}-{MONTH:02d}"})
    assert resp.status_code == 200, resp.text
    d = resp.json()["data"] if "data" in resp.json() else resp.json()
    assert d["month"] == f"{YEAR}-{MONTH:02d}"
    assert [(b["employee_code"], b["day"], b["month"]) for b in d["birthdays"]["items"]] == [
        ("Rsn5", 5, MONTH), ("Rsn20", 20, MONTH)]
    assert d["birthdays"]["allowed"] and d["birthdays"]["total"] == 2
    assert {a["employee_code"]: a["years"] for a in d["anniversaries"]["items"]} == {
        "Rkn1": 1, "Rkn3": 3, "Rkn5": 5, "Rkn10": 10}
    assert [c["employee_code"] for c in d["contracts"]["items"]] == ["Rhd"]
    assert [c["employee_code"] for c in d["probations"]["items"]] == ["Rtv"]
    assert d["contracts"]["items"][0]["end_date"] == LAST_DAY.isoformat()
    assert "1990" not in str(d["birthdays"]) and "1985" not in str(d["birthdays"])           # không lộ năm sinh


def test_thieu_quyen_nhay_cam_che_sinh_nhat(db, world, client_as):
    _dataset(db, world)
    resp = _actor(world, client_as, sensitive=False).get(URL, params={"month": f"{YEAR}-{MONTH:02d}"})
    assert resp.status_code == 200
    d = resp.json()["data"] if "data" in resp.json() else resp.json()
    assert d["birthdays"] == {"allowed": False, "items": [], "total": 0, "truncated": False}
    assert len(d["anniversaries"]["items"]) == 4 and d["contracts"]["allowed"]
    assert "1990" not in resp.text and "date_of_birth" not in resp.text


def test_thieu_quyen_hop_dong_che_hop_dong_va_thu_viec(db, world, client_as):
    _dataset(db, world)
    resp = _actor(world, client_as, contract=False).get(URL, params={"month": f"{YEAR}-{MONTH:02d}"})
    d = resp.json()["data"] if "data" in resp.json() else resp.json()
    for key in ("contracts", "probations"):
        assert d[key] == {"allowed": False, "items": [], "total": 0, "truncated": False}
    assert d["birthdays"]["total"] == 2


def test_pham_vi_dept(db, world, client_as):
    _emp(db, world, "pvB", date_of_birth=date(1990, MONTH, 5))
    _emp(db, world, "pvA", date_of_birth=date(1990, MONTH, 5), company_id=world.co["A"],
         department_id=world.dept["A.kt"])
    db.commit()
    resp = _actor(world, client_as, scope="dept").get(URL, params={"month": f"{YEAR}-{MONTH:02d}"})
    d = resp.json()["data"] if "data" in resp.json() else resp.json()
    assert [b["employee_code"] for b in d["birthdays"]["items"]] == ["RpvA"]


def test_tran_200_dong_moi_nhom(db, world, client_as):
    db.add_all([Employee(code=f"RC{i:03d}", full_name=f"Người {i}", company_id=world.co["B"],
                         department_id=world.dept["B.hc"], is_active=True, date_of_birth=date(1990, MONTH, 1 + i % 28))
                for i in range(205)])
    db.commit()
    d = _actor(world, client_as).get(URL, params={"month": f"{YEAR}-{MONTH:02d}"}).json()
    d = d["data"] if "data" in d else d
    assert len(d["birthdays"]["items"]) == 200 and d["birthdays"]["total"] == 205 and d["birthdays"]["truncated"]


@pytest.mark.parametrize("bad", ["2026-13", "2026-00", "abc", "2026-1", "1999-05", "2101-01", "2026/05"])
def test_thang_sai_422(db, world, client_as, bad):
    assert _actor(world, client_as).get(URL, params={"month": bad}).status_code == 422


def test_thang_mac_dinh_la_thang_nay(db, world, client_as):
    resp = _actor(world, client_as).get(URL)
    d = resp.json()["data"] if "data" in resp.json() else resp.json()
    assert resp.status_code == 200 and d["month"] == f"{YEAR}-{MONTH:02d}"
    assert parse_month("2026-10", TODAY) == (2026, 10)


def test_khong_co_quyen_doc_nhan_su_403(db, world, client_as):
    world.grant("a1", "purchase_request", "all", actions=("read",))
    resp = client_as(world.actor("a1").user).get(URL, params={"month": f"{YEAR}-{MONTH:02d}"})
    assert resp.status_code == 403


def test_so_truy_van_khong_tang_theo_so_nhan_su(db, world, client_as):
    client = _actor(world, client_as)

    def count() -> int:
        stmts: list[str] = []
        listener = lambda conn, cur, stmt, *a: stmts.append(stmt)               # noqa: E731
        engine = db.get_bind()
        event.listen(engine, "before_cursor_execute", listener)
        try:
            assert client.get(URL, params={"month": f"{YEAR}-{MONTH:02d}"}).status_code == 200
        finally:
            event.remove(engine, "before_cursor_execute", listener)
        return len(stmts)

    def add(n, start):
        for i in range(n):
            e = _emp(db, world, f"q{start + i}", date_of_birth=date(1990, MONTH, 1 + i % 28),
                     hire_date=date(YEAR - 3, MONTH, 10))
            _contract(db, e, 2, LAST_DAY)
        db.commit()

    add(3, 0)
    count()                                   # lần đầu nạp hồ sơ quyền vào bộ nhớ đệm 60 giây
    c3 = count()
    add(12, 3)
    count()                                   # commit làm hết hạn đối tượng tài khoản -> nạp lại một lần
    assert count() == c3
