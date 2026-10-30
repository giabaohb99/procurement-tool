"""Báo cáo B4 "Đối tượng cần chú ý theo luật" (khóa 29) — duoc-CR-689.

Router riêng chỉ chứa `/summary` + `/summary/export` + `/summary/rows` (khung báo cáo kiểu Haravan).
Đường gốc `/api/legal-watch` cố ý không nằm dưới router chính có `/{id}`.
Gác: `require('employee', read|export)` + `require_report(LEGAL_WATCH)` + phạm vi `apply_scope`, và đòi
`employee_sensitive.read` (dùng ngày sinh, con nhỏ) -> 403 bằng câu tiếng Việt dễ hiểu, không lộ mã quyền.
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
from app.modules.leave.request_model import LeaveRequest
from app.modules.report.procurement_summary_rows import valid_company_id, valid_department_id
from app.modules.labor_contract.access import has_perm
from app.modules.report_access.guard import require_report

from . import legal_watch_report_service as svc
from .model import Employee
from .sensitive import can_read_sensitive

router = APIRouter(prefix="/api/legal-watch", tags=["report"])
_GUARD = [Depends(require_report(ReportKey.LEGAL_WATCH))]
SENSITIVE_MSG = ("Báo cáo này dùng ngày sinh và thông tin con của nhân sự nên cần quyền xem dữ liệu nhạy cảm. "
                 "Hãy nhờ quản trị cấp quyền.")


def _inputs(request: Request, db: Session, user, action: str) -> tuple:
    prof = get_perm_profile(db, user)
    if not can_read_sensitive(prof):        # `employee_id=0`: danh sách, không có ngoại lệ "chính mình"
        raise HTTPException(403, SENSITIVE_MSG)
    qp = request.query_params
    q = apply_scope(db.query(Employee), Employee, "employee", user, prof, action)
    #  Thai sản = đơn nghỉ phép: chỉ đọc trong phạm vi `leave_request` của người xem (luôn hành động read).
    leave_q = (apply_scope(db.query(LeaveRequest), LeaveRequest, "leave_request", user, prof)
               if has_perm(prof, "leave_request", "read") else None)
    return q, parse_period(qp), dict(leave_q=leave_q, company_id=valid_company_id(qp.get("company_id")),
                                     department_id=valid_department_id(qp.get("department_id")))


@router.get("/summary", dependencies=_GUARD)
def legal_watch_summary(request: Request, db: Session = Depends(get_db),
                        user=Depends(require("employee", "read"))):
    q, period, flt = _inputs(request, db, user, "read")
    return success(svc.build_summary(db, q, period, request.query_params.get("group_by") or None, **flt))


@router.get("/summary/export", dependencies=_GUARD)
def legal_watch_summary_export(request: Request, db: Session = Depends(get_db),
                               user=Depends(require("employee", "export"))):
    q, period, flt = _inputs(request, db, user, "export")
    return report_xlsx("doi-tuong-theo-luat",
                       svc.build_summary(db, q, period, request.query_params.get("group_by") or None, **flt))


@router.get("/summary/rows", dependencies=_GUARD)
def legal_watch_summary_rows(request: Request, db: Session = Depends(get_db),
                             user=Depends(require("employee", "read"))):
    q, period, flt = _inputs(request, db, user, "read")
    allowed = {k: svc.LABELS[k] for k in svc.visible_kinds()}
    metric, group_by, group_key = parse_rows_params(request.query_params, allowed)
    return success(svc.build_rows(db, q, period, metric, group_by, group_key, **flt))
