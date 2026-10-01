"""Xu hướng (`trend`) của `/api/leave-requests/summary` — GOM theo NGÀY THÔ ở SQL rồi dồn lên
trục ngày/tuần/tháng Ở PYTHON bằng `report_period.bucket_of` (CHƯA từng có hơn ~1.096 ngày
trong một kỳ — `MAX_RANGE_DAYS` của `report_period.py` chặn sẵn), KHÔNG tính bucket tuần/tháng
ngay trong SQL — tránh phải portable hóa luật "tuần bắt đầu thứ Hai"/"cắt theo biên kỳ" giữa
SQLite và MySQL, đúng chủ trương chung đã chọn cho cả khung báo cáo (xem `report_period.py`).

`people_on_leave` KHÔNG thể suy ra bằng cách CỘNG số đếm DISTINCT theo từng ngày rồi gộp lên
tuần/tháng — một nhân sự nghỉ 2 ngày khác nhau trong CÙNG một tuần sẽ bị đếm 2 lần nếu cộng
thẳng số đã đếm riêng của từng ngày. Phải giữ một hình chiếu NHẸ (ngày, mã nhân sự) rồi tự gom
bằng `set()` theo mốc trục — cách rẻ nhất mà vẫn đúng (gói B, review hiệu năng 01/10/2026).
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.report_compute import compute_derived
from app.core.report_period import bucket_of
from app.modules.leave.constants import LR_APPROVED
from app.modules.leave.report_sql_metrics import DERIVED, ZERO_METRICS, header_aggregate, line_aggregate
from app.modules.leave.request_model import LeaveRequest


def people_on_leave_points(scoped_query) -> list[tuple[date, int]]:
    """Hình chiếu NHẸ (ngày, mã nhân sự) — CHỈ đơn đã duyệt, CHỈ phục vụ gom `people_on_leave`
    theo mốc trục. Số dòng ≤ số đơn ĐÃ DUYỆT trong kỳ, 2 cột — nhẹ hơn hẳn gọi đủ 5 chỉ số."""
    rows = (scoped_query.filter(LeaveRequest.status == LR_APPROVED, LeaveRequest.employee_id != 0)
           .with_entities(LeaveRequest.from_date, LeaveRequest.employee_id).all())
    return [(r.from_date, r.employee_id) for r in rows]


def trend_for_period(db: Session, scoped_query, header_subq, axis: list[dict], granularity: str,
                     shift=None) -> list[dict]:
    """`trend` cho MỘT kỳ — gọi 1 lần cho kỳ này; gọi lại kèm `shift`
    (`report_compute.compare_shift`, H1) cho kỳ so sánh để dồn đúng lên trục kỳ NÀY thay vì tự
    tính độ hạt riêng rồi ghép theo chỉ số mốc."""
    by_bucket = {a["key"]: dict(ZERO_METRICS) for a in axis}

    def _bucket_key(d: date) -> str | None:
        dd = shift(d) if shift else d
        k = bucket_of(dd, granularity)
        return k if k in by_bucket else None   # ngày dời ra ngoài biên kỳ so sánh → bỏ (H1)

    for r in header_aggregate(db, scoped_query, group_col=LeaveRequest.from_date):
        k = _bucket_key(r.key)
        if k is None:
            continue
        b = by_bucket[k]
        b["requests"] += int(r.requests or 0)
        b["requests_reject_return"] += int(r.requests_reject_return or 0)
        b["turnaround_hours_sum"] += float(r.turnaround_hours_sum or 0)
        b["turnaround_hours_count"] += int(r.turnaround_hours_count or 0)
    for r in line_aggregate(db, header_subq, group_col=header_subq.c.from_date):
        k = _bucket_key(r.key)
        if k is None:
            continue
        b = by_bucket[k]
        b["days_approved"] += float(r.days_approved or 0)
        b["days_pending"] += float(r.days_pending or 0)

    people_sets: dict[str, set[int]] = {a["key"]: set() for a in axis}
    for d, emp_id in people_on_leave_points(scoped_query):
        k = _bucket_key(d)
        if k is not None:
            people_sets[k].add(emp_id)

    out = []
    for a in axis:
        values = dict(by_bucket[a["key"]])
        values["people_on_leave"] = len(people_sets[a["key"]])
        values.update(compute_derived(values, DERIVED))
        out.append({"key": a["key"], "label": a["label"], "values": values})
    return out
