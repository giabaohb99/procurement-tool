"""Báo cáo A4 «Định biên kế hoạch so với thực tế» (khóa 25) — duoc-CR-689.

Router riêng chỉ chứa `/summary` + `/summary/export` + `/summary/rows` (khung báo cáo kiểu Haravan).
Đường gốc `/api/headcount-plan-report` cố ý không nằm dưới router chính có `/{id}`.
Gác KÉP: `require('headcount_plan', read|export)` + `require_report(HEADCOUNT_PLAN)`; phạm vi `apply_scope` trên bảng
kế hoạch VÀ trên số người đếm (cột pháp nhân + phòng, cũng theo khóa `headcount_plan`). `/summary/rows` liệt kê danh
tính nên đòi thêm `employee.read` + phạm vi `employee`. Xuất tệp dùng phạm vi `export` của kế hoạch.
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

from . import headcount_plan_report_service as svc

router = APIRouter(prefix="/api/headcount-plan-report", tags=["report"])
_GUARD = [Depends(require_report(ReportKey.HEADCOUNT_PLAN))]


def _summary(request: Request, db: Session, user, action: str = "read"):
    qp = request.query_params
    return svc.build_summary(db, user, get_perm_profile(db, user), parse_period(qp),
                             qp.get("group_by") or None, valid_company_id(qp.get("company_id")),
                             valid_department_id(qp.get("department_id")), action)


@router.get("/summary", dependencies=_GUARD)
def headcount_plan_summary(request: Request, db: Session = Depends(get_db),
                           user=Depends(require("headcount_plan", "read"))):
    return success(_summary(request, db, user))


@router.get("/summary/export", dependencies=_GUARD)
def headcount_plan_export(request: Request, db: Session = Depends(get_db),
                          user=Depends(require("headcount_plan", "export"))):
    return report_xlsx("dinh-bien-ke-hoach", _summary(request, db, user, "export"))


@router.get("/summary/rows", dependencies=[*_GUARD, Depends(require("employee", "read"))])
def headcount_plan_rows(request: Request, db: Session = Depends(get_db),
                        user=Depends(require("headcount_plan", "read"))):
    qp = request.query_params
    metric, group_by, group_key = parse_rows_params(qp, svc.METRICS)
    return success(svc.build_rows(db, user, get_perm_profile(db, user), parse_period(qp), metric, group_by,
                                  group_key, valid_company_id(qp.get("company_id")),
                                  valid_department_id(qp.get("department_id"))))
