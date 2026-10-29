"""Báo cáo Hợp đồng lao động — router RIÊNG (duoc-CR-686, khóa 17).

Ba đường: `/summary`, `/summary/export`, `/summary/rows` (bấm số ra danh sách). Đăng ký trong
`main.py` TRƯỚC `labor_contract_router` để `/api/labor-contracts/{cid}` không nuốt `summary`.
Cả ba gác KÉP: `require('labor_contract', read|export)` + `require_report(LABOR_CONTRACT)`.
Phạm vi: HĐ qua `apply_scope(LaborContract)`, người chưa có HĐ qua `apply_scope(Employee)`;
`company_id` / `department_id` lọc SAU phạm vi, chỉ thu hẹp.
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

from . import report_service
from .model import LaborContract

router = APIRouter(prefix="/api/labor-contracts", tags=["labor_contract"])
_GUARD = [Depends(require_report(ReportKey.LABOR_CONTRACT))]


def _inputs(request: Request, db: Session, user) -> dict:
    """Tham số chung của cả ba đường: kỳ, bộ lọc và HAI truy vấn đã qua phạm vi."""
    prof = get_perm_profile(db, user)
    qp = request.query_params
    return dict(
        contracts_q=apply_scope(db.query(LaborContract), LaborContract, "labor_contract", user, prof),
        employees_q=apply_scope(db.query(Employee), Employee, "employee", user, prof),
        period=parse_period(qp), company_id=valid_company_id(qp.get("company_id")),
        department_id=valid_department_id(qp.get("department_id")))


@router.get("/summary", dependencies=_GUARD)
def labor_contract_summary(request: Request, db: Session = Depends(get_db),
                           user=Depends(require("labor_contract", "read"))):
    kw = _inputs(request, db, user)
    return success(report_service.build_summary(db, group_by=request.query_params.get("group_by") or None, **kw))


@router.get("/summary/export", dependencies=_GUARD)
def labor_contract_summary_export(request: Request, db: Session = Depends(get_db),
                                  user=Depends(require("labor_contract", "export"))):
    kw = _inputs(request, db, user)
    data = report_service.build_summary(db, group_by=request.query_params.get("group_by") or None, **kw)
    return report_xlsx("hop-dong-lao-dong", data)


@router.get("/summary/rows", dependencies=_GUARD)
def labor_contract_summary_rows(request: Request, db: Session = Depends(get_db),
                                user=Depends(require("labor_contract", "read"))):
    metric, group_by, group_key = parse_rows_params(
        request.query_params, {k: v[0] for k, v in report_service.METRICS.items()})
    kw = _inputs(request, db, user)
    return success(report_service.build_rows(db, metric=metric, group_by=group_by,
                                             group_key=group_key, **kw))
