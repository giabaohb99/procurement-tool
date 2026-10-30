"""Báo cáo H1 "Phúc lợi & sự kiện" (khóa 22) — duoc-CR-688.

Router riêng chỉ chứa `/summary` + `/summary/export` + `/summary/rows` (khung báo cáo kiểu Haravan).
Đường gốc `/api/benefit-audience` cố ý KHÔNG nằm dưới `/api/employees` / `/api/labor-contracts` để khỏi bị
`/{id}` của router chính nuốt. Gác KÉP: `require('employee', read|export)` + `require_report(BENEFIT_AUDIENCE)`;
phạm vi `apply_scope(Employee, 'employee')` (xuất Excel dùng phạm vi của quyền `export`).
Lọc theo ngày sinh / người thân đòi `employee_sensitive.read`; bỏ người đang nghỉ phép đòi `leave_request.read`.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.report_drilldown import parse_rows_params
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.report.procurement_summary_rows import valid_company_id, valid_department_id
from app.modules.report_access.guard import require_report

from . import benefit_report_service as svc
from .benefit_report_export import benefit_export
from .benefit_report_inputs import LEAVE_MSG, SENSITIVE_MSG, parse_filters
from app.modules.company.model import Company
from .model import Employee
from .sensitive import can_read_sensitive

router = APIRouter(prefix="/api/benefit-audience", tags=["report"])
_GUARD = [Depends(require_report(ReportKey.BENEFIT_AUDIENCE))]


def _inputs(request: Request, db: Session, user, action: str):
    prof = get_perm_profile(db, user)
    flt = parse_filters(request.query_params, valid_company_id, valid_department_id)
    #  `employee_id=0` = chỉ xét khóa quyền (đây là danh sách, không có ngoại lệ "chính mình").
    if flt.needs_sensitive and not can_read_sensitive(prof):
        raise HTTPException(403, SENSITIVE_MSG)
    #  Bỏ người đang nghỉ = lộ ai có đơn nghỉ phép đã duyệt -> cần quyền xem đơn nghỉ phép.
    if not flt.include_on_leave and not ((prof.get("perms_union") or {}).get("leave_request") or {}).get("read"):
        raise HTTPException(403, LEAVE_MSG)
    q = apply_scope(db.query(Employee), Employee, "employee", user, prof, action)
    return q, parse_period(request.query_params), flt


@router.get("/summary", dependencies=_GUARD)
def benefit_summary(request: Request, db: Session = Depends(get_db), user=Depends(require("employee", "read"))):
    q, period, flt = _inputs(request, db, user, "read")
    return success(svc.build_summary(db, q, period, request.query_params.get("group_by"), flt))


@router.get("/summary/export", dependencies=_GUARD)
def benefit_summary_export(request: Request, db: Session = Depends(get_db),
                           user=Depends(require("employee", "export"))):
    q, period, flt = _inputs(request, db, user, "export")
    rows, company_name, department_name = svc.load_list(db, q, period, flt)
    short = {c.id: c.short_name.strip() for c in db.query(Company.id, Company.short_name).all()
             if (c.short_name or "").strip()}
    return benefit_export(rows, flt, company_name, department_name, short)


@router.get("/summary/rows", dependencies=_GUARD)
def benefit_summary_rows(request: Request, db: Session = Depends(get_db),
                         user=Depends(require("employee", "read"))):
    q, period, flt = _inputs(request, db, user, "read")
    metric, group_by, group_key = parse_rows_params(request.query_params, {"people": svc.LABELS["people"]})
    return success(svc.build_rows(db, q, period, flt, metric, group_by, group_key))
