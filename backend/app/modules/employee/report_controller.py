"""Báo cáo Nhân sự — biến động & cơ cấu (phase 04).

Router RIÊNG chỉ chứa `/summary` + `/summary/export` (khung báo cáo kiểu Haravan,
`core/report_aggregate.py`). Đăng ký trong `main.py` TRƯỚC router chính của phân hệ để
`/summary` không bị `/{id}` nuốt (422).
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.report_export import report_xlsx
from app.core.report_period import parse_period
from app.core.response import success
from app.modules.report.procurement_summary_rows import valid_company_id

from . import report_service

router = APIRouter(prefix="/api/employees", tags=["employee"])


@router.get("/summary")
def employee_summary(request: Request, db: Session = Depends(get_db),
                     user=Depends(require("employee", "read"))):
    prof = get_perm_profile(db, user)
    period = parse_period(request.query_params)
    cid = valid_company_id(request.query_params.get("company_id"))
    data = report_service.build_summary(db, user, prof, period,
                                        request.query_params.get("group_by") or None, cid)
    return success(data)


@router.get("/summary/export")
def employee_summary_export(request: Request, db: Session = Depends(get_db),
                            user=Depends(require("employee", "export"))):
    prof = get_perm_profile(db, user)
    period = parse_period(request.query_params)
    cid = valid_company_id(request.query_params.get("company_id"))
    data = report_service.build_summary(db, user, prof, period,
                                        request.query_params.get("group_by") or None, cid)
    return report_xlsx("nhan-su-bien-dong-co-cau", data)
