"""Dữ liệu ô E3 «Lịch nhắc trong tháng» của Tổng quan Nhân sự (duoc-CR-689).

Bốn nhóm, mỗi nhóm tối đa `GROUP_CAP` dòng (`total` vẫn là số thật, `truncated` báo bị cắt):
  - `birthdays`: sinh nhật trong tháng — CHỈ ngày + tháng (không năm sinh, không tuổi); chỉ khi người xem có
    `employee_sensitive.read`.
  - `anniversaries`: kỷ niệm 1 / 3 / 5 / 10 năm vào làm rơi vào tháng (theo `hire_date`).
  - `contracts` / `probations`: HĐLĐ / hợp đồng thử việc có ngày kết thúc trong tháng — dùng lại
    `labor_contract.expiry_service` (cùng bộ lọc với chuông cảnh báo: đã ký, chưa có HĐ nối tiếp, người còn làm,
    phạm vi `labor_contract`); chỉ khi có `labor_contract.read`. Ràng buộc của nguồn: cửa sổ tối đa
    `MAX_WINDOW_DAYS` (180) ngày kể từ hôm nay, nên tháng xa hơn thế chưa có dữ liệu (nhóm rỗng).
Nhóm không đủ quyền: `allowed=false`, rỗng — giao diện ẩn ô thay vì báo 0.

Số truy vấn CỐ ĐỊNH: nhân sự (sinh nhật) · nhân sự (kỷ niệm) · phòng ban · [3 truy vấn của `find_expiring`].
"""
from __future__ import annotations

import calendar
from datetime import date

from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractType
from app.modules.department.model import Department
from app.modules.labor_contract.expiry_service import MAX_WINDOW_DAYS, find_expiring

from .model import Employee
from .service import STATUS_RESIGNED

GROUP_CAP = 200
ANNIVERSARY_YEARS = (1, 3, 5, 10)


def _group(rows: list[dict], allowed: bool = True) -> dict:
    return {"allowed": allowed, "items": rows[:GROUP_CAP], "total": len(rows), "truncated": len(rows) > GROUP_CAP}


def _working(q):
    return q.filter(Employee.status != STATUS_RESIGNED, Employee.is_active == True)  # noqa: E712


def build(db: Session, employees_q, *, year: int, month: int, today: date, with_sensitive: bool,
          with_contracts: bool, user, profile: dict) -> dict:
    cols = (Employee.id, Employee.code, Employee.full_name, Employee.department_id)
    dept = {d.id: d.name for d in db.query(Department.id, Department.name).all()}

    def person(e, **extra) -> dict:
        return {"employee_id": e.id, "employee_code": e.code or "", "employee_name": e.full_name or "",
                "department": dept.get(e.department_id or 0, ""), "link": f"/hr/employees/{e.id}", **extra}

    birthdays: list[dict] = []
    if with_sensitive:
        rows = (_working(employees_q).filter(extract("month", Employee.date_of_birth) == month)
                .with_entities(*cols, Employee.date_of_birth).all())
        birthdays = sorted((person(e, day=e.date_of_birth.day, month=month) for e in rows),
                           key=lambda p: (p["day"], p["employee_code"]))

    wanted = {year - n: n for n in ANNIVERSARY_YEARS}
    rows = (_working(employees_q).filter(extract("month", Employee.hire_date) == month,
                                         extract("year", Employee.hire_date).in_(list(wanted)))
            .with_entities(*cols, Employee.hire_date).all())
    anniversaries = sorted((person(e, day=e.hire_date.day, month=month, years=wanted[e.hire_date.year],
                                   hire_date=e.hire_date.isoformat()) for e in rows),
                           key=lambda p: (p["day"], p["employee_code"]))

    contracts: list[dict] = []
    probations: list[dict] = []
    if with_contracts:
        month_end = date(year, month, calendar.monthrange(year, month)[1])
        window = max(0, min((month_end - today).days, MAX_WINDOW_DAYS))
        for c in find_expiring(db, today, user=user, profile=profile, within_days=window):
            if (c.end_date.year, c.end_date.month) != (year, month):
                continue
            item = {"employee_id": c.employee_id, "employee_code": c.employee_code,
                    "employee_name": c.employee_name, "contract_code": c.code, "contract_no": c.contract_no,
                    "end_date": c.end_date.isoformat(), "days_left": c.days_left, "level": c.level,
                    "link": c.alert_link().replace("/employees/", "/hr/employees/", 1)}
            (probations if c.contract_type == int(LaborContractType.PROBATION) else contracts).append(item)
    return {"month": f"{year:04d}-{month:02d}",
            "birthdays": _group(birthdays, with_sensitive), "anniversaries": _group(anniversaries),
            "contracts": _group(contracts, with_contracts), "probations": _group(probations, with_contracts)}
