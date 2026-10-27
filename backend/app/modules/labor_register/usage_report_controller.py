"""Báo cáo sử dụng lao động (mẫu 01/PLI) — router RIÊNG (duoc-CR-687, khóa 20): `/api/labor-usage-report/summary` (+ export, rows).

Gác: `require('employee', read|export)` + `require_report(LABOR_USAGE_REPORT)` + cổng quyền nhạy cảm / HĐLĐ
trong `report_inputs`. Phạm vi `apply_scope(Employee)` (và `LaborContract` cho HĐ); `company_id` /
`department_id` lọc SAU phạm vi, chỉ thu hẹp. Tên hàm route được trợ lý AI nạp theo tên — đừng đổi.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.report_drilldown import parse_rows_params
from app.core.report_keys import ReportKey
from app.core.response import success
from app.modules.report_access.guard import require_report

from . import report_service as svc
from .form_01_pli_export import export_form_01_pli
from .report_inputs import build_inputs

router = APIRouter(prefix="/api/labor-usage-report", tags=["labor_usage_report"])
_GUARD = [Depends(require_report(ReportKey.LABOR_USAGE_REPORT))]


@router.get("/summary", dependencies=_GUARD)
def labor_usage_summary(request: Request, db: Session = Depends(get_db),
                           user=Depends(require("employee", "read"))):
    kw = build_inputs(request, db, user)
    return success(svc.build_summary(db, svc.USAGE, group_by=request.query_params.get("group_by") or None, **kw))


@router.get("/summary/export", dependencies=_GUARD)
def labor_usage_summary_export(request: Request, db: Session = Depends(get_db),
                                  user=Depends(require("employee", "export"))):
    return export_form_01_pli(db, **build_inputs(request, db, user, export=True))


@router.get("/summary/rows", dependencies=_GUARD)
def labor_usage_summary_rows(request: Request, db: Session = Depends(get_db),
                                user=Depends(require("employee", "read"))):
    kw = build_inputs(request, db, user)
    metric, group_by, group_key = parse_rows_params(
        request.query_params, {k: v[0] for k, v in svc.USAGE.metrics.items()})
    return success(svc.build_rows(db, svc.USAGE, metric=metric, group_by=group_by, group_key=group_key, **kw))
