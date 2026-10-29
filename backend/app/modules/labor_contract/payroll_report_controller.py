"""Báo cáo A5 «Quỹ lương theo pháp nhân» (khóa 21) — duoc-CR-688.

Router riêng chỉ chứa `/summary` + `/summary/export` + `/summary/rows` (khung báo cáo kiểu Haravan).
Đường gốc `/api/payroll-fund` cố ý KHÔNG nằm dưới `/api/employees` / `/api/labor-contracts` để khỏi bị
`/{id}` của router chính nuốt. Cả ba gác KÉP: `require('labor_contract', read|export)` +
`require_report(PAYROLL_FUND)`; phạm vi qua `apply_scope(LaborContract)`; `company_id` / `department_id`
(của HĐ) chỉ thu hẹp thêm. Nhóm nhỏ bị che với MỌI người xem (số lương) — xem `payroll_report_service`.
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
from .access import has_perm
from .model import LaborContract

router = APIRouter(prefix="/api/payroll-fund", tags=["report"])
_GUARD = [Depends(require_report(ReportKey.PAYROLL_FUND))]


def _inputs(request: Request, db: Session, user, action: str = "read") -> dict:
    """Tham số chung của cả ba đường: kỳ, bộ lọc và truy vấn HĐ đã qua phạm vi."""
    prof = get_perm_profile(db, user)
    qp = request.query_params
    return dict(contracts_q=apply_scope(db.query(LaborContract), LaborContract, "labor_contract", user, prof, action),
                period=parse_period(qp), company_id=valid_company_id(qp.get("company_id")),
                department_id=valid_department_id(qp.get("department_id")))


def _employees_q(db: Session, user, prof: dict, action: str):
    """Truy vấn nhân sự đã qua phạm vi để đếm người chưa có HĐ hiệu lực; người xem không có quyền xem nhân sự → `None`."""
    if not has_perm(prof, "employee", action):
        return None
    return apply_scope(db.query(Employee), Employee, "employee", user, prof, action)


@router.get("/summary", dependencies=_GUARD)
def payroll_fund_summary(request: Request, db: Session = Depends(get_db),
                         user=Depends(require("labor_contract", "read"))):
    kw = _inputs(request, db, user)
    emp_q = _employees_q(db, user, get_perm_profile(db, user), "read")
    return success(service.build_summary(db, group_by=request.query_params.get("group_by") or None,
                                         employees_q=emp_q, **kw))


@router.get("/summary/export", dependencies=_GUARD)
def payroll_fund_summary_export(request: Request, db: Session = Depends(get_db),
                                user=Depends(require("labor_contract", "export"))):
    kw = _inputs(request, db, user, "export")   # phạm vi theo quyền XUẤT, không theo quyền xem
    emp_q = _employees_q(db, user, get_perm_profile(db, user), "export")
    data = service.build_summary(db, group_by=request.query_params.get("group_by") or None, employees_q=emp_q, **kw)
    return report_xlsx("quy-luong", data)


@router.get("/summary/rows", dependencies=_GUARD)
def payroll_fund_summary_rows(request: Request, db: Session = Depends(get_db),
                              user=Depends(require("labor_contract", "read"))):
    metric, group_by, group_key = parse_rows_params(request.query_params, service.METRICS)
    kw = _inputs(request, db, user)
    return success(service.build_rows(db, metric=metric, group_by=group_by, group_key=group_key, **kw))
