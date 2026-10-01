"""Báo cáo Văn bản (phase 05).

Router RIÊNG chỉ chứa `/summary` + `/summary/export` (khung báo cáo kiểu Haravan,
`core/report_aggregate.py`). Đăng ký trong `main.py` TRƯỚC router chính của phân hệ để
`/summary` không bị `/{id}` nuốt (422).

Gác bằng `require('document', 'read'|'export')` — CHẶT hơn menu nguồn (`/document/documents`
không khai `entity`, dùng khóa phân hệ), chấp nhận theo Q5.3 của `phase-05-admin-reports.md`.
Số liệu lọc qua `report_service._base_query` (= `documents_query` + `visible_condition`), đúng
phạm vi của danh sách văn bản — không đường nào lỏng hơn bảng gốc.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.report_export import report_xlsx
from app.core.report_period import parse_period
from app.core.response import success

from . import report_service as svc

router = APIRouter(prefix="/api/documents", tags=["document"])


@router.get("/summary")
def document_summary(request: Request, db: Session = Depends(get_db),
                     user=Depends(require("document", "read"))):
    profile = get_perm_profile(db, user)
    period = parse_period(request.query_params)
    data = svc.build_summary(db, user, profile, period, request.query_params.get("group_by") or None,
                             request.query_params.get("company_id"))
    return success(data)


@router.get("/summary/export")
def document_summary_export(request: Request, db: Session = Depends(get_db),
                            user=Depends(require("document", "export"))):
    profile = get_perm_profile(db, user)
    period = parse_period(request.query_params)
    data = svc.build_summary(db, user, profile, period, request.query_params.get("group_by") or None,
                             request.query_params.get("company_id"))
    return report_xlsx("van-ban", data)
