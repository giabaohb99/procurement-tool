"""Báo cáo A5 «Quỹ lương theo pháp nhân» (khóa 21) — duoc-CR-693 (nguồn số: ô lương trên hồ sơ nhân sự).

Router riêng chỉ chứa `/summary` + `/summary/export` + `/summary/rows` (khung báo cáo kiểu Haravan).
Đường gốc `/api/payroll-fund` cố ý KHÔNG nằm dưới `/api/employees` để khỏi bị `/{id}` của router chính nuốt.
Cả ba gác KÉP: `require('employee', read|export)` + `require_report(PAYROLL_FUND)`; phạm vi qua
`apply_scope(Employee, 'employee')` theo CHÍNH quyền đang dùng (xem = read, xuất = export); `company_id` /
`department_id` chỉ thu hẹp thêm. Chỉ có TỔNG, nhóm nhỏ bị che với MỌI người xem — xem `payroll_report_service`.
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
from app.modules.employee.model import Employee
from app.modules.report.procurement_summary_rows import valid_company_id, valid_department_id
from app.modules.report_access.guard import require_report

from . import payroll_report_service as service

router = APIRouter(prefix="/api/payroll-fund", tags=["report"])
_GUARD = [Depends(require_report(ReportKey.PAYROLL_FUND))]


def _inputs(request: Request, db: Session, user, action: str = "read") -> dict:
    """Tham số chung của cả ba đường: kỳ, bộ lọc và truy vấn nhân sự đã qua phạm vi."""
    prof = get_perm_profile(db, user)
    qp = request.query_params
    return dict(employees_q=apply_scope(db.query(Employee), Employee, "employee", user, prof, action),
                period=parse_period(qp), company_id=valid_company_id(qp.get("company_id")),
                department_id=valid_department_id(qp.get("department_id")))


@router.get("/summary", dependencies=_GUARD)
def payroll_fund_summary(request: Request, db: Session = Depends(get_db),
                         user=Depends(require("employee", "read"))):
    kw = _inputs(request, db, user)
    return success(service.build_summary(db, group_by=request.query_params.get("group_by") or None, **kw))


@router.get("/summary/export", dependencies=_GUARD)
def payroll_fund_summary_export(request: Request, db: Session = Depends(get_db),
                                user=Depends(require("employee", "export"))):
    kw = _inputs(request, db, user, "export")   # phạm vi theo quyền XUẤT, không theo quyền xem
    data = service.build_summary(db, group_by=request.query_params.get("group_by") or None, **kw)
    return report_xlsx("quy-luong", data)       # chỉ bảng TỔNG đã che — không có lương từng người


@router.get("/summary/rows", dependencies=_GUARD)
def payroll_fund_summary_rows(request: Request, db: Session = Depends(get_db),
                              user=Depends(require("employee", "read"))):
    metric, group_by, group_key = parse_rows_params(request.query_params, service.METRICS)
    kw = _inputs(request, db, user)
    return success(service.build_rows(db, metric=metric, group_by=group_by, group_key=group_key, **kw))
