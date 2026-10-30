"""Ngày nghỉ có lương / không lương trong kỳ của từng người, cho hai cột nghỉ "trong kỳ" của Sổ quản lý lao động.

Chỉ đơn ĐÃ DUYỆT. Đơn gọn trong kỳ lấy nguyên `line.days`; đơn vắt qua biên kỳ chia ngày theo đúng luật của
báo cáo Nghỉ phép (`leave/report_day_split.py`, CR-686) nên số khớp với báo cáo đó. Loại nghỉ "không lương"
= `LeaveType.is_paid is False`; mọi loại còn lại tính là có lương.
Đơn nghỉ đi qua `apply_scope(..., "leave_request")` của người xem (nơi gọi dựng `leave_q`), nên người không
thấy đơn của ai thì không có số của người đó. Số truy vấn CỐ ĐỊNH (đơn · dòng · loại nghỉ · các truy vấn chia ngày), không tăng theo số người.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.modules.leave.constants import LR_APPROVED
from app.modules.leave.report_day_split import build_split_requests, overlapping_rows
from app.modules.leave.report_spec import load_type_info
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine


def load_leave_days(db: Session, leave_q, employee_ids: list[int], d_from: date, d_to: date) -> dict[int, tuple[float, float]]:
    """`leave_q` PHẢI đã qua `apply_scope`. `{employee_id: (ngày có lương, ngày không lương)}`; người không nghỉ thì vắng khỏi từ điển."""
    if not employee_ids:
        return {}
    rows = [r for r in overlapping_rows(leave_q.filter(LeaveRequest.employee_id.in_(employee_ids),
                                                      LeaveRequest.is_deleted.is_(False)),
                                        d_from, d_to, multi_day_only=False) if r.status == LR_APPROVED]
    if not rows:
        return {}
    _names, unpaid_types, calendar_types = load_type_info(db)
    lines: dict[int, list[tuple[int, float]]] = {}
    for ln in (db.query(LeaveRequestLine.request_id, LeaveRequestLine.leave_type_id, LeaveRequestLine.days)
               .filter(LeaveRequestLine.request_id.in_([r.id for r in rows])).all()):
        lines.setdefault(ln.request_id, []).append((ln.leave_type_id or 0, float(ln.days or 0)))
    crossing = [r for r in rows if r.from_date < d_from or r.to_date > d_to]
    share = {s.id: s.share_where(lambda d: d_from <= d <= d_to)
             for s in build_split_requests(db, crossing, calendar_types)}
    out: dict[int, list[float]] = {}
    for r in rows:
        f = share.get(r.id, 1.0)
        acc = out.setdefault(r.employee_id, [0.0, 0.0])
        for type_id, days in lines.get(r.id, []):
            acc[1 if type_id in unpaid_types else 0] += days * f
    return {k: (round(v[0], 2), round(v[1], 2)) for k, v in out.items()}
