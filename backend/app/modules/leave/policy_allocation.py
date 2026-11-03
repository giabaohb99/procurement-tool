"""NỐI phân bổ chính sách vào việc cấp quỹ (duoc-CR-717): nạp phân bổ từ CSDL rồi gọi hàm thuần.

`balance_service.ensure_balance` gọi `allocated_days` — điểm cấp quỹ DUY NHẤT. Không có phân bổ nào chồng năm
đó thì kết quả y hệt `prorate_allocation(resolve_quota(...))` cũ, và không tốn thêm truy vấn thứ hai.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from . import accrual_service
from .catalog_model import LeaveType
from .policy_allocation_math import AssignmentSpan, compute_allocated
from .policy_model import LeavePolicyAssignment, LeavePolicyLine

#  CSDL có khóa hàng thật. SQLite (bộ test) không có `FOR UPDATE`.
ROW_LOCK_DIALECTS = ("mysql", "postgresql")


def with_row_lock(db: Session, query, *, exclusive: bool = False):
    """Biến câu truy vấn thành ĐỌC CÓ KHÓA (đọc bản ghi mới nhất, không qua ảnh chụp REPEATABLE READ của MySQL).

    Bắt buộc cho mọi lần đọc phân bổ / dòng gói trên đường GHI sau `lock_employees` (review CR-717 H1): đọc thường vẫn
    thấy ảnh chụp cũ nên không thấy phân bổ vừa được người khác commit. `populate_existing` để bản đã nằm trong phiên
    cũng được nạp lại. SQLite không có khóa hàng nên giữ nguyên.
    """
    if db.bind is None or db.bind.dialect.name not in ROW_LOCK_DIALECTS:
        return query
    return query.with_for_update(read=not exclusive).populate_existing()


def build_spans(assignments: list[LeavePolicyAssignment],
                lines_by_policy: dict[int, dict[int, float]]) -> list[AssignmentSpan]:
    """Đổi các dòng phân bổ (đã nạp) thành `AssignmentSpan` kèm hạn mức theo loại của gói."""
    return [AssignmentSpan(a.effective_from, a.effective_to, lines_by_policy.get(a.policy_id, {}))
            for a in assignments]


def load_lines(db: Session, policy_ids: set[int], *, lock: bool = False) -> dict[int, dict[int, float]]:
    """`{policy_id: {leave_type_id: annual_days}}` — MỘT truy vấn cho cả nhóm gói (`lock` = đọc có khóa)."""
    out: dict[int, dict[int, float]] = {}
    if not policy_ids:
        return out
    query = db.query(LeavePolicyLine).filter(LeavePolicyLine.policy_id.in_(policy_ids))
    for line in (with_row_lock(db, query) if lock else query).all():
        out.setdefault(line.policy_id, {})[line.leave_type_id] = float(line.annual_days or 0.0)
    return out


def load_assignments(db: Session, employee_ids: list[int], year: int | None = None, *, lock: bool = False
                     ) -> dict[int, list[LeavePolicyAssignment]]:
    """Phân bổ của từng người (chỉ loại chồng năm `year` nếu có truyền) — MỘT truy vấn. `lock` = đọc có khóa."""
    out: dict[int, list[LeavePolicyAssignment]] = {i: [] for i in employee_ids}
    if not employee_ids:
        return out
    query = db.query(LeavePolicyAssignment).filter(LeavePolicyAssignment.employee_id.in_(employee_ids))
    if year is not None:
        query = query.filter(LeavePolicyAssignment.effective_from <= date(year, 12, 31),
                             (LeavePolicyAssignment.effective_to.is_(None))
                             | (LeavePolicyAssignment.effective_to >= date(year, 1, 1)))
    query = query.order_by(LeavePolicyAssignment.effective_from)
    for a in (with_row_lock(db, query) if lock else query).all():
        out.setdefault(a.employee_id, []).append(a)
    return out


def allocated_days(db: Session, leave_type: LeaveType, employee, year: int, *, lock: bool = False) -> float:
    """Hạn mức `allocated_days` để cấp quỹ năm `year` cho người này, đã tính phân bổ chính sách (nếu có).

    `lock=True` (đường GHI phân bổ) đọc phân bổ + dòng gói có khóa — xem `with_row_lock`."""
    base = accrual_service.resolve_quota(db, leave_type, employee)
    mode = int(leave_type.accrual_mode or 1)
    hire = getattr(employee, "hire_date", None)
    assignments = load_assignments(db, [employee.id], year, lock=lock)[employee.id]
    spans = build_spans(assignments, load_lines(db, {a.policy_id for a in assignments}, lock=lock)) \
        if assignments else []
    return compute_allocated(base, mode, hire, year, spans, leave_type.id)
