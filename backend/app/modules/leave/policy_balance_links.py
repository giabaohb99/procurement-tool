"""Nối PHÂN BỔ CHÍNH SÁCH với QUỸ PHÉP NĂM (duoc-CR-745) — kiểu mục *Leaves* / liên kết ngược của ERPNext.

Hai màn trước đây không nhìn thấy nhau: phân bổ xong chỉ biết quỹ đổi ra sao ở lúc xem trước, còn bảng Quỹ phép năm
không nói hạn mức lấy theo chính sách nào. Ba hàm ở đây chỉ ĐỌC, mỗi hàm số truy vấn cố định (không tra từng dòng):

- `quotas_for_assignments` — danh sách phân bổ: hạn mức năm nay của các loại nghỉ trong gói + id dòng quỹ để bấm sang.
- `policy_names_for_balances` — danh sách dòng quỹ: chính sách quyết định hạn mức của ĐÚNG loại nghỉ đó trong năm đó.
- `policy_names_for_year` — ma trận theo nhân sự: chính sách áp trong năm đang xem.

Luật chọn chính sách khớp `policy_allocation_math`: phân bổ chạm năm Y và gói CÓ khai loại nghỉ đó thì mới quyết định
hạn mức của loại đó; loại vắng trong gói vẫn theo luật của loại (giao diện ghi *Theo loại nghỉ*).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.scoping import apply_scope

from .balance_model import LeaveBalance
from .catalog_model import LeaveType
from .policy_allocation import load_lines
from .policy_allocation_math import overlaps_year
from .policy_model import LeavePolicy, LeavePolicyAssignment

ENTITY = "leave_balance"
NAME_JOINER = " → "


def _assignments_by_employee(db: Session, employee_ids: set[int]) -> dict[int, list[LeavePolicyAssignment]]:
    out: dict[int, list[LeavePolicyAssignment]] = {}
    if not employee_ids:
        return out
    rows = (db.query(LeavePolicyAssignment).filter(LeavePolicyAssignment.employee_id.in_(employee_ids))
            .order_by(LeavePolicyAssignment.effective_from).all())
    for a in rows:
        out.setdefault(a.employee_id, []).append(a)
    return out


def _policy_names(db: Session, policy_ids: set[int]) -> dict[int, str]:
    if not policy_ids:
        return {}
    return dict(db.query(LeavePolicy.id, LeavePolicy.name).filter(LeavePolicy.id.in_(policy_ids)).all())


def _join_names(policy_ids: list[int], names: dict[int, str]) -> str:
    """Tên các gói theo thứ tự ngày bắt đầu, bỏ trùng (đổi qua đổi lại cùng một gói chỉ ghi một lần liền nhau)."""
    out: list[str] = []
    for pid in policy_ids:
        name = names.get(pid, "")
        if name and (not out or out[-1] != name):
            out.append(name)
    return NAME_JOINER.join(out)


def policy_names_for_balances(db: Session, rows: list[LeaveBalance]) -> dict[int, str]:
    """`{balance_id: tên chính sách}`; dòng không có chính sách nào quyết định loại nghỉ đó thì không có khóa.

    3 truy vấn cho cả trang: phân bổ của các người trên trang + dòng gói + tên gói."""
    assigns = _assignments_by_employee(db, {r.employee_id for r in rows})
    policy_ids = {a.policy_id for per in assigns.values() for a in per}
    lines = load_lines(db, policy_ids)
    names = _policy_names(db, policy_ids)
    out: dict[int, str] = {}
    for r in rows:
        hits = [a.policy_id for a in assigns.get(r.employee_id, [])
                if overlaps_year(a.effective_from, a.effective_to, r.year)
                and r.leave_type_id in lines.get(a.policy_id, {})]
        label = _join_names(hits, names)
        if label:
            out[r.id] = label
    return out


def policy_names_for_year(db: Session, employee_ids: list[int], year: int) -> dict[int, str]:
    """`{employee_id: tên chính sách}` của các phân bổ chạm năm `year` — 2 truy vấn cho cả trang ma trận."""
    assigns = _assignments_by_employee(db, set(employee_ids))
    names = _policy_names(db, {a.policy_id for per in assigns.values() for a in per})
    out: dict[int, str] = {}
    for emp_id, per in assigns.items():
        label = _join_names([a.policy_id for a in per if overlaps_year(a.effective_from, a.effective_to, year)], names)
        if label:
            out[emp_id] = label
    return out


def quotas_for_assignments(db: Session, rows: list[LeavePolicyAssignment], user, prof: dict,
                           year: int) -> dict[int, list[dict]]:
    """`{assignment_id: [{leave_type_id, leave_type_name, allocated_days, balance_id}]}` cho phân bổ CHẠM năm `year`.

    Số là `allocated_days` của dòng quỹ năm đó (hạn mức đang cấp — có thể đã trộn nhiều gói nếu đổi giữa năm).
    Chưa có dòng quỹ → `allocated_days = None`, `balance_id = 0` (giao diện ghi *chưa cấp*). Dòng quỹ đọc qua
    `apply_scope(leave_balance)` nên không bao giờ lộ số của người ngoài phạm vi. 3 truy vấn cho cả trang.
    """
    touching = [a for a in rows if overlaps_year(a.effective_from, a.effective_to, year)]
    if not touching:
        return {}
    lines = load_lines(db, {a.policy_id for a in touching})
    type_ids = {t for per in lines.values() for t in per}
    types = {t.id: t.name for t in db.query(LeaveType.id, LeaveType.name, LeaveType.sort_order)
             .filter(LeaveType.id.in_(type_ids or {0}), LeaveType.counts_balance.is_(True))
             .order_by(LeaveType.sort_order, LeaveType.id).all()}
    balances: dict[tuple[int, int], LeaveBalance] = {}
    if types:
        query = apply_scope(db.query(LeaveBalance), LeaveBalance, ENTITY, user, prof).filter(
            LeaveBalance.year == year, LeaveBalance.employee_id.in_({a.employee_id for a in touching}),
            LeaveBalance.leave_type_id.in_(set(types)))
        balances = {(b.employee_id, b.leave_type_id): b for b in query.all()}
    out: dict[int, list[dict]] = {}
    for a in touching:
        items = []
        for tid, name in types.items():          # giữ thứ tự loại nghỉ như danh mục
            if tid not in lines.get(a.policy_id, {}):
                continue
            b = balances.get((a.employee_id, tid))
            items.append({"leave_type_id": tid, "leave_type_name": name,
                          "allocated_days": float(b.allocated_days or 0.0) if b is not None else None,
                          "balance_id": b.id if b is not None else 0})
        out[a.id] = items
    return out

