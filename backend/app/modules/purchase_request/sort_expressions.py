"""YCMH — biểu thức SQL cho các cột danh sách KHÔNG phải cột vật lý (duoc-CR-738).

`apply_sort_from_request(..., allow=...)` nhận map {khóa cột ở giao diện: biểu thức SQLAlchemy}.
Dùng truy vấn con tương quan (correlated scalar subquery) để chạy được cả MySQL 8 lẫn SQLite của bộ test.
"""
from sqlalchemy import func, select

from app.core.code_rank_sql import build_value_rank_expression

from .model import PurchaseRequest, PurchaseRequestItem


#  Dòng đời của phiếu (cột `status`) theo đúng thứ tự `PR_STATUS_LABELS` ở giao diện: nhãn đang hiện
#  là tiếng Việt nên xếp theo TIẾN TRÌNH, không theo chữ cái của mã tiếng Anh (duoc-CR-744).
#  Nhánh rẽ (bị trả lại, từ chối) đứng sau chuỗi.
PR_STATUS_ORDER = ("draft", "submitted", "approved", "dispatched", "processing", "purchasing",
                   "purchased", "completed", "rejected", "cancelled", "")


def list_sort_allow() -> dict:
    """Map cho cột tính toán của danh sách YCMH.

    `total` = tổng thành tiền (đã gồm VAT) mọi dòng của phiếu — đúng số `service.list_line_summaries`
    trả cho cột *Tổng tiền*; phiếu chưa có dòng nào tính 0 (khớp serializer).
    `status` xếp theo hạng dòng đời (`PR_STATUS_ORDER`).
    """
    total = (
        select(func.coalesce(func.sum(PurchaseRequestItem.amount), 0))
        .where(PurchaseRequestItem.pr_id == PurchaseRequest.id)
        .correlate(PurchaseRequest)
        .scalar_subquery()
    )
    return {"total": total, "status": build_value_rank_expression(PurchaseRequest.status, PR_STATUS_ORDER)}
