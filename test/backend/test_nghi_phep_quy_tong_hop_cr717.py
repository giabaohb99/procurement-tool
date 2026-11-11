"""duoc-CR-717 — ba khoảng hở nhỏ của Quỹ phép: ma trận "Tổng hợp theo người" (`/api/leave-balances/matrix`),
chỉ số "Nghỉ bù cộng thêm" của báo cáo Quỹ phép năm, và hộp "Cấp quỹ" có lọc.
"""
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.subject_match import SUBJECT_EMPLOYEE
from app.core.vn_time import vn_today
from app.main import app
from app.modules.employee.model import Employee
from app.modules.leave import balance_matrix_service
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LeaveAccrualMode
from app.modules.report_access.model import ReportAccess

YEAR = vn_today().year + 1          # năm tới: loại cộng dần chưa tới tháng nào → ô = 0 (không phụ thuộc ngày chạy test)
MATRIX = "/api/leave-balances/matrix"


@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _types(db):
    full = LeaveType(code="PN", name="Phép năm", counts_balance=True, annual_quota_days=12.0, sort_order=1)
    monthly = LeaveType(code="PC", name="Phép cộng dần", counts_balance=True, annual_quota_days=12.0, sort_order=2,
                        accrual_mode=int(LeaveAccrualMode.MONTHLY))
    free = LeaveType(code="KL", name="Không lương", counts_balance=False, sort_order=3)
    db.add_all([full, monthly, free])
    db.flush()
    return full, monthly, free


def _emp(db, world, tag, dept="B.hc", co="B", **kw) -> Employee:
    e = Employee(code=f"M{tag}", full_name=f"Người {tag}", company_id=world.co[co],
                 department_id=world.dept[dept], is_active=True, hire_date=date(2020, 1, 1), **kw)
    db.add(e)
    db.flush()
    return e


def _bal(db, world, emp, lt, year=YEAR, co="B", **kw) -> LeaveBalance:
    row = LeaveBalance(employee_id=emp.id, year=year, leave_type_id=lt.id, company_id=world.co[co], **kw)
    db.add(row)
    db.flush()
    return row


def _actor(world, client_as, scope="all", actions=("read", "export"), key="a1"):
    world.grant(key, "leave_balance", scope, actions=actions)
    return world.actor(key), client_as(world.actor(key).user)


def test_ma_tran_cot_theo_loai_va_o_la_so_dung_duoc(db, world, client_as):
    full, monthly, free = _types(db)
    e1, e2 = _emp(db, world, "1"), _emp(db, world, "2", dept="B.kt")
    _bal(db, world, e1, full, allocated_days=12, used_days=2)
    _bal(db, world, e1, monthly, allocated_days=12)
    _bal(db, world, e2, full, allocated_days=10, comp_days=1)
    _bal(db, world, e2, free, allocated_days=5)                 # loại không trừ quỹ — không thành cột
    _bal(db, world, e2, full, year=YEAR - 1, allocated_days=99)  # năm khác — không vào
    db.commit()
    _, client = _actor(world, client_as)
    resp = client.get(MATRIX, params={"year": YEAR})
    assert resp.status_code == 200, resp.text                    # không bị `/{bid}` nuốt
    d = resp.json()["data"]
    assert [c["name"] for c in d["columns"]] == ["Phép năm", "Phép cộng dần"]
    assert d["total"] == 2 and d["year"] == YEAR
    by = {i["code"]: i for i in d["items"]}
    assert by["M1"]["cells"] == {str(full.id): 10.0, str(monthly.id): 0.0}      # cộng dần: chưa tới tháng → 0
    assert by["M1"]["total"] == 10.0 and by["M1"]["department_name"] == "Phòng Hành chính"
    assert by["M2"]["cells"] == {str(full.id): 11.0} and by["M2"]["total"] == 11.0
    assert [i["code"] for i in d["items"]] == ["M1", "M2"]


def test_ma_tran_loc_tim_kiem_phan_trang_va_trang_thai(db, world, client_as):
    full, _, _ = _types(db)
    emps = [_emp(db, world, str(i), dept="B.hc" if i % 2 else "B.kt") for i in range(5)]
    for e in emps:
        _bal(db, world, e, full, allocated_days=12)
    gone = _emp(db, world, "x")
    gone.is_active = False
    _bal(db, world, gone, full, allocated_days=12)
    db.commit()
    _, client = _actor(world, client_as)
    q = {"year": YEAR}
    assert client.get(MATRIX, params=q).json()["data"]["total"] == 5               # mặc định chỉ người đang làm
    assert client.get(MATRIX, params={**q, "employee_status": "all"}).json()["data"]["total"] == 6
    assert client.get(MATRIX, params={**q, "employee_status": "bogus"}).status_code == 422
    page = client.get(MATRIX, params={**q, "page": 2, "page_size": 2}).json()["data"]
    assert page["total"] == 5 and [i["code"] for i in page["items"]] == ["M2", "M3"]
    assert [c["name"] for c in page["columns"]] == ["Phép năm"]                    # cột không nhảy theo trang
    assert client.get(MATRIX, params={**q, "search": "Người 3"}).json()["data"]["total"] == 1
    assert client.get(MATRIX, params={**q, "search": "%"}).json()["data"]["total"] == 0   # không là ký tự đại diện
    assert client.get(MATRIX, params={**q, "department_id": world.dept["B.kt"]}).json()["data"]["total"] == 3
    assert client.get(MATRIX, params={**q, "company_id": world.co["A"]}).json()["data"]["total"] == 0


def test_ma_tran_pham_vi_own_chi_mot_dong_va_gac_quyen(db, world, client_as):
    full, _, _ = _types(db)
    actor = world.actor("a1")
    other = _emp(db, world, "o", dept="A.kt", co="A")
    for e in (actor.employee, other):
        _bal(db, world, e, full, co="A", allocated_days=12)
    db.commit()
    _, client = _actor(world, client_as, scope="own")
    d = client.get(MATRIX, params={"year": YEAR}).json()["data"]
    assert d["total"] == 1 and d["items"][0]["employee_id"] == actor.employee.id
    world.grant("a2", "leave_request", "all")                    # có tài khoản nhưng KHÔNG có quyền quỹ phép
    assert client_as(world.actor("a2").user).get(MATRIX).status_code == 403
    assert client_as(world.actor("a2").user).get(MATRIX + "/export").status_code == 403


def test_ma_tran_export_cot_dong(db, world, client_as):
    full, monthly, _ = _types(db)
    e1 = _emp(db, world, "1")
    _bal(db, world, e1, full, allocated_days=12)
    _bal(db, world, e1, monthly, allocated_days=12)
    db.commit()
    _, client = _actor(world, client_as)
    r = client.get(MATRIX + "/export", params={"year": YEAR})
    assert r.status_code == 200 and "spreadsheetml" in r.headers["content-type"]
    import io
    from openpyxl import load_workbook
    ws = load_workbook(io.BytesIO(r.content)).active
    #  duoc-CR-745: thêm cột Chính sách sau Phòng ban; người chưa phân bổ ghi "Theo loại nghỉ".
    assert [c.value for c in ws[1]] == ["Mã NV", "Họ tên", "Phòng ban", "Chính sách", "Phép năm", "Phép cộng dần",
                                        "Tổng còn lại"]
    assert [c.value for c in ws[2]][3:] == ["Theo loại nghỉ", 12, 0, 12]
    _, ro = _actor(world, client_as, actions=("read",), key="a2")
    assert ro.get(MATRIX + "/export").status_code == 403


def test_ma_tran_so_truy_van_co_dinh(db, world):
    full, monthly, _ = _types(db)
    world.grant("a1", "leave_balance", "all", actions=("read",))
    actor = world.actor("a1")
    prof = actor.profile()

    def add(n, start):
        for i in range(n):
            e = _emp(db, world, f"q{start + i}", dept="B.hc" if i % 2 else "B.kt")
            _bal(db, world, e, full, allocated_days=12, carried_days=1)
            _bal(db, world, e, monthly, allocated_days=12)
        db.commit()

    def count() -> int:
        stmts: list[str] = []

        def listener(conn, cur, stmt, *args):
            stmts.append(stmt)

        eng = db.get_bind()
        event.listen(eng, "before_cursor_execute", listener)
        try:
            balance_matrix_service.build_matrix(db, actor.user, prof, "read", YEAR, None, None, "working", None, 0, 50)
        finally:
            event.remove(eng, "before_cursor_execute", listener)
        return len(stmts)

    add(2, 0)
    c2 = count()
    add(40, 2)
    assert c2 > 0 and c2 == count()


def test_bao_cao_quy_phep_nam_co_chi_so_nghi_bu_cong_them(db, world, client_as):
    full, _, _ = _types(db)
    e1, e2 = _emp(db, world, "1"), _emp(db, world, "2")
    year = vn_today().year
    _bal(db, world, e1, full, year=year, allocated_days=12, comp_days=1.5)
    _bal(db, world, e2, full, year=year, allocated_days=12, comp_days=2)
    db.commit()
    actor, client = _actor(world, client_as, actions=("read",))
    db.add(ReportAccess(report_key=int(ReportKey.LEAVE_BALANCE), subject_kind=SUBJECT_EMPLOYEE,
                        subject_id=actor.employee.id, effect=1, reason="t", created_by=0, updated_by=0))
    db.commit()
    resp = client.get("/api/leave-balances/summary", params={"preset": "this_year", "compare": "none"})
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["totals"]["current"]["comp"] == pytest.approx(3.5)
    comp = next(m for m in data["meta"]["metrics"] if m["key"] == "comp")
    assert comp["label"] == "Nghỉ bù cộng thêm" and comp["kind"] == "days"


def _only_mine(db):
    """Nhân sự mẫu của `world` thôi hoạt động để bài đếm đúng số người do bài dựng."""
    db.query(Employee).filter(~Employee.code.like("M%")).update({"is_active": False}, synchronize_session=False)
    db.commit()


def _allocate(client, **body):
    return client.post("/api/leave-balances/allocate", json={"year": YEAR, **body})


def test_cap_quy_co_loc_chi_thu_hep_trong_pham_vi(db, world, client_as):
    full, _, _ = _types(db)
    in_kt = _emp(db, world, "1", dept="B.kt", employment_type=1, job_level=2)
    in_hc = _emp(db, world, "2", dept="B.hc", employment_type=1, job_level=3)
    other = _emp(db, world, "3", dept="B.hc", employment_type=2, job_level=2)
    _only_mine(db)
    world.grant("a1", "leave_balance", "all", actions=("create",))
    world.grant("a1", "employee", "all", actions=("read",))
    client = client_as(world.actor("a1").user)

    def owners() -> set[str]:
        return {db.get(Employee, r.employee_id).code for r in db.query(LeaveBalance).filter_by(year=YEAR).all()}

    d = _allocate(client, leave_type_ids=[full.id], department_id=world.dept["B.kt"]).json()["data"]
    assert d["employee_count"] == 1 and owners() == {in_kt.code}
    assert _allocate(client, leave_type_ids=[full.id], employment_type=1, job_level=3).json()["data"]["employee_count"] == 1
    assert owners() == {in_kt.code, in_hc.code}
    assert _allocate(client, leave_type_ids=[full.id], company_id=world.co["A"]).json()["data"]["employee_count"] == 0
    assert _allocate(client, leave_type_ids=[full.id], job_level=-1).status_code == 422
    #  Không lọc = như cũ (mọi người đang làm trong phạm vi) — chạy lại chỉ thêm dòng còn thiếu.
    d = _allocate(client, leave_type_ids=[full.id]).json()["data"]
    assert d["created"] == 1 and other.code in owners()
    assert db.query(LeaveBalance).filter_by(year=YEAR, employee_id=in_kt.id).count() == 1


def test_cap_quy_loc_khong_mo_rong_ra_ngoai_pham_vi(db, world, client_as):
    full, _, _ = _types(db)
    mine = _emp(db, world, "1", dept="A.kt", co="A")
    theirs = _emp(db, world, "2", dept="B.kt", co="B")
    _only_mine(db)
    world.grant("a1", "leave_balance", "all", actions=("create",))
    world.grant("a1", "employee", "dept", actions=("read",))          # a1 chỉ thấy phòng A.kt
    client = client_as(world.actor("a1").user)
    d = _allocate(client, leave_type_ids=[full.id], department_id=world.dept["B.kt"]).json()["data"]
    assert d["employee_count"] == 0                                    # lọc sang phòng ngoài phạm vi vẫn ra rỗng
    assert db.query(LeaveBalance).filter_by(employee_id=theirs.id).count() == 0
    d = _allocate(client, leave_type_ids=[full.id], department_id=world.dept["A.kt"]).json()["data"]
    assert d["employee_count"] == 1 and db.query(LeaveBalance).filter_by(employee_id=mine.id).count() == 1
