"""Truy vấn NỀN cho báo cáo Nghỉ phép — phạm vi + lọc kỳ, dùng chung bởi mọi hàm
GOM Ở SQL (`report_sql_metrics.py`, `report_sql_trend.py`, `report_service.py`).

Review hiệu năng 01/10/2026 (gói B): bản CŨ nạp TOÀN BỘ đơn + dòng loại nghỉ
thành đối tượng Python (`LeaveRow`) rồi cộng bằng `report_aggregate.aggregate()`
— ở quy mô 60 nghìn đơn/3 năm, 79% thời gian nằm ở vòng lặp Python đó
(`group_by=employee` 1.898–22.897ms, xem báo cáo load-test). Bản MỚI không còn
nạp hàng thô: mỗi hàm GOM ở `report_sql_metrics.py` tự `with_entities(...)`
đúng cột cần rồi để DATABASE cộng (SUM/COUNT/COUNT DISTINCT), nên tệp này chỉ
còn lo phần DÙNG CHUNG — phạm vi (`apply_scope`) + lọc kỳ/trạng thái/công ty +
subquery "đơn đã lọc" để JOIN sang bảng dòng.

`scoped_requests(...)` trả một Query ORM (CHƯA gọi `.all()`), mỗi hàm GOM tự
thêm `.with_entities(...)`/`.group_by(...)` cho đúng chỉ số cần — không hàm nào
được chỉnh sửa Query này quay lại tầng gọi (tránh hiệu ứng lề, builder luôn
dựng Query MỚI từ `scoped_requests`).
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.report_period import range_filter
from app.core.scoping import apply_scope
from app.modules.leave.constants import LR_DRAFT
from app.modules.leave.request_model import LeaveRequest


def scoped_requests(db: Session, user, prof: dict, d_from: date, d_to: date,
                    company_id: int | None = None):
    """Đơn trong PHẠM VI (đã `apply_scope`) + lọc kỳ (`from_date`)/trạng thái/công ty — H1:
    `company_id` lọc SAU `apply_scope`, chỉ THU HẸP thêm, không mở rộng phạm vi."""
    q = apply_scope(db.query(LeaveRequest), LeaveRequest, "leave_request", user, prof)
    if company_id is not None:
        q = q.filter(LeaveRequest.company_id == company_id)
    return (q.filter(LeaveRequest.is_deleted.is_(False), LeaveRequest.status != LR_DRAFT)
           .filter(range_filter(LeaveRequest.from_date, "date", d_from, d_to)))


def header_subquery(scoped_query):
    """Subquery "đơn đã lọc" mang đúng 7 cột mà các hàm GOM dòng (`line_aggregate`) cần JOIN
    vào — company/department/employee/status CHÉP từ đơn (lines không tự có các cột này)."""
    return scoped_query.with_entities(
        LeaveRequest.id, LeaveRequest.status, LeaveRequest.from_date, LeaveRequest.company_id,
        LeaveRequest.department_id, LeaveRequest.employee_id, LeaveRequest.leave_type_id,
    ).subquery()
