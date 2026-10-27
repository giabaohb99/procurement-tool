"""«Bấm số ra danh sách ĐƠN» của báo cáo Tình hình nghỉ phép (duoc-CR-686,
`GET /api/leave-requests/summary/rows`). Hợp đồng chung ở `core/report_drilldown.py`.

Khớp với con số trên bảng:
  - `requests` / `requests_pending_over_3d`: đơn có NGÀY BẮT ĐẦU trong kỳ (như `/summary`).
  - `days_approved` / `days_pending`: đơn có NGÀY rơi vào kỳ (kể cả bắt đầu trước kỳ); cột «Số
    ngày trong kỳ» là phần ngày đã chia theo `report_day_split` — cộng cột này = con số ngày.
  - Nhóm (`group_by`/`group_key`) lọc bằng `core.report_drilldown.filter_group` trên đúng cột mà
    `/summary` gom theo; riêng `leave_type` + chỉ số ngày thì mỗi DÒNG loại nghỉ là một mục.
Số truy vấn cố định: đơn · dòng · (khoảng + lịch + ngày lễ khi có đơn vắt biên) · tên NV/phòng.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DimensionSpec
from app.core.report_drilldown import Col, filter_group, parse_rows_params, rows_response
from app.core.report_period import Period
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.leave.constants import LEAVE_REQUEST_STATUS_LABELS, LR_APPROVED, LR_PENDING
from app.modules.leave.report_day_split import build_split_requests, overlapping_rows
from app.modules.leave.report_rows import scoped_base, scoped_requests
from app.modules.leave.report_spec import DRILLDOWN_METRICS, load_type_info
from app.modules.leave.report_sql_metrics import PENDING_OVERDUE_HOURS
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine

COLUMNS = [Col("code", "Mã đơn"), Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"),
           Col("department", "Phòng ban"), Col("leave_type", "Loại nghỉ chính"),
           Col("from_date", "Từ ngày", "date"), Col("to_date", "Đến ngày", "date"),
           Col("days", "Số ngày trong kỳ", "days"), Col("status", "Trạng thái")]
_CHUNK = 900
#  Chiều gom của `/summary` → thuộc tính trên mục danh sách (cùng cột chép trên đơn).
_DIM_ATTR = {"company": "company_id", "department": "department_id", "employee": "employee_id",
             "status": "status", "leave_type": "leave_type_id"}


def _lines_of(db: Session, ids: list[int]) -> dict[int, list[tuple[int, float]]]:
    out: dict[int, list[tuple[int, float]]] = {}
    for i in range(0, len(ids), _CHUNK):
        for ln in (db.query(LeaveRequestLine.request_id, LeaveRequestLine.leave_type_id,
                            LeaveRequestLine.days)
                   .filter(LeaveRequestLine.request_id.in_(ids[i:i + _CHUNK])).all()):
            out.setdefault(ln.request_id, []).append((ln.leave_type_id or 0, float(ln.days or 0)))
    return out


def _entries(db: Session, rows, d_from, d_to, calendar_types, by_line_type: bool) -> list:
    """Mục danh sách `(đơn, loại nghỉ, số ngày trong kỳ)` — đơn vắt biên kỳ được chia ngày."""
    lines = _lines_of(db, [r.id for r in rows])
    crossing = [r for r in rows if r.from_date < d_from or r.to_date > d_to]
    share = {s.id: s.share_where(lambda d: d_from <= d <= d_to)
             for s in build_split_requests(db, crossing, calendar_types)}
    out = []
    for r in rows:
        f = share.get(r.id, 1.0)
        ls = lines.get(r.id, [])
        if by_line_type:
            out += [(r, t, days * f) for t, days in ls]
        else:
            out.append((r, r.leave_type_id or 0, sum(d for _t, d in ls) * f))
    return out


def _dim_for(group_by: str) -> DimensionSpec:
    attr = _DIM_ATTR[group_by]
    return DimensionSpec(group_by, group_by, key_of=lambda e: [(getattr(e, attr), "")])


def build_rows(db: Session, user, prof: dict, period: Period, params, company_id: int | None,
               department_id: int | None) -> dict:
    metric, group_by, group_key = parse_rows_params(params, DRILLDOWN_METRICS)
    if group_by and group_by not in _DIM_ATTR:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    type_name, _unpaid, calendar_types = load_type_info(db)
    d_from, d_to = period.date_from, period.date_to
    days_metric = metric in ("days_approved", "days_pending")

    if days_metric:
        status = LR_APPROVED if metric == "days_approved" else LR_PENDING
        rows = [r for r in overlapping_rows(scoped_base(db, user, prof, company_id, department_id),
                                            d_from, d_to, multi_day_only=False) if r.status == status]
    else:
        q = scoped_requests(db, user, prof, d_from, d_to, company_id, department_id)
        if metric == "requests_pending_over_3d":
            #  Cùng đồng hồ với `submitted_at` (xem report_sql_metrics). ⚠️ Bản CR-686 để phép trừ lọt vào
            #  chú thích nên danh sách KHÔNG lọc mốc 72 giờ — thẻ ghi 0, danh sách ra 1 (E2E 27/10/2026).
            cutoff = datetime.now() - timedelta(hours=PENDING_OVERDUE_HOURS)
            q = q.filter(LeaveRequest.status == LR_PENDING, LeaveRequest.submitted_at < cutoff)
        rows = q.with_entities(
            LeaveRequest.id, LeaveRequest.status, LeaveRequest.code, LeaveRequest.from_date,
            LeaveRequest.to_date, LeaveRequest.company_id, LeaveRequest.department_id,
            LeaveRequest.employee_id, LeaveRequest.leave_type_id).all()

    by_line_type = days_metric and group_by == "leave_type"
    items = _entries(db, rows, d_from, d_to, calendar_types, by_line_type)
    objs = [SimpleNamespace(company_id=r.company_id or 0, department_id=r.department_id or 0,
                            employee_id=r.employee_id or 0, status=r.status, leave_type_id=t,
                            req=r, days=days) for r, t, days in items]
    if group_by:
        objs = filter_group(objs, _dim_for(group_by), group_key)
    if days_metric:
        objs = [o for o in objs if o.days > 1e-9]
    objs.sort(key=lambda o: (o.req.from_date, o.req.code))

    emp_ids = list({o.employee_id for o in objs})
    emps = {}
    for i in range(0, len(emp_ids), _CHUNK):
        emps.update({e.id: e for e in db.query(Employee.id, Employee.code, Employee.full_name)
                     .filter(Employee.id.in_(emp_ids[i:i + _CHUNK])).all()})
    dept_name = ({d.id: d.name for d in db.query(Department.id, Department.name).all()}
                 if objs else {})
    out = []
    for o in objs:
        emp = emps.get(o.employee_id)
        out.append({"code": o.req.code, "employee_code": emp.code if emp else "",
                    "employee_name": emp.full_name if emp else "",
                    "department": dept_name.get(o.department_id, ""),
                    "leave_type": type_name.get(o.req.leave_type_id, ""),
                    "from_date": o.req.from_date, "to_date": o.req.to_date,
                    "days": round(o.days, 2), "status": LEAVE_REQUEST_STATUS_LABELS.get(o.status, ""),
                    "link": f"/hr/leave-requests/{o.req.id}"})
    return rows_response(metric, DRILLDOWN_METRICS[metric], COLUMNS, out)
