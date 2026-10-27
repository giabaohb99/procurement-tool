"""Sổ quản lý lao động — router RIÊNG (duoc-CR-687, khóa 19): `/api/labor-register/summary` (+ export, rows).

Gác: `require('employee', read|export)` + `require_report(LABOR_BOOK)` + cổng quyền nhạy cảm / HĐLĐ
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
from .labor_book_export import export_labor_book
from .report_inputs import build_inputs

router = APIRouter(prefix="/api/labor-register", tags=["labor_register"])
_GUARD = [Depends(require_report(ReportKey.LABOR_BOOK))]


@router.get("/summary", dependencies=_GUARD)
def labor_register_summary(request: Request, db: Session = Depends(get_db),
                           user=Depends(require("employee", "read"))):
    kw = build_inputs(request, db, user)
    return success(svc.build_summary(db, svc.BOOK, group_by=request.query_params.get("group_by") or None, **kw))


@router.get("/summary/export", dependencies=_GUARD)
def labor_register_summary_export(request: Request, db: Session = Depends(get_db),
                                  user=Depends(require("employee", "export"))):
    return export_labor_book(db, **build_inputs(request, db, user, export=True, with_leave=True))


@router.get("/summary/rows", dependencies=_GUARD)
def labor_register_summary_rows(request: Request, db: Session = Depends(get_db),
                                user=Depends(require("employee", "read"))):
    kw = build_inputs(request, db, user)
    metric, group_by, group_key = parse_rows_params(
        request.query_params, {k: v[0] for k, v in svc.BOOK.metrics.items()})
    return success(svc.build_rows(db, svc.BOOK, metric=metric, group_by=group_by, group_key=group_key, **kw))
