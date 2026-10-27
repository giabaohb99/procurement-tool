"""«Bấm số ra danh sách» của báo cáo Quỹ phép năm (duoc-CR-686,
`GET /api/leave-balances/summary/rows`). Hợp đồng chung ở `core/report_drilldown.py`.

  - `remaining` (mọi dòng quỹ) · `people_over_quota` (còn lại < 0) · `people_unused` (được cấp > 0,
    đã dùng = 0, giữ chỗ = 0) · `carried_expired` (phép chuyển đã hết hạn > 0): MỘT DÒNG QUỸ
    (người × loại nghỉ). Nhóm lọc bằng ĐÚNG `DimensionSpec.key_of` mà `/summary` dùng để gom.
  - `people_missing_balance`: MỘT NGƯỜI đang làm chưa có quỹ năm đó (`balance_report_missing`);
    chỉ số này chỉ ở Tổng nên `group_by`/`group_key` được bỏ qua.
Năm = năm của ngày kết thúc kỳ. Không trả trường nhạy cảm — chỉ mã, tên, phòng ban, ngày vào làm.
"""
from __future__ import annotations

from dataclasses import replace

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_drilldown import Col, filter_group, parse_rows_params, rows_response
from app.core.report_period import Period
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.leave.balance_report_missing import missing_balance_query
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.balance_report_spec import DRILLDOWN_METRICS, BalanceRow, build_spec, rows_of

BALANCE_COLUMNS = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"),
                   Col("department", "Phòng ban"), Col("leave_type", "Loại nghỉ"),
                   Col("allocated", "Cơ bản", "days"), Col("seniority", "Thâm niên", "days"),
                   Col("carried", "Chuyển sang", "days"), Col("adjusted", "Điều chỉnh", "days"),
                   Col("used", "Đã dùng", "days"), Col("pending", "Giữ chỗ", "days"),
                   Col("remaining", "Còn lại", "days")]
MISSING_COLUMNS = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"),
                   Col("company", "Công ty"), Col("department", "Phòng ban"),
                   Col("hire_date", "Ngày vào làm", "date")]
PERSON_METRICS = ('people_over_quota', 'people_unused')
_PICK = {
    "remaining": lambda r: True,
    "people_over_quota": lambda r: r.remaining < 0,
    "people_unused": lambda r: r.person_unused,
    "carried_expired": lambda r: r.carried_expired > 0,
}


def _missing_rows(db: Session, user, prof, year, status, company_id, department_id) -> list[dict]:
    emps = (missing_balance_query(db, user, prof, year, status, company_id, department_id)
            .order_by(Employee.code)
            .with_entities(Employee.id, Employee.code, Employee.full_name, Employee.company_id,
                           Employee.department_id, Employee.hire_date).all())
    company = {c.id: c.name for c in db.query(Company.id, Company.name).all()} if emps else {}
    dept = {d.id: d.name for d in db.query(Department.id, Department.name).all()} if emps else {}
    return [{"employee_code": e.code, "employee_name": e.full_name,
             "company": company.get(e.company_id, ""), "department": dept.get(e.department_id, ""),
             "hire_date": e.hire_date, "link": f"/hr/employees/{e.id}"} for e in emps]


def build_rows(db: Session, user, prof: dict, period: Period, params, company_id: int | None,
               department_id: int | None, employee_status: str) -> dict:
    metric, group_by, group_key = parse_rows_params(params, DRILLDOWN_METRICS)
    year = period.date_to.year
    label = DRILLDOWN_METRICS[metric]
    if metric == "people_missing_balance":
        return rows_response(metric, label, MISSING_COLUMNS,
                             _missing_rows(db, user, prof, year, employee_status, company_id,
                                           department_id))

    #  MỘT lượt quét Employee cho cả mã, tên và phòng ban hiện tại (cột hiển thị + chiều gom).
    emps = db.query(Employee.id, Employee.code, Employee.full_name, Employee.department_id).all()
    codes = {e.id: e.code for e in emps}
    emp_dept = {e.id: e.department_id or 0 for e in emps}
    emp_name = {e.id: e.full_name for e in emps}
    type_name = {t.id: t.name for t in db.query(LeaveType.id, LeaveType.name).all()}
    department_name = {d.id: d.name for d in db.query(Department.id, Department.name).all()}
    company_name = {c.id: c.name for c in db.query(Company.id, Company.name).all()}
    spec = build_spec(company_name, department_name)
    dim = spec.dimensions.get(group_by) if group_by else None
    if group_by and dim is None:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    rows = rows_of(db, user, prof, year, type_name, emp_dept, emp_name, company_id,
                   employee_status, department_id)
    rows = filter_group([r for r in rows if _PICK[metric](r)], dim, group_key)
    if metric in PERSON_METRICS:   # MỘT dòng mỗi người → `total` khớp số người trên bảng
        rows = _merge_by_person(rows)
    rows.sort(key=lambda r: (codes.get(r.employee_id, ""), r.leave_type_name))
    return rows_response(metric, label, BALANCE_COLUMNS, [_row_dict(r, codes, department_name)
                                                           for r in rows])


def _merge_by_person(rows: list[BalanceRow]) -> list[BalanceRow]:
    """Cộng dồn các dòng quỹ của cùng một người; cột «Loại nghỉ» ghi các loại, cách nhau dấu phẩy."""
    by_emp: dict[int, list[BalanceRow]] = {}
    for r in rows:
        by_emp.setdefault(r.employee_id, []).append(r)
    out = []
    for group in by_emp.values():
        first = group[0]
        out.append(replace(
            first, leave_type_name=", ".join(sorted({g.leave_type_name for g in group if g.leave_type_name})),
            **{f: round(sum(getattr(g, f) for g in group), 2)
               for f in ("allocated", "seniority", "carried", "adjusted", "used", "pending",
                         "remaining")}))
    return out


def _row_dict(r: BalanceRow, codes: dict, department_name: dict) -> dict:
    return {"employee_code": codes.get(r.employee_id, ""), "employee_name": r.employee_name,
            "department": department_name.get(r.department_id, ""), "leave_type": r.leave_type_name,
            "allocated": r.allocated, "seniority": r.seniority, "carried": r.carried,
            "adjusted": r.adjusted, "used": r.used, "pending": r.pending,
            "remaining": r.remaining, "link": f"/hr/employees/{r.employee_id}"}
