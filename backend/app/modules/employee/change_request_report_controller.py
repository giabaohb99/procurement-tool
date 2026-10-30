"""Báo cáo E2 "Yêu cầu sửa hồ sơ" (khóa 27) — duoc-CR-689.

Router riêng chỉ chứa `/summary` + `/summary/export` + `/summary/rows` (khung báo cáo kiểu Haravan).
Đường gốc `/api/profile-change-report` cố ý không nằm dưới router chính có `/{id}`.
Gác KÉP: `require('employee', 'write')` — CÙNG khóa với màn duyệt yêu cầu sửa hồ sơ (`change_request_controller`;
không có khóa quyền riêng; yêu cầu sửa chứa giá trị cũ / mới của hồ sơ nên chỉ người duyệt được xem, `read` thì
chưa đủ) + `require_report(PROFILE_CHANGES)`; đường xuất Excel đòi thêm `employee.export`. Phạm vi
`apply_scope(Employee, 'employee', action='write')` giống màn duyệt; `company_id` / `department_id` lọc SAU
phạm vi, chỉ thu hẹp.
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

from . import change_request_report_service as svc
from .model import Employee

router = APIRouter(prefix="/api/profile-change-report", tags=["report"])
_GUARD = [Depends(require_report(ReportKey.PROFILE_CHANGES))]


def _inputs(request: Request, db: Session, user) -> tuple:
    qp = request.query_params
    q = apply_scope(db.query(Employee), Employee, "employee", user, get_perm_profile(db, user), "write")
    return q, parse_period(qp), dict(company_id=valid_company_id(qp.get("company_id")),
                                     department_id=valid_department_id(qp.get("department_id")))


@router.get("/summary", dependencies=_GUARD)
def profile_change_summary(request: Request, db: Session = Depends(get_db),
                           user=Depends(require("employee", "write"))):
    q, period, flt = _inputs(request, db, user)
    return success(svc.build_summary(db, q, period, request.query_params.get("group_by") or None, **flt))


@router.get("/summary/export", dependencies=_GUARD)
def profile_change_summary_export(request: Request, db: Session = Depends(get_db),
                                  user=Depends(require("employee", "write")),
                                  _export=Depends(require("employee", "export"))):
    q, period, flt = _inputs(request, db, user)
    return report_xlsx("yeu-cau-sua-ho-so",
                       svc.build_summary(db, q, period, request.query_params.get("group_by") or None, **flt))


@router.get("/summary/rows", dependencies=_GUARD)
def profile_change_summary_rows(request: Request, db: Session = Depends(get_db),
                                user=Depends(require("employee", "write"))):
    q, period, flt = _inputs(request, db, user)
    metric, group_by, group_key = parse_rows_params(request.query_params, svc.LABELS)
    return success(svc.build_rows(db, q, period, metric, group_by, group_key, **flt))
