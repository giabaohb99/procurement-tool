"""CẤP / TÍNH LẠI quỹ phép NĂM NAY sau khi phân bổ chính sách đổi (duoc-CR-717).

Chỉ cột `allocated_days` của dòng quỹ đã có bị đụng; dòng thiếu thì cấp mới. Hạn mức mới do `plan_change` tính sẵn
(`PlanItem.new_values`) nên đường hàng loạt có SỐ TRUY VẤN CỐ ĐỊNH theo số người: một câu đọc khóa dòng quỹ, một
lần ghi gộp (UPDATE / INSERT / nhật ký đi chung một flush) — review CR-717 M4. Không commit: nơi gọi commit một lần.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.audit import record as audit_record

from . import balance_service, policy_allocation
from .balance_model import LeaveBalance
from .catalog_model import LeaveType
from .policy_assignment_plan import PlanContext, PlanItem
from .policy_model import LeavePolicy

_EPS = 1e-9


def empty_balances() -> dict:
    return {"created": 0, "recalculated": [], "kept": 0, "negative_after": []}


def merge_balances(total: dict, part: dict, employee_id: int = 0) -> None:
    """Cộng kết quả quỹ của một người vào tổng của cả lô (kèm `employee_id` ở các dòng chi tiết)."""
    total["created"] += part["created"]
    total["kept"] += part["kept"]
    total["recalculated"] += [{**r, "employee_id": employee_id} for r in part["recalculated"]]
    total["negative_after"] += [{**r, "employee_id": employee_id} for r in part["negative_after"]]


def _lock_balance_rows(db: Session, employee_ids: list[int], type_ids: set[int], year: int
                       ) -> dict[tuple[int, int], LeaveBalance]:
    """MỘT câu khóa mọi dòng quỹ sắp ghi (`FOR UPDATE`, đọc bản mới nhất)."""
    if not employee_ids or not type_ids:
        return {}
    query = db.query(LeaveBalance).filter(
        LeaveBalance.year == year, LeaveBalance.employee_id.in_(employee_ids),
        LeaveBalance.leave_type_id.in_(type_ids)).order_by(LeaveBalance.employee_id, LeaveBalance.leave_type_id)
    return {(b.employee_id, b.leave_type_id): b
            for b in policy_allocation.with_row_lock(db, query, exclusive=True).all()}


def _new_balance(db: Session, employee, year: int, leave_type: LeaveType, allocated: float, actor: int,
                 seniority_cache: dict) -> LeaveBalance:
    """Dòng quỹ mới — cùng các cột `balance_service.ensure_balance` điền, chỉ khác: hạn mức do `plan_change` tính
    sẵn (đã gồm phân bổ vừa tạo) và bậc thâm niên tra một lần cho mỗi (loại, số năm)."""
    years = balance_service.seniority_years(getattr(employee, "hire_date", None), date(year, 1, 1))
    key = (leave_type.id, years)
    if key not in seniority_cache:
        seniority_cache[key] = balance_service.seniority_days(db, leave_type.id, years)
    row = LeaveBalance(employee_id=employee.id, year=year, leave_type_id=leave_type.id,
                       company_id=getattr(employee, "company_id", 0) or 0, allocated_days=allocated,
                       seniority_days=seniority_cache[key], created_by=actor, updated_by=actor)
    db.add(row)
    return row


def apply_values(db: Session, employee, values: dict[int, float], types: dict[int, LeaveType],
                 rows: dict, year: int, *, recalc: bool, actor: int, label: str, create_missing: bool,
                 seniority_cache: dict) -> dict:
    """Áp `values` ({loại: hạn mức mới}) lên dòng quỹ MỘT người. Không flush — nơi gọi flush một lần cho cả lô."""
    result = empty_balances()
    for tid in sorted(values):
        leave_type = types.get(tid)
        if leave_type is None:
            continue
        new_value, row = values[tid], rows.get((employee.id, tid))
        if row is None:
            if create_missing:
                rows[(employee.id, tid)] = _new_balance(db, employee, year, leave_type, new_value, actor,
                                                        seniority_cache)
                result["created"] += 1
            continue
        old_value = float(row.allocated_days or 0.0)
        if not recalc or abs(new_value - old_value) < _EPS:
            result["kept"] += 1
            continue
        row.allocated_days = new_value
        row.updated_by = actor
        audit_record(db, actor, "leave_balance", row.id, "update",
                     f"{label}: hạn mức {leave_type.name} năm {year} {old_value:g} → {new_value:g} ngày",
                     commit=False)
        result["recalculated"].append({"leave_type_id": tid, "before": old_value, "after": new_value})
        available = balance_service.available_days(db, row, leave_type=leave_type,
                                                   hire_date=getattr(employee, "hire_date", None))
        if available < -float(leave_type.max_negative_days or 0.0):
            result["negative_after"].append({"leave_type_id": tid, "available_days": available})
    return result


def reconcile_plan(db: Session, items: list[PlanItem], ctx: PlanContext, year: int, *, recalc: bool, actor: int,
                   label: str) -> list[dict]:
    """Kết quả quỹ cho từng `PlanItem` (cùng thứ tự). Dùng số `plan_change` đã tính — không truy vấn lại theo người."""
    type_ids = {t for it in items for t in it.type_ids if t in ctx.leave_types}
    rows = _lock_balance_rows(db, [it.employee.id for it in items], type_ids, year)
    cache: dict = {}
    parts = [apply_values(db, it.employee, it.new_values, ctx.leave_types, rows, year, recalc=recalc, actor=actor,
                          label=label, create_missing=True, seniority_cache=cache) for it in items]
    db.flush()
    return parts


def reconcile_policy_types(db: Session, user, employee, policy_id: int, year: int, *, recalc: bool,
                           create_missing: bool) -> dict:
    """Đường SỬA / XÓA một phân bổ: tính lại các loại của gói theo phân bổ HIỆN TẠI (đọc có khóa)."""
    lines = policy_allocation.load_lines(db, {policy_id}, lock=True).get(policy_id, {})
    name = db.query(LeavePolicy.name).filter(LeavePolicy.id == policy_id).scalar() or ""
    types = {t.id: t for t in db.query(LeaveType).filter(
        LeaveType.id.in_(set(lines) or {0}), LeaveType.is_active.is_(True),
        LeaveType.counts_balance.is_(True)).all()}
    values = {tid: policy_allocation.allocated_days(db, lt, employee, year, lock=True) for tid, lt in types.items()}
    rows = _lock_balance_rows(db, [employee.id], set(types), year)
    result = apply_values(db, employee, values, types, rows, year, recalc=recalc, actor=user.id,
                          label=f"Phân bổ chính sách {name}", create_missing=create_missing, seniority_cache={})
    db.flush()
    return result
