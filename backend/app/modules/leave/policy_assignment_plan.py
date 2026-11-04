"""LẬP KẾ HOẠCH một thay đổi phân bổ chính sách (duoc-CR-717) — DÙNG CHUNG cho xem trước và đường ghi.

`plan_change` KHÔNG ghi gì: dựng danh sách phân bổ SAU thay đổi trong bộ nhớ rồi tính hạn mức trước/sau bằng hàm
thuần. Đường ghi (`policy_assignment_service`) dùng đúng kết quả này để biết ai bị chốt chặn, phân bổ cũ nào phải
đóng, loại nghỉ nào cần cấp / tính lại — nên màn xem trước và lúc bấm lưu không thể nói hai điều khác nhau.

Số truy vấn CỐ ĐỊNH với mọi số người: phân bổ (1) + gói (1) + dòng gói (1) + loại nghỉ (1) + luật hạn mức (1) +
dòng quỹ năm nay (1). Hồ sơ nhân sự do nơi gọi nạp.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import Session

from . import accrual_service, policy_allocation
from .balance_model import LeaveBalance
from .catalog_model import LeaveType, LeaveTypeQuota
from .constants import LeavePolicyAssignmentState
from .policy_allocation_math import AssignmentSpan, compute_allocated, overlaps_year
from .policy_model import LeavePolicy, LeavePolicyAssignment

CONFLICT_OVERLAP = "overlap"
CONFLICT_SELF = "self"
CONFLICT_INACTIVE = "inactive"
#  Mã HTTP tương ứng khi đường ghi đổi chốt chặn thành lỗi.
CONFLICT_HTTP = {CONFLICT_OVERLAP: 409, CONFLICT_SELF: 403, CONFLICT_INACTIVE: 422}

SELF_MESSAGE = "Không tự phân bổ chính sách nghỉ phép cho chính mình — nhờ người khác trong phòng Nhân sự làm."
INACTIVE_MESSAGE = "Chính sách đã ngừng dùng — không phân bổ mới được."


def assignment_state(a: LeavePolicyAssignment, today: date) -> int:
    """Trạng thái DẪN XUẤT theo ngày (không lưu)."""
    if a.effective_from > today:
        return int(LeavePolicyAssignmentState.UPCOMING)
    if a.effective_to is not None and a.effective_to < today:
        return int(LeavePolicyAssignmentState.ENDED)
    return int(LeavePolicyAssignmentState.ACTIVE)


def _fmt_range(a: LeavePolicyAssignment) -> str:
    end = f"{a.effective_to:%d/%m/%Y}" if a.effective_to else "không thời hạn"
    return f"từ {a.effective_from:%d/%m/%Y} đến {end}"


def overlap_message(employee, other: LeavePolicyAssignment, policy_name: str) -> str:
    return f"Nhân sự {employee.full_name} đã có chính sách {policy_name} {_fmt_range(other)}."


def find_overlaps(assignments: list[LeavePolicyAssignment], from_date: date, to_date: date | None,
                  exclude_id: int = 0) -> list[LeavePolicyAssignment]:
    """Các phân bổ chồng ngày với `[from, to]` (đến trống = vô hạn)."""
    return [a for a in assignments
            if a.id != exclude_id
            and (to_date is None or a.effective_from <= to_date)
            and (a.effective_to is None or a.effective_to >= from_date)]


@dataclass
class PlanItem:
    employee: object
    conflict: str | None = None
    message: str = ""
    #  Phân bổ cũ phải đóng (`to = from − 1`) khi bật "Kết thúc chính sách cũ".
    closed: LeavePolicyAssignment | None = None
    #  Phân bổ đang hiệu lực hôm nay (để màn xem trước hiện "đang áp gói nào").
    current: LeavePolicyAssignment | None = None
    #  Loại nghỉ cần cấp / tính lại ở quỹ năm nay (rỗng khi phân bổ không chạm năm nay).
    type_ids: list[int] = field(default_factory=list)
    #  `[{leave_type_id, before, after}]` — chỉ những loại có số đổi.
    changes: list[dict] = field(default_factory=list)
    #  `{leave_type_id: hạn mức SAU thay đổi}` cho MỌI loại trong `type_ids` — đường ghi dùng thẳng, khỏi tính lại.
    new_values: dict[int, float] = field(default_factory=dict)


@dataclass
class PlanContext:
    """Dữ liệu tra cứu đã nạp một lượt — trả kèm để màn xem trước dựng tên gói / loại mà khỏi truy vấn lại."""

    policy_names: dict[int, str]
    leave_types: dict[int, LeaveType]


def plan_change(db: Session, employees: list, policy: LeavePolicy, from_date: date, to_date: date | None,
                close_previous: bool, year: int, today: date, *, actor_employee_id: int = 0,
                actor_is_admin: bool = False, lock: bool = False) -> tuple[list[PlanItem], PlanContext]:
    """`lock=True` (đường GHI, gọi SAU `lock_employees`) đọc phân bổ + dòng gói có khóa — xem `with_row_lock`."""
    ids = [e.id for e in employees]
    assigns = policy_allocation.load_assignments(db, ids, lock=lock)
    policy_ids = {policy.id} | {a.policy_id for rows in assigns.values() for a in rows}
    names = {p.id: p.name for p in db.query(LeavePolicy).filter(LeavePolicy.id.in_(policy_ids)).all()}
    lines = policy_allocation.load_lines(db, policy_ids, lock=lock)
    type_ids = {t for per in lines.values() for t in per}
    types = {t.id: t for t in db.query(LeaveType).filter(
        LeaveType.id.in_(type_ids or {0}), LeaveType.is_active.is_(True),
        LeaveType.counts_balance.is_(True)).all()}
    rules: dict[int, list[LeaveTypeQuota]] = {}
    for rule in db.query(LeaveTypeQuota).filter(LeaveTypeQuota.leave_type_id.in_(types or {0})).all():
        rules.setdefault(rule.leave_type_id, []).append(rule)
    balances = {(b.employee_id, b.leave_type_id): b for b in db.query(LeaveBalance).filter(
        LeaveBalance.year == year, LeaveBalance.employee_id.in_(ids or {0}),
        LeaveBalance.leave_type_id.in_(types or {0})).all()}
    new_quotas = lines.get(policy.id, {})

    items: list[PlanItem] = []
    for emp in employees:
        mine = assigns.get(emp.id, [])
        item = PlanItem(employee=emp, current=next(
            (a for a in mine if assignment_state(a, today) == int(LeavePolicyAssignmentState.ACTIVE)), None))
        items.append(item)
        if actor_employee_id and actor_employee_id == emp.id and not actor_is_admin:
            item.conflict, item.message = CONFLICT_SELF, SELF_MESSAGE
            continue
        if not policy.is_active:
            item.conflict, item.message = CONFLICT_INACTIVE, INACTIVE_MESSAGE
            continue
        overlapping = find_overlaps(mine, from_date, to_date)
        if overlapping:
            if close_previous and len(overlapping) == 1 and overlapping[0].effective_from < from_date:
                item.closed = overlapping[0]
            else:
                first = overlapping[0]
                item.conflict = CONFLICT_OVERLAP
                item.message = overlap_message(emp, first, names.get(first.policy_id, ""))
                continue

        touches = overlaps_year(from_date, to_date, year) or (
            item.closed is not None and overlaps_year(item.closed.effective_from, item.closed.effective_to, year))
        if not touches:
            continue
        before = policy_allocation.build_spans(mine, lines)
        after = [AssignmentSpan(a.effective_from,
                                from_date - timedelta(days=1) if a is item.closed else a.effective_to,
                                lines.get(a.policy_id, {})) for a in mine]
        after.append(AssignmentSpan(from_date, to_date, new_quotas))
        candidates = set(new_quotas) | (set(lines.get(item.closed.policy_id, {})) if item.closed else set())
        for tid in sorted(candidates & set(types)):
            lt = types[tid]
            base = accrual_service.pick_quota(rules.get(tid, []), lt, emp)
            mode, hire = int(lt.accrual_mode or 1), getattr(emp, "hire_date", None)
            old_value = compute_allocated(base, mode, hire, year, before, tid)
            new_value = compute_allocated(base, mode, hire, year, after, tid)
            item.type_ids.append(tid)
            item.new_values[tid] = new_value
            row = balances.get((emp.id, tid))
            shown_before = float(row.allocated_days or 0.0) if row is not None else old_value
            if abs(shown_before - new_value) > 1e-9:
                item.changes.append({"leave_type_id": tid, "before": shown_before, "after": new_value})
    return items, PlanContext(policy_names=names, leave_types=types)
