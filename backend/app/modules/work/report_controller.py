"""Báo cáo Công việc / Dự án (phase 06).

Router RIÊNG chỉ chứa `/summary` + `/summary/export` (khung báo cáo kiểu Haravan,
`core/report_aggregate.py`). Đăng ký trong `main.py` TRƯỚC router chính của phân hệ để
`/summary` không bị `/{id}` nuốt (422).

Gác CỬA 1 bằng `require("work_task", ...)` như mọi route khác của phân hệ; cửa 2
(ai thấy dự án nào) là việc của `report_service.compute_work_summary`, qua
`visible_list_ids`. `_actor` giống hệt `controller.py`/`task_controller.py`:
chặn luôn tài khoản chưa gắn nhân sự (`employee_id=0` → 400).
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.report_export import report_xlsx
from app.core.report_period import parse_period
from app.core.response import success

from . import report_service as rpt
from .membership_service import require_employee, resolve_actor

router = APIRouter(prefix="/api/work", tags=["work"])


def _actor(db: Session, user):
    actor = resolve_actor(db, user)
    require_employee(actor)
    return actor


@router.get("/summary")
def work_summary(request: Request, db: Session = Depends(get_db),
                 user=Depends(require("work_task", "read"))):
    actor = _actor(db, user)
    period = parse_period(request.query_params)
    data = rpt.compute_work_summary(db, actor.employee_id, period, request.query_params)
    return success(data)


@router.get("/summary/export")
def work_summary_export(request: Request, db: Session = Depends(get_db),
                        user=Depends(require("work_task", "export"))):
    actor = _actor(db, user)
    period = parse_period(request.query_params)
    data = rpt.compute_work_summary(db, actor.employee_id, period, request.query_params)
    return report_xlsx("cong-viec", data)
