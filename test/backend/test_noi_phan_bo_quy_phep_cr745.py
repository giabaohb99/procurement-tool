"""duoc-CR-745 — nối Phân bổ chính sách với Quỹ phép năm (kiểu mục Leaves / liên kết ngược của ERPNext).

- Danh sách phân bổ kèm `current_year_quotas`: hạn mức năm nay theo loại nghỉ của gói + `balance_id` để bấm sang.
- Danh sách dòng quỹ kèm `policy_name`: chính sách quyết định hạn mức của ĐÚNG loại đó trong năm đó.
- Ma trận theo nhân sự kèm `policy_name` của các phân bổ chạm năm đang xem.
Số truy vấn cố định theo trang (không tra từng dòng).
"""
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.vn_time import vn_today
from app.main import app
from app.modules.employee.model import Employee
from app.modules.leave import balance_matrix_service, policy_balance_links
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.policy_model import LeavePolicy, LeavePolicyAssignment, LeavePolicyLine

YEAR = vn_today().year
ASSIGN = "/api/leave-policy-assignments"
BALANCES = "/api/leave-balances"
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
    annual = LeaveType(code="PN", name="Phép năm", counts_balance=True, annual_quota_days=12.0, sort_order=1)
    comp = LeaveType(code="NB", name="Nghỉ thêm", counts_balance=True, annual_quota_days=0.0, sort_order=2)
    sick = LeaveType(code="OM", name="Ốm đau", counts_balance=False, sort_order=3)
    db.add_all([annual, comp, sick])
    db.flush()
    return annual, comp, sick


def _policy(db, code, name, lines):
    p = LeavePolicy(code=code, name=name, is_active=True)
    db.add(p)
    db.flush()
    db.add_all([LeavePolicyLine(policy_id=p.id, leave_type_id=t.id, annual_days=d) for t, d in lines])
    db.flush()
    return p


def _emp(db, world, tag):
    e = Employee(code=f"N{tag}", full_name=f"Người {tag}", company_id=world.co["B"],
                 department_id=world.dept["B.hc"], is_active=True, hire_date=date(2020, 1, 1))
    db.add(e)
    db.flush()
    return e


def _assign(db, world, emp, policy, start, end=None):
    a = LeavePolicyAssignment(employee_id=emp.id, company_id=world.co["B"], policy_id=policy.id,
                              effective_from=start, effective_to=end)
    db.add(a)
    db.flush()
    return a


def _bal(db, world, emp, lt, year=YEAR, **kw):
    b = LeaveBalance(employee_id=emp.id, year=year, leave_type_id=lt.id, company_id=world.co["B"], **kw)
    db.add(b)
    db.flush()
    return b


def _client(world, client_as):
    world.grant("a1", "leave_balance", "all", actions=("read", "export"))
    return client_as(world.actor("a1").user)


def test_danh_sach_phan_bo_kem_han_muc_nam_nay_va_id_dong_quy(db, world, client_as):
    annual, comp, sick = _types(db)
    policy = _policy(db, "QL", "Cấp quản lý", [(annual, 15), (comp, 2), (sick, 30)])
    e1, e2 = _emp(db, world, "1"), _emp(db, world, "2")
    a1 = _assign(db, world, e1, policy, date(YEAR, 1, 1))
    old = _assign(db, world, e2, policy, date(YEAR - 1, 1, 1), date(YEAR - 1, 12, 31))  # không chạm năm nay
    b1 = _bal(db, world, e1, annual, allocated_days=15)
    db.commit()

    items = {i["id"]: i for i in _client(world, client_as).get(ASSIGN).json()["data"]["items"]}
    #  Ốm đau không trừ quỹ nên không hiện; Nghỉ thêm có trong gói nhưng chưa có dòng quỹ -> chưa cấp.
    assert items[a1.id]["current_year_quotas"] == [
        {"leave_type_id": annual.id, "leave_type_name": "Phép năm", "allocated_days": 15.0, "balance_id": b1.id},
        {"leave_type_id": comp.id, "leave_type_name": "Nghỉ thêm", "allocated_days": None, "balance_id": 0},
    ]
    assert items[old.id]["current_year_quotas"] == []


def test_dong_quy_ghi_chinh_sach_dung_loai_dung_nam(db, world, client_as):
    annual, comp, _ = _types(db)
    policy = _policy(db, "TC", "Tiêu chuẩn", [(annual, 12)])
    e1 = _emp(db, world, "1")
    _assign(db, world, e1, policy, date(YEAR, 3, 1))
    in_policy = _bal(db, world, e1, annual, allocated_days=12)
    not_in_policy = _bal(db, world, e1, comp, allocated_days=0)          # gói không khai loại này
    last_year = _bal(db, world, e1, annual, year=YEAR - 1, allocated_days=12)  # phân bổ chưa chạm năm ngoái
    db.commit()

    items = {i["id"]: i for i in _client(world, client_as).get(BALANCES).json()["data"]["items"]}
    assert items[in_policy.id]["policy_name"] == "Tiêu chuẩn"
    assert items[not_in_policy.id]["policy_name"] == ""
    assert items[last_year.id]["policy_name"] == ""


def test_ma_tran_ghi_hai_chinh_sach_khi_doi_giua_nam(db, world, client_as):
    annual, _, _ = _types(db)
    std = _policy(db, "TC", "Tiêu chuẩn", [(annual, 12)])
    mgr = _policy(db, "QL", "Cấp quản lý", [(annual, 15)])
    e1, e2 = _emp(db, world, "1"), _emp(db, world, "2")
    _assign(db, world, e1, std, date(YEAR, 1, 1), date(YEAR, 6, 30))
    _assign(db, world, e1, mgr, date(YEAR, 7, 1))
    _bal(db, world, e1, annual, allocated_days=14)
    _bal(db, world, e2, annual, allocated_days=12)
    db.commit()

    items = {i["employee_id"]: i for i in
             _client(world, client_as).get(MATRIX, params={"year": YEAR}).json()["data"]["items"]}
    assert items[e1.id]["policy_name"] == "Tiêu chuẩn → Cấp quản lý"
    assert items[e2.id]["policy_name"] == ""


def _count_queries(db, fn) -> int:
    stmts: list[str] = []

    def listener(conn, cur, stmt, *args):
        stmts.append(stmt)

    eng = db.get_bind()
    event.listen(eng, "before_cursor_execute", listener)
    try:
        fn()
    finally:
        event.remove(eng, "before_cursor_execute", listener)
    return len(stmts)


def test_so_truy_van_co_dinh_theo_trang(db, world):
    annual, comp, _ = _types(db)
    policy = _policy(db, "QL", "Cấp quản lý", [(annual, 15), (comp, 2)])
    world.grant("a1", "leave_balance", "all", actions=("read",))
    actor = world.actor("a1")
    prof = actor.profile()

    def add(n, start):
        for i in range(n):
            e = _emp(db, world, f"q{start + i}")
            _assign(db, world, e, policy, date(YEAR, 1, 1))
            _bal(db, world, e, annual, allocated_days=15)
        db.commit()

    def run():
        rows = db.query(LeavePolicyAssignment).all()
        policy_balance_links.quotas_for_assignments(db, rows, actor.user, prof, YEAR)
        policy_balance_links.policy_names_for_balances(db, db.query(LeaveBalance).all())
        balance_matrix_service.build_matrix(db, actor.user, prof, "read", YEAR, None, None, "working", None, 0, 50)

    add(2, 0)
    small = _count_queries(db, run)
    add(30, 2)
    assert small > 0 and small == _count_queries(db, run)
