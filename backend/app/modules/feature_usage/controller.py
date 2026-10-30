"""API báo cáo "Mức dùng chức năng" (duoc-CR-655, D0c) — `prefix=/api/feature-usage`, ReportKey 15.

Gác KÉP như 13 báo cáo cũ: `require("setting", …)` VÀ `require_report(ReportKey.FEATURE_USAGE)` (mặc định chỉ admin).
Chỉ số gom theo chức năng / phòng ban — không có đường xem theo từng người (muốn xem người → hồ sơ, khóa 14).
`/summary`, `/summary/export` khai TRƯỚC `/breakdown`.
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.response import success
from app.modules.report_access.guard import require_report

from . import export, service

router = APIRouter(prefix="/api/feature-usage", tags=["feature-usage"])
GUARD = [Depends(require_report(ReportKey.FEATURE_USAGE))]
MAX_ROUTE_LEN = 120


def _filters(request: Request, company_id, department_id) -> service.Filters:
    period = parse_period({**request.query_params, "compare": "none"})
    return service.Filters(period.date_from, period.date_to, company_id, department_id)


@router.get("/summary", dependencies=GUARD)
def feature_summary(request: Request, company_id: int | None = Query(None, ge=1),
                    department_id: int | None = Query(None, ge=1), db: Session = Depends(get_db),
                    user=Depends(require("setting", "read"))):
    return success(service.summary(db, _filters(request, company_id, department_id)))


@router.get("/summary/export", dependencies=GUARD)
def feature_summary_export(request: Request, company_id: int | None = Query(None, ge=1),
                           department_id: int | None = Query(None, ge=1), db: Session = Depends(get_db),
                           user=Depends(require("setting", "export"))):
    return export.export_summary(db, user, _filters(request, company_id, department_id))


@router.get("/breakdown", dependencies=GUARD)
def feature_breakdown(request: Request, kind: int = Query(..., ge=1, le=99), code: int = Query(0, ge=0, le=32767),
                      route: str = Query("", max_length=MAX_ROUTE_LEN), company_id: int | None = Query(None, ge=1),
                      department_id: int | None = Query(None, ge=1), db: Session = Depends(get_db),
                      user=Depends(require("setting", "read"))):
    return success(service.breakdown(db, _filters(request, company_id, department_id), kind, code, route))
