"""duoc-CR-749 — hai lượt "Cấp quỹ" chạy cùng lúc không còn trả 500.

Kiểm thật trên MySQL (11/11/2026): hai `POST /api/leave-balances/allocate` song song cùng thấy "chưa có dòng" rồi cùng
chèn; lượt sau vấp UNIQUE (nhân sự, năm, loại) ngay trong `ensure_balance` (lúc flush) và trả 500, cả lô bị hủy. Dữ liệu
vẫn đúng nhờ UNIQUE. Nay: lùi lại, chạy lại lô một lần (đường này chỉ tạo dòng thiếu); vẫn vấp thì 409 bằng lời.
SQLite không tái hiện được va chạm thật — bài này giả lập bằng cách cho `ensure_balance` ném `IntegrityError`.
"""
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.modules.employee.model import Employee
from app.modules.leave import balance_service
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType

ALLOCATE = "/api/leave-balances/allocate"
YEAR = 2030


@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _setup(db, world, client_as):
    lt = LeaveType(code="PN", name="Phép năm", counts_balance=True, annual_quota_days=12.0, sort_order=1)
    db.add(lt)
    emp = Employee(code="CQ1", full_name="Người cấp quỹ", company_id=world.co["B"], department_id=world.dept["B.hc"],
                   is_active=True, hire_date=date(2020, 1, 1))
    db.add(emp)
    db.commit()
    world.grant("a1", "leave_balance", "all", actions=("read", "create"))
    world.grant("a1", "employee", "all", actions=("read",))
    return lt, emp, client_as(world.actor("a1").user)


def _collide(monkeypatch, times: int):
    """Cho `ensure_balance` ném IntegrityError `times` lần đầu — như lượt bấm song song vừa chèn trước."""
    real = balance_service.ensure_balance
    calls = {"n": 0}

    def fake(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] <= times:
            raise IntegrityError("INSERT", {}, Exception("Duplicate entry for key uq_leave_balance_emp_year_type"))
        return real(*args, **kwargs)

    monkeypatch.setattr(balance_service, "ensure_balance", fake)


def test_cap_quy_va_cham_mot_lan_thi_tu_chay_lai_va_thanh_cong(db, world, client_as, monkeypatch):
    lt, emp, client = _setup(db, world, client_as)
    _collide(monkeypatch, times=1)
    r = client.post(ALLOCATE, json={"year": YEAR, "leave_type_ids": [lt.id], "employee_ids": [emp.id]})
    assert r.status_code == 200, r.text
    rows = db.query(LeaveBalance).filter(LeaveBalance.employee_id == emp.id, LeaveBalance.year == YEAR).all()
    assert len(rows) == 1


def test_cap_quy_va_cham_hai_lan_thi_409_bang_loi_khong_500(db, world, client_as, monkeypatch):
    lt, emp, client = _setup(db, world, client_as)
    _collide(monkeypatch, times=2)
    r = client.post(ALLOCATE, json={"year": YEAR, "leave_type_ids": [lt.id], "employee_ids": [emp.id]})
    assert r.status_code == 409
    assert "cấp quỹ khác đang chạy cùng lúc" in r.json()["error"]["message"]
