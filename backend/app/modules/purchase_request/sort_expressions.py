"""YCMH — biểu thức SQL cho các cột danh sách KHÔNG phải cột vật lý (duoc-CR-738).

`apply_sort_from_request(..., allow=...)` nhận map {khóa cột ở giao diện: biểu thức SQLAlchemy}.
Dùng truy vấn con tương quan (correlated scalar subquery) để chạy được cả MySQL 8 lẫn SQLite của bộ test.
"""
from sqlalchemy import func, select

from .model import PurchaseRequest, PurchaseRequestItem


def list_sort_allow() -> dict:
    """Map cho cột tính toán của danh sách YCMH.

    `total` = tổng thành tiền (đã gồm VAT) mọi dòng của phiếu — đúng số `service.list_line_summaries`
    trả cho cột *Tổng tiền*; phiếu chưa có dòng nào tính 0 (khớp serializer).
    """
    total = (
        select(func.coalesce(func.sum(PurchaseRequestItem.amount), 0))
        .where(PurchaseRequestItem.pr_id == PurchaseRequest.id)
        .correlate(PurchaseRequest)
        .scalar_subquery()
    )
    return {"total": total}
