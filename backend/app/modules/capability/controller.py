"""API năng lực — `prefix=/api/work-capability` (duoc-CR-656 tải, duoc-CR-657 báo cáo). Chỉ QUẢN TRỊ mặc định.

Gác KÉP như mọi báo cáo: `require("setting", …)` VÀ `require_report(ReportKey.WORK_CAPABILITY)` (khóa 16, gán được cho người khác).
Admin xem tất cả — không `apply_scope` (khóa `setting` không có bảng để lọc). Mỗi lần mở để lại dòng `tab_request_log`
(GET không bị loại): đủ trả lời "ai đã xem năng lực của ai". `/summary`, `/summary/export` khai TRƯỚC `/load`.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.capability_codes import CycleKind, CycleRole
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.response import success
from app.modules.capability import stats_export, stats_service, workload_service
from app.modules.capability.stats_service import StatsFilter
from app.modules.report_access.guard import require_report

router = APIRouter(prefix="/api/work-capability", tags=["work-capability"])
GUARD = [Depends(require_report(ReportKey.WORK_CAPABILITY))]
MAX_IDS = 200


def build_filter(request: Request, company_id, department_id, kind, task_type_id, role) -> StatsFilter:
    """Báo cáo quản trị: không chọn phạm vi nghĩa là TẤT CẢ (người gọi đã qua khóa 16 + `setting`)."""
    period = parse_period({**request.query_params, "compare": "none"})
    if kind is not None and kind not in {int(k) for k in CycleKind}:
        raise HTTPException(422, "Loại phiếu không hợp lệ")
    if role not in {int(r) for r in CycleRole}:
        raise HTTPException(422, "Vai không hợp lệ")
    return StatsFilter(date_from=period.date_from, date_to=period.date_to, role=CycleRole(role),
                       kinds=(kind,) if kind is not None else (), task_type_ids=(task_type_id,) if task_type_id else (),
                       company_id=company_id, department_ids=tuple(department_id or ()), unrestricted=True)


@router.get("/summary", dependencies=GUARD)
def capability_summary(request: Request, company_id: int | None = Query(None, ge=1),
                       department_id: list[int] | None = Query(None, max_length=50), kind: int | None = Query(None, ge=1),
                       task_type_id: int | None = Query(None, ge=1), role: int = Query(int(CycleRole.HANDLER)),
                       db: Session = Depends(get_db), user=Depends(require("setting", "read"))):
    f = build_filter(request, company_id, department_id, kind, task_type_id, role)
    return success({"period": {"date_from": f.date_from.isoformat(), "date_to": f.date_to.isoformat()},
                    **stats_service.fetch_stats(db, f)})


@router.get("/summary/export", dependencies=GUARD)
def capability_summary_export(request: Request, company_id: int | None = Query(None, ge=1),
                              department_id: list[int] | None = Query(None, max_length=50),
                              kind: int | None = Query(None, ge=1), task_type_id: int | None = Query(None, ge=1),
                              role: int = Query(int(CycleRole.HANDLER)), db: Session = Depends(get_db),
                              user=Depends(require("setting", "export"))):
    f = build_filter(request, company_id, department_id, kind, task_type_id, role)
    return stats_export.export_summary(db, user, f)


@router.get("/load", dependencies=GUARD)
def get_current_load(company_id: int | None = Query(None, ge=1),
                     department_id: list[int] | None = Query(None, max_length=50),
                     employee_id: list[int] | None = Query(None, max_length=MAX_IDS),
                     horizon_days: int = Query(14, ge=1, le=workload_service.MAX_HORIZON_DAYS),
                     db: Session = Depends(get_db), user=Depends(require("setting", "read"))):
    """Tải đang ôm từng người, tính lúc gọi. Phải truyền ít nhất một trong `company_id` / `department_id` / `employee_id`."""
    if not (company_id or department_id or employee_id):
        raise HTTPException(422, "Cần chọn pháp nhân, phòng ban hoặc nhân sự — không trả cả công ty khi không nói rõ")
    rows = workload_service.current_load(db, company_id=company_id, department_ids=department_id,
                                         employee_ids=employee_id, horizon_days=horizon_days)
    return success({"items": rows, "count": len(rows), "horizon_days": horizon_days})
