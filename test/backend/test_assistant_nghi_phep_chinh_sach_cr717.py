"""duoc-CR-717 phía AI — `my_leave_summary` nói được chính sách nghỉ phép đang áp cho người hỏi.

1. Có phân bổ phủ hôm nay → `policy` (tên, mã, khoảng ngày) + `policy_name` / `policy_annual_days` từng loại; loại gói
   không khai thì `policy_annual_days = None` (theo luật của loại). Hạn mức vẫn đọc `allocated_days` của dòng quỹ.
2. Không có phân bổ, hoặc phân bổ đã hết trước mốc → `policy = None`, các ô của loại đều `None`.
3. Năm đã qua: mốc = 31/12 của năm đó (gói hết giữa năm không còn là "đang áp").
4. Chỉ đọc: số câu truy vấn thêm cố định, không sinh dòng quỹ.
"""
from datetime import date

import pytest
from sqlalchemy import event

from app.modules.assistant import tools as T
from app.modules.assistant.tools import leave_tool
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.policy_model import LeavePolicy, LeavePolicyAssignment, LeavePolicyLine
from app.modules.user.model import User

TODAY = date(2026, 11, 3)


@pytest.fixture(autouse=True)
def _frozen_today(monkeypatch):
    monkeypatch.setattr(leave_tool, "vn_today", lambda: TODAY)


@pytest.fixture()
def world(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "leave_request", scope="own", read=True)
    annual = LeaveType(code="annual", name="Phép năm", counts_balance=True, annual_quota_days=12.0)
    sick = LeaveType(code="sick", name="Nghỉ ốm", counts_balance=True, annual_quota_days=5.0)
    db.add_all([annual, sick])
    db.flush()
    policy = LeavePolicy(code="CS-QL", name="Chính sách cấp quản lý", is_active=True)
    db.add(policy)
    db.flush()
    db.add(LeavePolicyLine(policy_id=policy.id, leave_type_id=annual.id, annual_days=15.0))
    db.add(LeaveBalance(employee_id=seed.emp_req_id, year=2026, leave_type_id=annual.id, allocated_days=13.5))
    db.commit()
    return user, annual, sick, policy


def _assign(db, seed, policy, start: date, end: date | None = None):
    db.add(LeavePolicyAssignment(employee_id=seed.emp_req_id, company_id=0, policy_id=policy.id,
                                 effective_from=start, effective_to=end))
    db.commit()


def _row(out, type_id):
    return next(b for b in out["balances"] if b["leave_type_id"] == type_id)


def test_co_phan_bo_thi_noi_ten_goi_va_so_ngay_tung_loai(db, seed, world):
    user, annual, sick, policy = world
    _assign(db, seed, policy, date(2026, 7, 1))
    out = T.run_tool(db, user, "my_leave_summary", {"year": 2026})
    assert out["policy"] == {"name": "Chính sách cấp quản lý", "code": "CS-QL",
                             "effective_from": "2026-07-01", "effective_to": None}
    row = _row(out, annual.id)
    assert row["policy_name"] == "Chính sách cấp quản lý" and row["policy_annual_days"] == 15.0
    assert row["allocated_days"] == 13.5                     # hạn mức thật vẫn là số chia theo tháng của dòng quỹ
    unallocated = _row(out, sick.id)                         # loại gói không khai → theo luật của loại
    assert unallocated["allocated"] is False and unallocated["policy_annual_days"] is None
    assert "policy" in out["glossary"]


def test_khong_co_phan_bo_hoac_da_het_thi_policy_none(db, seed, world):
    user, annual, _sick, policy = world
    out = T.run_tool(db, user, "my_leave_summary", {"year": 2026})
    assert out["policy"] is None and _row(out, annual.id)["policy_name"] is None

    _assign(db, seed, policy, date(2026, 1, 1), date(2026, 6, 30))        # hết trước hôm nay
    out = T.run_tool(db, user, "my_leave_summary", {"year": 2026})
    assert out["policy"] is None and _row(out, annual.id)["policy_annual_days"] is None


def test_nam_da_qua_lay_moc_cuoi_nam(db, seed, world):
    user, _annual, _sick, policy = world
    _assign(db, seed, policy, date(2025, 3, 1), date(2025, 12, 31))
    assert T.run_tool(db, user, "my_leave_summary", {"year": 2025})["policy"]["effective_to"] == "2025-12-31"
    _assign(db, seed, policy, date(2024, 1, 1), date(2024, 6, 30))
    assert T.run_tool(db, user, "my_leave_summary", {"year": 2024})["policy"] is None


def test_chi_doc_so_cau_co_dinh_khong_sinh_dong_quy(db, seed, world):
    user, _annual, _sick, policy = world
    _assign(db, seed, policy, date(2026, 1, 1))
    before = db.query(LeaveBalance).count()
    statements = []

    def count(*_args):
        statements.append(1)

    event.listen(db.bind, "before_cursor_execute", count)
    try:
        leave_tool._active_policy(db, seed.emp_req_id, 2026)
    finally:
        event.remove(db.bind, "before_cursor_execute", count)
    assert len(statements) <= 3                               # phân bổ · gói · dòng gói
    assert db.query(LeaveBalance).count() == before
