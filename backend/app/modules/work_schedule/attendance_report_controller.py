"""Báo cáo C3 "Có mặt theo ngày" (khóa 26) — duoc-CR-689.

Router riêng chỉ chứa `/summary` + `/summary/export` + `/summary/rows` (khung báo cáo kiểu Haravan).
Đường gốc `/api/attendance-report` cố ý không nằm dưới router chính có `/{id}`.
Gác KÉP: `require('employee', read|export)` + `require_report(ATTENDANCE_DAILY)`; phạm vi
`apply_scope(Employee)`; số nghỉ đọc đơn qua `apply_scope(LeaveRequest, 'leave_request')` — thiếu quyền
xem đơn nghỉ thì chỉ số nghỉ để trống (riêng `/rows` là danh sách người nghỉ nên trả 403).
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.report_drilldown import parse_rows_params
from app.core.report_export import report_xlsx
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.labor_contract.access import has_perm
from app.modules.leave.request_model import LeaveRequest
from app.modules.report.procurement_summary_rows import valid_company_id, valid_department_id
from app.modules.report_access.guard import require_report

from . import attendance_report_service as service

router = APIRouter(prefix="/api/attendance-report", tags=["report"])
_GUARD = [Depends(require_report(ReportKey.ATTENDANCE_DAILY))]


def _inputs(request: Request, db: Session, user, action: str = "read") -> tuple[dict, bool]:
    """Truy vấn nhân sự (đã qua phạm vi + lọc công ty/phòng ban), truy vấn đơn nghỉ, kỳ."""
    prof = get_perm_profile(db, user)
    qp = request.query_params
    emp_q = apply_scope(db.query(Employee), Employee, "employee", user, prof, action)
    company_id, department_id = valid_company_id(qp.get("company_id")), valid_department_id(qp.get("department_id"))
    if company_id is not None:
        emp_q = emp_q.filter(Employee.company_id == company_id)
    if department_id is not None:
        emp_q = emp_q.filter(Employee.department_id == department_id)
    with_leave = has_perm(prof, "leave_request", "read")
    leave_q = apply_scope(db.query(LeaveRequest), LeaveRequest, "leave_request", user, prof) if with_leave else None
    return dict(emp_q=emp_q, leave_q=leave_q, period=parse_period(qp)), with_leave


@router.get("/summary", dependencies=_GUARD)
def attendance_summary(request: Request, db: Session = Depends(get_db), user=Depends(require("employee", "read"))):
    kw, with_leave = _inputs(request, db, user)
    return success(service.build_summary(db, with_leave=with_leave, group_by=request.query_params.get("group_by") or None, **kw))


@router.get("/summary/export", dependencies=_GUARD)
def attendance_summary_export(request: Request, db: Session = Depends(get_db),
                              user=Depends(require("employee", "export"))):
    kw, with_leave = _inputs(request, db, user, "export")   # phạm vi theo quyền XUẤT
    return report_xlsx("co-mat-theo-ngay", service.build_summary(
        db, with_leave=with_leave, group_by=request.query_params.get("group_by") or None, **kw))


@router.get("/summary/rows", dependencies=_GUARD)
def attendance_summary_rows(request: Request, db: Session = Depends(get_db),
                            user=Depends(require("employee", "read"))):
    metric, group_by, group_key = parse_rows_params(request.query_params, service.METRICS)
    kw, with_leave = _inputs(request, db, user)
    if not with_leave:
        raise HTTPException(403, "Bạn chưa có quyền xem đơn nghỉ phép nên không xem được danh sách người nghỉ")
    return success(service.build_rows(db, metric=metric, group_by=group_by, group_key=group_key, **kw))
