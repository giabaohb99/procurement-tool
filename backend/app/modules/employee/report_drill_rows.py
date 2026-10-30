""""Bấm số ra danh sách NHÂN SỰ" của báo cáo Biến động nhân sự (duoc-CR-686,
`GET /api/employees/summary/rows`). Hợp đồng chung ở `core/report_drilldown.py`.

Dùng LẠI đúng hàm sinh sự kiện của `/summary` (`hire_events` · `resign_events` · `employees_as_of`)
rồi lọc nhóm bằng `DimensionSpec.key_of` của `report_headcount_spec.build_spec` — danh sách luôn
khớp con số trên bảng. Tra thêm hồ sơ bằng MỘT truy vấn theo mã nhân sự.

⚠️ Chỉ trả cột công khai (mã, tên, công ty, phòng ban, chức vụ, ngày vào/nghỉ, trạng thái) —
KHÔNG đọc trường trong `employee/sensitive.py`.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_drilldown import Col, filter_group, parse_rows_params, rows_response
from app.core.report_period import Period
from app.core.status_codes import EMPLOYEE_STATUS
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.employee.report_headcount_events import (employees_as_of,
                                                           hire_events, resign_events, vn_today)
from app.modules.employee.report_headcount_privacy import require_age_rows_allowed
from app.modules.employee.report_headcount_spec import DRILLDOWN_METRICS, build_spec

COLUMNS = [Col("code", "Mã NV"), Col("full_name", "Họ tên"), Col("company", "Công ty"),
           Col("department", "Phòng ban"), Col("position", "Chức vụ"),
           Col("hire_date", "Ngày vào làm", "date"), Col("resign_date", "Ngày nghỉ việc", "date"),
           Col("status", "Trạng thái")]
_CHUNK = 900


def build_rows(db: Session, user, prof: dict, period: Period, params, company_id: int | None,
               department_id: int | None) -> dict:
    metric, group_by, group_key = parse_rows_params(params, DRILLDOWN_METRICS)
    require_age_rows_allowed(prof, group_by, group_key)   # duoc-CR-687: danh sách theo tuổi lộ tuổi
    company_name = {c.id: c.name for c in db.query(Company.id, Company.name).all()}
    department_name = {d.id: d.name for d in db.query(Department.id, Department.name).all()}
    spec, _status_dim = build_spec(company_name, department_name)
    dim = spec.dimensions.get(group_by) if group_by else None
    if group_by and dim is None:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")

    d_from, d_to = period.date_from, period.date_to
    if metric == "new_hires":
        events = hire_events(db, user, prof, d_from, d_to, vn_today(), company_id, department_id)
    elif metric == "departures":
        events = resign_events(db, user, prof, d_from, d_to, company_id, department_id)
    else:
        events = employees_as_of(db, user, prof, d_to, company_id, department_id)
    events = filter_group(events, dim, group_key)

    ids = list({e.employee_id for e in events})
    emps = {}
    for i in range(0, len(ids), _CHUNK):
        emps.update({e.id: e for e in db.query(
            Employee.id, Employee.code, Employee.full_name, Employee.position, Employee.hire_date,
            Employee.resign_date, Employee.created_at, Employee.status)
            .filter(Employee.id.in_(ids[i:i + _CHUNK])).all()})
    rows = []
    for ev in sorted(events, key=lambda e: (e.event_date, e.employee_id)):
        emp = emps.get(ev.employee_id)
        if emp is None:
            continue
        rows.append({"code": emp.code, "full_name": emp.full_name,
                     "company": company_name.get(ev.company_id, ""),
                     "department": department_name.get(ev.department_id, ""),
                     "position": emp.position or "",
                     "hire_date": emp.hire_date,   # thiếu thì để TRỐNG — không điền ngày tạo hồ sơ
                     "resign_date": emp.resign_date,
                     "status": EMPLOYEE_STATUS.label_of(emp.status) or emp.status or "",
                     "link": f"/hr/employees/{emp.id}"})
    return rows_response(metric, DRILLDOWN_METRICS[metric], COLUMNS, rows)
