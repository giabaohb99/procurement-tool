"""Báo cáo "Làm việc vào ngày lễ, ngày nghỉ" (khóa 30) — duoc-CR-717.

Router riêng `/api/holiday-work-report` (không đặt dưới `/api/leave-comp-requests` để khỏi bị `/{id}` nuốt).
Gác KÉP: `require('leave_comp_request', read|export)` + `require_report(HOLIDAY_WORK)`; phạm vi
`apply_scope(LeaveCompRequest)` (export theo quyền XUẤT).
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.report_drilldown import parse_rows_params
from app.core.report_export import report_xlsx
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.report.procurement_summary_rows import valid_company_id, valid_department_id
from app.modules.report_access.guard import require_report

from . import holiday_work_report_service as service
from .comp_request_model import LeaveCompRequest
from .holiday_work_report_data import valid_day_kind, valid_flag

ENTITY = "leave_comp_request"
router = APIRouter(prefix="/api/holiday-work-report", tags=["report"])
_GUARD = [Depends(require_report(ReportKey.HOLIDAY_WORK))]


def _inputs(request: Request, db: Session, user, action: str = "read") -> dict:
    """Truy vấn phiếu (đã qua phạm vi + lọc công ty/phòng ban), kỳ, `include_pending`, `day_kind`."""
    qp = request.query_params
    q = apply_scope(db.query(LeaveCompRequest), LeaveCompRequest, ENTITY, user, get_perm_profile(db, user), action)
    company_id, department_id = valid_company_id(qp.get("company_id")), valid_department_id(qp.get("department_id"))
    if company_id is not None:
        q = q.filter(LeaveCompRequest.company_id == company_id)
    if department_id is not None:
        q = q.filter(LeaveCompRequest.department_id == department_id)
    return dict(comp_q=q, period=parse_period(qp), include_pending=valid_flag(qp.get("include_pending")),
                day_kind=valid_day_kind(qp.get("day_kind")))


@router.get("/summary", dependencies=_GUARD)
def holiday_work_summary(request: Request, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(service.build_summary(db, group_by=request.query_params.get("group_by") or None,
                                         **_inputs(request, db, user)))


@router.get("/summary/export", dependencies=_GUARD)
def holiday_work_summary_export(request: Request, db: Session = Depends(get_db),
                                user=Depends(require(ENTITY, "export"))):
    return report_xlsx("lam-viec-ngay-le", service.build_summary(
        db, group_by=request.query_params.get("group_by") or None, **_inputs(request, db, user, "export")))


@router.get("/summary/rows", dependencies=_GUARD)
def holiday_work_summary_rows(request: Request, db: Session = Depends(get_db),
                              user=Depends(require(ENTITY, "read"))):
    metric, group_by, group_key = parse_rows_params(request.query_params, service.METRICS)
    return success(service.build_rows(db, metric=metric, group_by=group_by, group_key=group_key,
                                      **_inputs(request, db, user)))
