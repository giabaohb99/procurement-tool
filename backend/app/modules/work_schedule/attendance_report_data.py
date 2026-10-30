"""Nạp "người-ngày" cho báo cáo C3 "Có mặt theo ngày" (duoc-CR-689, khóa 26).

Mỗi nhân sự × mỗi ngày trong kỳ (chỉ ngày ≤ hôm nay giờ VN) sinh ra MỘT `DayRow` nếu hôm đó
người ấy PHẢI LÀM (theo lịch làm việc riêng của họ, không phải ngày lễ, đang làm việc hôm đó):
  - `scheduled` = công tối đa của ngày (1 ngày làm trọn, 0,5 ngày làm nửa buổi);
  - `on_leave`  = phần công nghỉ có đơn ĐÃ DUYỆT phủ (nửa buổi 0,5; đơn theo giờ tính theo tỉ lệ giờ),
    không bao giờ vượt `scheduled`;
  - `present`   = `scheduled − on_leave`.

Số truy vấn CỐ ĐỊNH, không tăng theo số người/số đơn: nhân sự (1) · lịch làm việc (3) · ngày lễ (1) ·
đơn nghỉ (1) · khoảng nghỉ (1-2). Đơn nghỉ đọc qua phạm vi `leave_request` của người xem.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.vn_time import vn_today
from app.modules.employee.model import Employee
from app.modules.employee.report_headcount_events import effective_hire_date, not_resigned_cond
from app.modules.employee.service import STATUS_RESIGNED
from app.modules.leave.constants import LR_APPROVED, SESSION_HOURLY
from app.modules.leave.holiday_calendar import date_range, holiday_names_many
from app.modules.leave.period_spans import periods_by_request
from app.modules.leave.request_model import LeaveRequest
from app.modules.leave.workday_service import leave_mask
from app.modules.work_schedule.day_rules import AM, PM, day_capacity, day_hours, work_mask, worked_hours
from app.modules.work_schedule.resolver_many import load_day_plans_many

MAX_PERIOD_DAYS = 92
PERIOD_MSG = (f"Báo cáo \"Có mặt theo ngày\" chỉ xem được tối đa {MAX_PERIOD_DAYS} ngày một lần "
              "(mỗi người × mỗi ngày là một dòng tính). Hãy chọn kỳ ngắn hơn, ví dụ một tháng hoặc một quý.")


@dataclass(slots=True)
class DayRow:
    """Một người trong một ngày PHẢI LÀM."""
    employee_id: int
    code: str
    name: str
    company_id: int
    department_id: int
    day: date
    scheduled: float
    on_leave: float
    present: float
    leaves: tuple = ()          # ((id loại nghỉ, nhãn buổi), ...) — chỉ để dựng danh sách `/rows`


def check_period(d_from: date, d_to: date) -> None:
    if (d_to - d_from).days + 1 > MAX_PERIOD_DAYS:
        raise HTTPException(422, PERIOD_MSG)


def _session_label(mask: int) -> str:
    return {AM | PM: "Cả ngày", AM: "Buổi sáng", PM: "Buổi chiều"}.get(mask, "")


def _leave_by_day(db: Session, leave_q, emp_ids_q, d_from: date, d_to: date) -> dict:
    """`{(employee_id, ngày): [(loại nghỉ, mask nửa buổi, (từ giờ, đến giờ) | None)]}` — 1 truy vấn đơn
    + 1-2 truy vấn khoảng. Đơn nhiều khoảng đọc theo TỪNG KHOẢNG (khe giữa các khoảng không nghỉ)."""
    reqs = (leave_q.filter(LeaveRequest.status == LR_APPROVED, LeaveRequest.from_date <= d_to,
                           LeaveRequest.to_date >= d_from, LeaveRequest.employee_id.in_(emp_ids_q))
            .with_entities(LeaveRequest.id, LeaveRequest.employee_id, LeaveRequest.leave_type_id,
                           LeaveRequest.from_time, LeaveRequest.to_time).all())
    periods = periods_by_request(db, [r.id for r in reqs])
    out: dict = {}
    for r in reqs:
        for p in periods.get(r.id, []):
            hourly = p.from_session == SESSION_HOURLY and r.from_time and r.to_time
            for day in date_range(max(p.from_date, d_from), min(p.to_date, d_to)):
                mask = leave_mask(day, p.from_date, p.to_date, p.from_session, p.to_session)
                out.setdefault((r.employee_id, day), []).append(
                    (r.leave_type_id or 0, mask, (r.from_time, r.to_time) if hourly else None))
    return out


def _on_leave(entries, spec) -> tuple[float, tuple]:
    """(công nghỉ trong ngày, nhãn từng khoản) cho một người-ngày; không vượt công tối đa."""
    cap, wmask = day_capacity(spec), work_mask(spec)
    mask, hours, labels = 0, 0.0, []
    for type_id, m, hr in entries:
        if hr is None:
            mask |= m & wmask
            labels.append((type_id, _session_label(m & wmask)))
        else:
            whole = day_hours(spec)
            if whole > 0:
                part = worked_hours(spec, hr[0], hr[1]) / whole * cap
                hours += part
                labels.append((type_id, f"Theo giờ {hr[0]:%H:%M}–{hr[1]:%H:%M}"))
    return min(0.5 * bin(mask).count("1") + hours, cap), tuple(l for l in labels if l[1])


def load_day_rows(db: Session, emp_q, leave_q, d_from: date, d_to: date, *, with_leave: bool = True
                  ) -> list[DayRow]:
    """Người-ngày của [d_from, d_to] (cắt ở hôm nay). `emp_q` đã qua phạm vi + lọc công ty/phòng ban;
    `leave_q` đã qua phạm vi `leave_request` (bỏ qua nếu `with_leave=False`)."""
    d_to = min(d_to, vn_today())
    if d_to < d_from:
        return []
    emps = (emp_q.filter(not_resigned_cond(d_from))
            .with_entities(Employee.id, Employee.code, Employee.full_name, Employee.company_id,
                           Employee.department_id, Employee.hire_date, Employee.created_at,
                           Employee.status, Employee.resign_date).all())
    if not emps:
        return []
    plans = load_day_plans_many(db, emps, d_from, d_to)
    holidays = holiday_names_many(db, {e.company_id or 0 for e in emps}, d_from, d_to)
    leaves = _leave_by_day(db, leave_q, emp_q.with_entities(Employee.id).subquery().select(),
                           d_from, d_to) if with_leave else {}
    days = list(date_range(d_from, d_to))
    out: list[DayRow] = []
    for e in emps:
        hired = effective_hire_date(e.hire_date, e.created_at)
        off = holidays.get(int(e.company_id or 0), {})
        for day in days:
            if (hired and hired > day) or (e.status == STATUS_RESIGNED and (e.resign_date is None or e.resign_date <= day)):
                continue
            spec, _sid = plans.at(e.id, day)
            cap = day_capacity(spec)
            if cap <= 0 or day in off:
                continue
            took, labels = _on_leave(leaves[(e.id, day)], spec) if (e.id, day) in leaves else (0.0, ())
            out.append(DayRow(e.id, e.code, e.full_name, int(e.company_id or 0), int(e.department_id or 0),
                              day, cap, took, cap - took, labels))
    return out
