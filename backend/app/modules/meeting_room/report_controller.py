"""Báo cáo F1 «Sử dụng phòng họp» (khóa 28) — duoc-CR-689.

Router riêng chỉ chứa `/summary` + `/summary/export` + `/summary/rows` (khung báo cáo kiểu Haravan).
Đường gốc `/api/room-usage` cố ý không nằm dưới router chính có `/{id}`.
Gác KÉP: `require('room_booking', read|export)` + `require_report(ROOM_USAGE)`; phạm vi
`apply_scope(RoomBooking, 'room_booking')` (xuất Excel dùng phạm vi của quyền `export`).
`company_id` lọc theo pháp nhân sở hữu phòng, `department_id` theo phòng ban đặt — chỉ thu hẹp thêm.
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

from . import report_rows, report_service as service
from .model import RoomBooking

router = APIRouter(prefix="/api/room-usage", tags=["report"])
_GUARD = [Depends(require_report(ReportKey.ROOM_USAGE))]
ENTITY = "room_booking"


def _inputs(request: Request, db: Session, user, action: str = "read") -> dict:
    qp = request.query_params
    q = apply_scope(db.query(RoomBooking), RoomBooking, ENTITY, user, get_perm_profile(db, user), action)
    return dict(booking_q=q, period=parse_period(qp), company_id=valid_company_id(qp.get("company_id")),
                department_id=valid_department_id(qp.get("department_id")))


@router.get("/summary", dependencies=_GUARD)
def room_usage_summary(request: Request, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(service.build_summary(db, group_by=request.query_params.get("group_by") or None,
                                         **_inputs(request, db, user)))


@router.get("/summary/export", dependencies=_GUARD)
def room_usage_summary_export(request: Request, db: Session = Depends(get_db),
                              user=Depends(require(ENTITY, "export"))):
    return report_xlsx("su-dung-phong-hop", service.build_summary(
        db, group_by=request.query_params.get("group_by") or None, **_inputs(request, db, user, "export")))


@router.get("/summary/rows", dependencies=_GUARD)
def room_usage_summary_rows(request: Request, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    metric, group_by, group_key = parse_rows_params(request.query_params, service.METRICS)
    return success(report_rows.build_rows(db, metric=metric, group_by=group_by, group_key=group_key,
                                          **_inputs(request, db, user)))
