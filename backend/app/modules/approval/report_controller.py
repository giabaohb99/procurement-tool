"""Báo cáo Phê duyệt (phase 05).

Router RIÊNG chỉ chứa `/summary` + `/summary/export` (khung báo cáo kiểu Haravan,
`core/report_aggregate.py`). Đăng ký trong `main.py` TRƯỚC router chính của phân hệ để
`/summary` không bị `/{id}` nuốt (422).

Gác bằng `require('approval_flow', 'read'|'export')` (Q5.4 — thường chỉ quản trị/HCNS).
Số liệu vẫn lọc riêng theo quyền đọc TỪNG loại chứng từ nguồn, xem `report_service.py`.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.report_export import report_xlsx
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.response import success
from app.modules.report_access.guard import require_report

from . import report_service as svc

router = APIRouter(prefix="/api/approvals", tags=["approval"])


@router.get("/summary", dependencies=[Depends(require_report(ReportKey.APPROVAL))])
def approval_summary(request: Request, db: Session = Depends(get_db),
                     user=Depends(require("approval_flow", "read"))):
    profile = get_perm_profile(db, user)
    period = parse_period(request.query_params)
    data = svc.build_summary(db, user, profile, period, request.query_params.get("group_by") or None)
    return success(data)


@router.get("/summary/export", dependencies=[Depends(require_report(ReportKey.APPROVAL))])
def approval_summary_export(request: Request, db: Session = Depends(get_db),
                            user=Depends(require("approval_flow", "export"))):
    profile = get_perm_profile(db, user)
    period = parse_period(request.query_params)
    data = svc.build_summary(db, user, profile, period, request.query_params.get("group_by") or None)
    return report_xlsx("phe-duyet", data)
