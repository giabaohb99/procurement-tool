"""Báo cáo A3 «Cơ cấu quản lý» (khóa 23) — duoc-CR-688.

Router riêng chỉ chứa `/summary` + `/summary/export` + `/summary/rows` (khung báo cáo kiểu Haravan).
Đường gốc `/api/management-span` cố ý KHÔNG nằm dưới `/api/employees` / `/api/labor-contracts` để khỏi bị
`/{id}` của router chính nuốt. Gác KÉP: `require('employee', read|export)` + `require_report(23)`;
phạm vi `apply_scope(Employee, 'employee')`; `company_id`/`department_id` chỉ thu hẹp thêm.
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
from app.modules.report.procurement_summary_rows import valid_company_id, valid_department_id
from app.modules.report_access.guard import require_report

from . import management_report_service as svc

router = APIRouter(prefix="/api/management-span", tags=["report"])
_GUARD = [Depends(require_report(ReportKey.MANAGEMENT_SPAN))]


def _summary(request: Request, db: Session, user, action: str = "read"):
    qp = request.query_params
    return svc.build_summary(db, user, get_perm_profile(db, user), parse_period(qp),
                             qp.get("group_by") or None, valid_company_id(qp.get("company_id")),
                             valid_department_id(qp.get("department_id")), action)


@router.get("/summary", dependencies=_GUARD)
def management_span_summary(request: Request, db: Session = Depends(get_db),
                            user=Depends(require("employee", "read"))):
    return success(_summary(request, db, user))


@router.get("/summary/export", dependencies=_GUARD)
def management_span_export(request: Request, db: Session = Depends(get_db),
                           user=Depends(require("employee", "export"))):
    return report_xlsx("co-cau-quan-ly", _summary(request, db, user, "export"))


@router.get("/summary/rows", dependencies=_GUARD)
def management_span_rows(request: Request, db: Session = Depends(get_db),
                         user=Depends(require("employee", "read"))):
    qp = request.query_params
    metric, group_by, group_key = parse_rows_params(qp, svc.DRILLDOWN_METRICS)
    return success(svc.build_rows(db, user, get_perm_profile(db, user), parse_period(qp), metric, group_by,
                                  group_key, valid_company_id(qp.get("company_id")),
                                  valid_department_id(qp.get("department_id"))))
