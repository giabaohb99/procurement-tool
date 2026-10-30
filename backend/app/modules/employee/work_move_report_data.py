"""Nạp dữ liệu báo cáo D1 "Điều chuyển & bổ nhiệm" (khóa 24, duoc-CR-688) từ
`tab_employee_work_history`: mỗi dòng quá trình công tác là một hàng `MoveRow`.

Phạm vi: `apply_scope(Employee, 'employee', action)` áp lên NGƯỜI của dòng (join `Employee`), rồi
`company_id`/`department_id` lọc theo hồ sơ HIỆN TẠI của người đó — chỉ thu hẹp thêm.

"Phòng đi" = phòng của dòng NHÓM CHÍNH liền trước cùng người (bỏ dòng không khai phòng); không có
thì, với dòng CHƯA ÁP vào hồ sơ (trừ Tuyển dụng), lấy phòng hồ sơ hiện tại — CHỈ khi không có dòng nhóm
chính nào ĐÃ ÁP muộn hơn có khai phòng (dòng đó đã đổi phòng hiện tại nên không còn là phòng "trước");
còn lại 0 = "(Chưa rõ)". Số truy vấn CỐ ĐỊNH: 1 (dòng) + 1 mỗi 900 người (lịch sử để tra phòng đi).

⚠️ KHÔNG đọc/trả tệp quyết định (gác bằng `employee_sensitive.read`) — chỉ số quyết định.
"""
from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.hr_work_history_codes import MAIN_TRACK, WorkEventType
from app.core.report_period import range_filter
from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.employee.report_headcount_events import not_resigned_cond
from app.modules.employee.work_history_model import EmployeeWorkHistory as H

_CHUNK = 900
_NO_ORIGIN_EVENTS = {int(WorkEventType.HIRE)}
_MAIN = {int(t) for t in MAIN_TRACK}


@dataclass(frozen=True)
class MoveRow:
    line_id: int
    employee_id: int
    code: str
    name: str
    hire_date: date | None
    event_type: int
    from_date: date
    to_date: date | None
    company_id: int
    department_id: int          # phòng ĐẾN (0 = không khai)
    from_department_id: int     # phòng ĐI (0 = chưa rõ)
    position: str
    decision_no: str


def _origin_map(db: Session, employee_ids: list[int]) -> tuple[dict[int, list[tuple]], dict[int, list[tuple]]]:
    """({employee_id: [(from_date, line_id, department_id)] đã sắp} cho dòng nhóm chính có khai phòng,
    cùng cấu trúc ấy nhưng chỉ dòng ĐÃ ÁP vào hồ sơ)."""
    out: dict[int, list[tuple]] = defaultdict(list)
    applied: dict[int, list[tuple]] = defaultdict(list)
    for i in range(0, len(employee_ids), _CHUNK):
        for r in db.query(H.id, H.employee_id, H.from_date, H.department_id, H.applied_at).filter(
                H.employee_id.in_(employee_ids[i:i + _CHUNK]), H.event_type.in_(_MAIN),
                H.department_id > 0).all():
            out[r.employee_id].append((r.from_date, r.id, r.department_id))
            if r.applied_at is not None:
                applied[r.employee_id].append((r.from_date, r.id, r.department_id))
    for lst in (*out.values(), *applied.values()):
        lst.sort()
    return out, applied


def load_lines(db: Session, user, prof: dict, conditions: list, *, company_id: int | None = None,
               department_id: int | None = None, action: str = "read",
               with_origin: bool = True) -> list[MoveRow]:
    """Dòng quá trình công tác thỏa `conditions` (biểu thức SQL trên `H`/`Employee`)."""
    q = (db.query(H.id, H.employee_id, H.event_type, H.from_date, H.to_date, H.company_id,
                  H.department_id, H.position_label, H.decision_no, H.applied_at,
                  Employee.code, Employee.full_name, Employee.hire_date,
                  Employee.department_id.label("current_dept"))
         .join(Employee, Employee.id == H.employee_id))
    q = apply_scope(q, Employee, "employee", user, prof, action)
    if company_id is not None:
        q = q.filter(Employee.company_id == company_id)
    if department_id is not None:
        q = q.filter(Employee.department_id == department_id)
    lines = q.filter(*conditions).all()
    origins, applied = (_origin_map(db, sorted({r.employee_id for r in lines}))
                        if with_origin and lines else ({}, {}))
    out = []
    for r in lines:
        prev = origins.get(r.employee_id, [])
        pos = bisect_left(prev, (r.from_date, r.id, 0))   # dòng liền trước = đứng trước (ngày, id)
        if pos:
            origin = prev[pos - 1][2]
        elif with_origin and r.applied_at is None and r.event_type not in _NO_ORIGIN_EVENTS:
            later = applied.get(r.employee_id, [])    # có dòng đã áp muộn hơn -> phòng hiện tại đã bị đổi
            origin = 0 if later and later[-1][:2] > (r.from_date, r.id) else (r.current_dept or 0)
        else:
            origin = 0
        out.append(MoveRow(r.id, r.employee_id, r.code or "", r.full_name or "", r.hire_date,
                           r.event_type, r.from_date, r.to_date, r.company_id or 0,
                           r.department_id or 0, origin, r.position_label or "", r.decision_no or ""))
    return out


def period_lines(db: Session, user, prof: dict, d_from: date, d_to: date, **kw) -> list[MoveRow]:
    """Dòng có `from_date` rơi trong kỳ — ĐÃ ÁP lẫn CHƯA ÁP đều tính."""
    return load_lines(db, user, prof, [range_filter(H.from_date, "date", d_from, d_to)], **kw)


def concurrent_lines(db: Session, user, prof: dict, as_of: date, expiring_within: int | None = None,
                     **kw) -> list[MoveRow]:
    """Kiêm nhiệm đang hiệu lực tại `as_of` (người chưa nghỉ); `expiring_within` ngày → chỉ dòng có
    `to_date` rơi trong [as_of, as_of + n]."""
    cond = [H.event_type == int(WorkEventType.CONCURRENT), H.from_date <= as_of,
            (H.to_date.is_(None)) | (H.to_date >= as_of), not_resigned_cond(as_of)]
    if expiring_within is not None:
        cond.append(H.to_date.isnot(None) & (H.to_date <= as_of + timedelta(days=expiring_within)))
    return load_lines(db, user, prof, cond, **kw)
