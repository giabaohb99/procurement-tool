"""GHI phân bổ chính sách nghỉ phép (duoc-CR-717): tạo · sửa · xóa · hàng loạt + cấp / tính lại quỹ NĂM NAY.

Luật chốt (xem `plan.md` D1–D6): chỉ quỹ năm nay (`vn_today().year`) được đụng, chỉ cột `allocated_days`, năm đã qua
không bao giờ. Mọi hàm ở đây KHÔNG commit — nơi gọi (controller) commit một lần để cả lô nguyên khối; vì thế hàng loạt
KHÔNG dùng savepoint (nhả savepoint làm `change_tracker` đóng dấu "đã commit" sớm — review M3): lô hoặc xong hết hoặc không gì.

⚠️ MySQL REPEATABLE READ (review H1): sau `lock_employees` MỌI lần đọc phân bổ / dòng gói / dòng quỹ trên đường ghi
phải là ĐỌC CÓ KHÓA (`policy_allocation.with_row_lock`) — đọc thường vẫn thấy ảnh chụp cũ nên không thấy phân bổ vừa
được người khác commit.
"""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.modules.employee.model import Employee

from . import policy_allocation
from .policy_allocation import with_row_lock
from .policy_allocation_math import overlaps_year
from .policy_assignment_balances import (empty_balances, merge_balances, reconcile_plan,
                                         reconcile_policy_types)
from .policy_assignment_plan import (CONFLICT_HTTP, PlanContext, PlanItem, find_overlaps, overlap_message,
                                     plan_change)
from .policy_model import LeavePolicy, LeavePolicyAssignment

ENTITY = "leave_policy_assignment"


def lock_employees(db: Session, employee_ids: list[int]) -> None:
    """Khóa hàng hồ sơ (theo id tăng dần, tránh khóa chéo) để hai HR phân bổ cùng người không cùng qua chốt chồng ngày."""
    if not employee_ids or db.bind is None or db.bind.dialect.name not in policy_allocation.ROW_LOCK_DIALECTS:
        return
    db.query(Employee.id).filter(Employee.id.in_(sorted(set(employee_ids)))).order_by(
        Employee.id).with_for_update().all()


def lock_policy(db: Session, policy_id: int) -> LeavePolicy:
    """Khóa DÙNG CHUNG dòng gói + nạp lại bản mới nhất; gói vừa bị xóa → 404. Xóa gói khóa ĐỘC QUYỀN cùng dòng
    (`policy_controller`) nên "xóa gói" và "tạo phân bổ" không thể cùng qua chốt (review L4)."""
    policy = with_row_lock(db, db.query(LeavePolicy).filter(LeavePolicy.id == policy_id)).first()
    if policy is None:
        raise HTTPException(404, "Không tìm thấy chính sách nghỉ phép")
    return policy


def lock_assignment(db: Session, assignment_id: int) -> LeavePolicyAssignment:
    """Nạp lại phân bổ có khóa độc quyền (bản ở phiên có thể đã cũ / đã bị xóa) — mất rồi → 404."""
    obj = with_row_lock(db, db.query(LeavePolicyAssignment).filter(LeavePolicyAssignment.id == assignment_id),
                        exclusive=True).first()
    if obj is None:
        raise HTTPException(404, "Không tìm thấy phân bổ")
    return obj


def raise_for_conflict(item: PlanItem) -> None:
    if item.conflict:
        raise HTTPException(CONFLICT_HTTP[item.conflict], item.message)


def add_assignment(db: Session, user, item: PlanItem, policy: LeavePolicy, from_date: date, to_date: date | None,
                   note: str) -> LeavePolicyAssignment:
    """Thêm MỘT phân bổ đã qua `plan_change` (không còn xung đột) + đóng phân bổ cũ nếu có. Không flush."""
    employee = item.employee
    if item.closed is not None:
        item.closed.effective_to = from_date - timedelta(days=1)
        item.closed.updated_by = user.id
        audit_record(db, user.id, ENTITY, item.closed.id, "update",
                     f"Kết thúc phân bổ chính sách cũ của {employee.full_name} vào {item.closed.effective_to:%d/%m/%Y}",
                     commit=False)
    assignment = LeavePolicyAssignment(
        employee_id=employee.id, company_id=getattr(employee, "company_id", 0) or 0, policy_id=policy.id,
        effective_from=from_date, effective_to=to_date, note=note or "",
        created_by=user.id, updated_by=user.id)
    db.add(assignment)
    return assignment


def _audit_created(db: Session, user, assignment: LeavePolicyAssignment, item: PlanItem, policy: LeavePolicy) -> None:
    audit_record(db, user.id, ENTITY, assignment.id, "create",
                 f"Phân bổ chính sách {policy.name} cho {item.employee.full_name} từ {assignment.effective_from:%d/%m/%Y}",
                 commit=False)


def _write_plan(db: Session, user, items: list[PlanItem], ctx: PlanContext, policy: LeavePolicy, from_date: date,
                to_date: date | None, note: str, recalc: bool, year: int) -> list[tuple[LeavePolicyAssignment, dict]]:
    """Ghi các phân bổ của những `PlanItem` hết xung đột rồi tính quỹ — số truy vấn không tăng theo số người."""
    assignments = [add_assignment(db, user, it, policy, from_date, to_date, note) for it in items]
    db.flush()
    for assignment, item in zip(assignments, items):
        _audit_created(db, user, assignment, item, policy)
    parts = reconcile_plan(db, items, ctx, year, recalc=recalc, actor=user.id,
                           label=f"Phân bổ chính sách {policy.name}")
    return list(zip(assignments, parts))


def create_one(db: Session, user, employee, policy: LeavePolicy, from_date: date, to_date: date | None,
               note: str, recalc: bool, close_previous: bool, year: int, today: date, *,
               actor_employee_id: int, actor_is_admin: bool) -> tuple[LeavePolicyAssignment, dict]:
    lock_employees(db, [employee.id])
    policy = lock_policy(db, policy.id)
    items, ctx = plan_change(db, [employee], policy, from_date, to_date, close_previous, year, today,
                             actor_employee_id=actor_employee_id, actor_is_admin=actor_is_admin, lock=True)
    raise_for_conflict(items[0])
    return _write_plan(db, user, items, ctx, policy, from_date, to_date, note, recalc, year)[0]


def create_bulk(db: Session, user, employees: list, policy: LeavePolicy, from_date: date, to_date: date | None,
                recalc: bool, close_previous: bool, year: int, today: date, *, actor_employee_id: int,
                actor_is_admin: bool) -> dict:
    """Người vướng chốt nghiệp vụ → `skipped`; còn lại ghi trong MỘT giao dịch, không savepoint. Không commit."""
    lock_employees(db, [e.id for e in employees])
    policy = lock_policy(db, policy.id)
    items, ctx = plan_change(db, employees, policy, from_date, to_date, close_previous, year, today,
                             actor_employee_id=actor_employee_id, actor_is_admin=actor_is_admin, lock=True)
    skipped = [{"employee_id": it.employee.id, "name": it.employee.full_name, "reason": it.message}
               for it in items if it.conflict]
    ok = [it for it in items if not it.conflict]
    balances = empty_balances()
    for item, (_assignment, part) in zip(ok, _write_plan(db, user, ok, ctx, policy, from_date, to_date, "", recalc,
                                                         year) if ok else []):
        merge_balances(balances, part, item.employee.id)
    audit_record(db, user.id, ENTITY, 0, "create",
                 f"Phân bổ hàng loạt chính sách {policy.name} từ {from_date:%d/%m/%Y}: tạo {len(ok)}, bỏ qua {len(skipped)}",
                 commit=False)
    return {"created": len(ok), "skipped": skipped, "balances": balances}


def update_one(db: Session, user, obj: LeavePolicyAssignment, values: dict, recalc: bool, year: int) -> dict:
    """Sửa `effective_to` / `note`. Kéo dài thì kiểm chồng ngày lại; đổi `effective_to` thì tính lại các loại của gói."""
    employee = db.query(Employee).filter(Employee.id == obj.employee_id).first()
    if employee is None:
        raise HTTPException(404, "Không tìm thấy nhân sự của phân bổ này")
    lock_employees(db, [obj.employee_id])
    obj = lock_assignment(db, obj.id)
    old_to = obj.effective_to
    new_to = values["effective_to"] if "effective_to" in values else old_to
    if new_to is not None and new_to < obj.effective_from:
        raise HTTPException(422, "\"Đến ngày\" không được trước \"Từ ngày\".")
    others = policy_allocation.load_assignments(db, [obj.employee_id], lock=True)[obj.employee_id]
    clash = find_overlaps(others, obj.effective_from, new_to, exclude_id=obj.id)
    if clash:
        name = db.query(LeavePolicy.name).filter(LeavePolicy.id == clash[0].policy_id).scalar() or ""
        raise HTTPException(409, overlap_message(employee, clash[0], name))
    if values.get("note") is not None:
        obj.note = values["note"]
    obj.effective_to = new_to
    obj.updated_by = user.id
    db.flush()
    audit_record(db, user.id, ENTITY, obj.id, "update", "Sửa phân bổ chính sách nghỉ phép", commit=False)
    if new_to == old_to or not (
            overlaps_year(obj.effective_from, old_to, year) or overlaps_year(obj.effective_from, new_to, year)):
        return empty_balances()
    return reconcile_policy_types(db, user, employee, obj.policy_id, year, recalc=recalc, create_missing=True)


def delete_one(db: Session, user, obj: LeavePolicyAssignment, recalc: bool, year: int) -> dict:
    """Xóa phân bổ; `recalc` thì các loại của gói quay về luật của loại (nếu không còn phân bổ khác phủ tháng đó).
    Hồ sơ nhân sự đã mất vẫn xóa được (dọn phân bổ mồ côi) — chỉ không tính lại quỹ."""
    employee_id = obj.employee_id
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    lock_employees(db, [employee_id])
    obj = lock_assignment(db, obj.id)
    touches = overlaps_year(obj.effective_from, obj.effective_to, year)
    policy_id, assignment_id = obj.policy_id, obj.id
    db.delete(obj)
    db.flush()
    audit_record(db, user.id, ENTITY, assignment_id, "delete", "Xóa phân bổ chính sách nghỉ phép", commit=False)
    if not (recalc and touches and employee is not None):
        return empty_balances()
    return reconcile_policy_types(db, user, employee, policy_id, year, recalc=True, create_missing=False)
