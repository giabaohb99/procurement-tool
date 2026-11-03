"""Dòng dữ liệu của báo cáo "Làm việc vào ngày lễ, ngày nghỉ" (duoc-CR-717, khóa 30).

Nguồn = `tab_leave_comp_request` (phiếu xin nghỉ bù, CR-715): mỗi phiếu là MỘT người-ngày đã đi làm vào
ngày lễ HOẶC ngày nghỉ theo lịch. Loại ngày được phân lại lúc xem theo lịch ngày lễ HIỆN HÀNH
(`holiday_names_many`): có tên ngày lễ → 1, không → 2 (ngày nghỉ theo lịch).

Số truy vấn CỐ ĐỊNH mỗi lần `load_rows`: 1 câu phiếu + 1 câu ngày lễ (mọi pháp nhân một lượt) + 1 câu tên NV.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Query, Session

from app.modules.employee.model import Employee

from .constants import LeaveCompStatus
from .holiday_calendar import holiday_names_many
from .comp_request_model import LeaveCompRequest

MAX_PERIOD_DAYS = 366
PERIOD_MSG = "Kỳ báo cáo tối đa 366 ngày — hãy chọn kỳ ngắn hơn"
DAY_KIND_ALL, DAY_KIND_HOLIDAY, DAY_KIND_OFFDAY = 0, 1, 2
DAY_KIND_LABELS = {DAY_KIND_HOLIDAY: "Ngày lễ", DAY_KIND_OFFDAY: "Ngày nghỉ theo lịch"}
WEEKDAYS = ("Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật")


@dataclass(frozen=True)
class HolidayWorkRow:
    code: str
    employee_id: int
    employee_code: str
    employee_name: str
    company_id: int
    department_id: int          # phòng GHI TRÊN PHIẾU (phòng lúc đi làm)
    work_date: date
    days: float
    status: int
    day_kind: int               # 1 ngày lễ · 2 ngày nghỉ theo lịch
    holiday_name: str


def check_period(d_from: date, d_to: date) -> None:
    if (d_to - d_from).days + 1 > MAX_PERIOD_DAYS:
        raise HTTPException(422, PERIOD_MSG)


def valid_day_kind(raw) -> int:
    """`day_kind` từ query string: rỗng → 0 (tất cả); ngoài 0/1/2 → 422."""
    s = str(raw if raw is not None else "").strip() or "0"
    if s not in ("0", "1", "2"):
        raise HTTPException(422, "day_kind phải là 0 (tất cả), 1 (ngày lễ) hoặc 2 (ngày nghỉ theo lịch)")
    return int(s)


def valid_flag(raw) -> bool:
    return str(raw or "").strip().lower() in ("1", "true", "yes", "on")


def load_rows(db: Session, comp_q: Query, d_from: date, d_to: date, include_pending: bool,
              day_kind: int) -> list[HolidayWorkRow]:
    """`comp_q` đã qua `apply_scope` (+ lọc công ty/phòng). Phiếu nháp / từ chối / trả về / hủy / xóa KHÔNG BAO GIỜ vào."""
    check_period(d_from, d_to)
    statuses = [int(LeaveCompStatus.APPROVED)] + ([int(LeaveCompStatus.PENDING)] if include_pending else [])
    recs = (comp_q.filter(LeaveCompRequest.is_deleted.is_(False), LeaveCompRequest.status.in_(statuses),
                          LeaveCompRequest.work_date >= d_from, LeaveCompRequest.work_date <= d_to)
            .with_entities(LeaveCompRequest.code, LeaveCompRequest.employee_id, LeaveCompRequest.company_id,
                           LeaveCompRequest.department_id, LeaveCompRequest.work_date, LeaveCompRequest.days,
                           LeaveCompRequest.status).all())
    if not recs:
        return []
    holidays = holiday_names_many(db, {r.company_id or 0 for r in recs}, d_from, d_to)
    emp = {i: (c, n) for i, c, n in db.query(Employee.id, Employee.code, Employee.full_name)
           .filter(Employee.id.in_({r.employee_id for r in recs})).all()}
    out = []
    for r in recs:
        name = holidays.get(r.company_id or 0, {}).get(r.work_date, "")
        kind = DAY_KIND_HOLIDAY if name else DAY_KIND_OFFDAY
        if day_kind and kind != day_kind:
            continue
        code, full = emp.get(r.employee_id, ("", ""))
        out.append(HolidayWorkRow(r.code, r.employee_id or 0, code, full, r.company_id or 0, r.department_id or 0,
                                  r.work_date, float(r.days or 0), int(r.status), kind, name))
    return out
