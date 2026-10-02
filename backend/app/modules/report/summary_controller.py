"""Route MỚI của Báo cáo mua hàng kiểu Haravan (P03) — tách khỏi `controller.py` (đã ~460
dòng, xem risk assessment của phase-03) để mỗi tệp giữ dưới 200 dòng.

Đăng ký TRƯỚC `report_router` ở `main.py` cho chắc, dù hiện `report_router` (`/api/reports`)
chưa có route `/procurement/{...}` nào có thể đụng `/procurement/summary`.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.report_export import report_xlsx
from app.core.report_period import parse_period
from app.core.response import success
from app.core.report_keys import ReportKey
from app.modules.report_access.guard import require_report

from .controller import _can_see_ncc
from .procurement_summary_service import compute_procurement_summary

router = APIRouter(prefix="/api/reports", tags=["report"])


@router.get("/procurement/summary", dependencies=[Depends(require_report(ReportKey.PURCHASE_REPORT))])
def procurement_summary(request: Request, db: Session = Depends(get_db),
                        user=Depends(require("report", "read"))):
    """Tổng hợp Báo cáo mua hàng kiểu Haravan — kỳ + so sánh + Xem theo, hợp đồng chuẩn
    `report_aggregate.build_report`. Chiều NCC/NSPT chỉ có khi `_can_see_ncc` đúng."""
    qp = request.query_params
    period = parse_period(qp)
    return success(compute_procurement_summary(
        db, user, period, qp.get("company_id"), qp.get("group_by") or None, _can_see_ncc(db, user)))


@router.get("/procurement/summary/export",
           dependencies=[Depends(require_report(ReportKey.PURCHASE_REPORT))])
def procurement_summary_export(request: Request, db: Session = Depends(get_db),
                               user=Depends(require("report", "export"))):
    qp = request.query_params
    period = parse_period(qp)
    data = compute_procurement_summary(
        db, user, period, qp.get("company_id"), qp.get("group_by") or None, _can_see_ncc(db, user))
    return report_xlsx("mua-hang", data)
