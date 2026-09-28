"""Hai lỗi bắt được khi diễn tập erp-v2 trên bản sao DB prod ngày 28/09/2026.

1. Bản v1 gửi 0 cho ô Dự toán / Tạm tính chưa gõ, còn dòng chi phí chuyển từ khuôn cũ để TRỐNG
   hai cột đó — phép so «dòng đã quyết toán có bị sửa không» coi None ≠ 0 nên mọi lần lưu ĐMH
   trên v1 ăn 400 (PO00122 trên prod).
2. Ô chọn NSTM bỏ sót người giữ vai trò phạm vi «được giao» (`pur_staff`) — 3/4 người đang nhận
   việc trên prod biến mất khỏi ô chọn.
"""
from types import SimpleNamespace

from app.modules.category_assignee.service import assignable_staff
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_order.service import is_cost_row_changed
from app.modules.user.model import User


def test_legacy_null_stage_amount_equals_zero_sent_by_v1():
    row = SimpleNamespace(estimate_amount=None, provisional_amount=None, final_amount=1500.0,
                          manual_allocation="", line_stage=3)
    same = {"estimate_amount": 0, "provisional_amount": 0, "final_amount": 1500}
    assert not is_cost_row_changed(row, {}, same, {}), "0 do v1 gửi = ô trống, không phải sửa"
    changed = {"estimate_amount": 0, "provisional_amount": 0, "final_amount": 1600}
    assert is_cost_row_changed(row, {}, changed, {}), "đổi số Quyết toán thật thì vẫn phải chặn"
    typed = {"estimate_amount": 200, "provisional_amount": 0, "final_amount": 1500}
    assert is_cost_row_changed(row, {}, typed, {}), "gõ số vào ô đang trống vẫn là sửa"


def test_assigned_scope_buyers_are_offered(db, seed, cap_quyen):
    dept = db.query(Department).filter(Department.code == "DEPT01").first()
    emp = Employee(code="PURSTAFF01", full_name="NV thu mua được giao", company_id=seed.company_id,
                   department_id=dept.id, is_active=True)
    db.add(emp)
    db.flush()
    u = User(email="PURSTAFF01", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(u)
    db.flush()
    cap_quyen(u.id, "purchase_request", scope="assigned", read=True, write=True)
    db.commit()
    ticket = SimpleNamespace(handler_dept_id=0, department_id=dept.id)
    assert "PURSTAFF01" in [e.code for e in assignable_staff(db, ticket)]
