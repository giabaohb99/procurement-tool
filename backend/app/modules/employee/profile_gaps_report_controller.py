"""Báo cáo "Hồ sơ & tài khoản còn thiếu" — router RIÊNG (duoc-CR-686, khóa 18).

Ba đường: `/profile-gaps/summary`, `/profile-gaps/summary/export`, `/profile-gaps/summary/rows`.
Đăng ký trong `main.py` TRƯỚC `employee_router` (`/{eid}` nuốt `profile-gaps`). Gác KÉP:
`require('employee', read|export)` + `require_report(HR_PROFILE_GAPS)`; phạm vi
`apply_scope(Employee, 'employee')`; `company_id` / `department_id` lọc SAU phạm vi, chỉ thu hẹp.
Nhóm nhạy cảm cần thêm `employee_sensitive.read`, nhóm tài khoản cần `user.read` — thiếu thì
chỉ số đó vắng hẳn (và `/rows` của nó trả 422 như một chỉ số không tồn tại).
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

from . import profile_gaps_report_service as svc
from .model import Employee

router = APIRouter(prefix="/api/employees/profile-gaps", tags=["employee"])
_GUARD = [Depends(require_report(ReportKey.HR_PROFILE_GAPS))]


def _inputs(request: Request, db: Session, user) -> dict:
    prof = get_perm_profile(db, user)
    perms = prof.get("perms_union") or {}
    qp = request.query_params
    return dict(
        employees_q=apply_scope(db.query(Employee), Employee, "employee", user, prof),
        with_sensitive=bool((perms.get("employee_sensitive") or {}).get("read")),
        with_account=bool((perms.get("user") or {}).get("read")),
        company_id=valid_company_id(qp.get("company_id")),
        department_id=valid_department_id(qp.get("department_id")))


@router.get("/summary", dependencies=_GUARD)
def profile_gaps_summary(request: Request, db: Session = Depends(get_db),
                         user=Depends(require("employee", "read"))):
    kw = _inputs(request, db, user)
    return success(svc.build_summary(db, period=parse_period(request.query_params),
                                     group_by=request.query_params.get("group_by") or None, **kw))


@router.get("/summary/export", dependencies=_GUARD)
def profile_gaps_summary_export(request: Request, db: Session = Depends(get_db),
                                user=Depends(require("employee", "export"))):
    kw = _inputs(request, db, user)
    data = svc.build_summary(db, period=parse_period(request.query_params),
                             group_by=request.query_params.get("group_by") or None, **kw)
    return report_xlsx("ho-so-tai-khoan-con-thieu", data)


@router.get("/summary/rows", dependencies=_GUARD)
def profile_gaps_summary_rows(request: Request, db: Session = Depends(get_db),
                              user=Depends(require("employee", "read"))):
    kw = _inputs(request, db, user)
    allowed = {k: svc.LABELS[k] for k in ("active_total", *svc.visible_gaps(kw["with_sensitive"], kw["with_account"]))}
    metric, group_by, group_key = parse_rows_params(request.query_params, allowed)
    return success(svc.build_rows(db, metric=metric, group_by=group_by, group_key=group_key, **kw))
