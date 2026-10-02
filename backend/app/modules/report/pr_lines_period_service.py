"""Bản THEO KỲ của báo cáo Chi tiết YC mua hàng (P03, `GET /api/reports/pr-lines/summary`
khi có `preset`) — hợp đồng chuẩn `report_aggregate.build_report`. Tách khỏi `service.py`
(đã 735 dòng) để giữ tệp mới dưới 200 dòng; dùng lại `_pr_lines_base_query`/
`_apply_pr_line_filters` của tệp đó nên số liệu luôn khớp bảng `/pr-lines` và bản `year` cũ.
"""
from __future__ import annotations

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_period import Period, range_filter, to_local_date
from app.core.status_codes import PR_LINE_STATUS

from . import service as report_service


def _build_spec(db, emp_names: dict) -> ReportSpec:
    from app.modules.purchase_request.service import LINE_STATUS_CANCELLED, LINE_STATUS_IDLE, LINE_STATUS_NO_PO

    def countable(r) -> bool:
        return (r.line_status or LINE_STATUS_NO_PO) != LINE_STATUS_CANCELLED

    def idle(r) -> bool:
        return (r.line_status or LINE_STATUS_NO_PO) in LINE_STATUS_IDLE

    metrics = [
        MetricSpec("lines", "Số dòng", kind="int", value_of=lambda r: 1 if countable(r) else 0),
        MetricSpec("amount", "Giá trị", kind="money",
                  value_of=lambda r: float(r.amount or 0) if countable(r) else 0),
        MetricSpec("idle_lines", "Dòng chưa đặt", kind="int", good="down",
                  value_of=lambda r: 1 if countable(r) and idle(r) else 0),
        MetricSpec("idle_amount", "Giá trị chưa đặt", kind="money",
                  value_of=lambda r: float(r.amount or 0) if countable(r) and idle(r) else 0),
        MetricSpec("ordered_lines", "Dòng đã đặt", kind="int",
                  value_of=lambda r: 1 if countable(r) and not idle(r) else 0),
    ]
    derived = [DerivedSpec("ordered_rate", "Đã đặt hàng", num="ordered_lines", den="lines", good="up")]

    def assignee_label(code: str) -> str:
        name = emp_names.get(code)
        return f"{code} — {name}" if name else code

    dimensions = {
        "department": DimensionSpec("department", "Bộ phận",
                                    key_of=lambda r: [(r.department, r.department)] if r.department else []),
        "item_group": DimensionSpec("item_group", "Nhóm hàng",
                                    key_of=lambda r: [(r.item_group, r.item_group)] if r.item_group else []),
        "assignee": DimensionSpec("assignee", "NSTM",
                                  key_of=lambda r: [(r.assignee, assignee_label(r.assignee))]
                                  if r.assignee else []),
        "line_status": DimensionSpec(
            "line_status", "Tiến độ dòng",
            key_of=lambda r: [((r.line_status or LINE_STATUS_NO_PO),
                               PR_LINE_STATUS.label_of(r.line_status or LINE_STATUS_NO_PO,
                                                       r.line_status or LINE_STATUS_NO_PO))]),
    }
    return ReportSpec(date_of=lambda r: to_local_date(r.request_date), metrics=metrics, derived=derived,
                      dimensions=dimensions, breakdowns=dimensions, rank_by="amount")


def compute_pr_lines_summary_period(db, user, period: Period, *, company_id=None, group_by=None,
                                    status=None, line_status=None, assignee=None, search=None) -> dict:
    """Hợp đồng chuẩn cho `/api/reports/pr-lines/summary` (+ `/export`) khi có `preset`."""
    from app.modules.employee.model import Employee
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem

    base = report_service._apply_pr_line_filters(
        report_service._pr_lines_base_query(db, user, None, company_id),
        status=status, line_status=line_status, assignee=assignee, search=search)

    def fetch(d_from, d_to):
        q = base.filter(range_filter(PurchaseRequest.request_date, "str", d_from, d_to))
        return q.with_entities(PurchaseRequest.request_date, PurchaseRequest.department,
                               PurchaseRequestItem.item_group, PurchaseRequestItem.assignee,
                               PurchaseRequestItem.line_status, PurchaseRequestItem.amount).all()

    codes = [c for (c,) in base.with_entities(PurchaseRequestItem.assignee).distinct().all() if c]
    emp_names = dict(db.query(Employee.code, Employee.full_name)
                     .filter(Employee.code.in_(codes)).all()) if codes else {}

    data = build_report(fetch, _build_spec(db, emp_names), period, group_by=group_by)
    #  M2 (review 28/09/2026): mọi chỉ số ở đây BỎ dòng đã hủy, kể cả khi "Xem theo" 'Tiến độ
    #  dòng' — nhóm 'Đã hủy' vì vậy hiện 0 dòng (không phải lỗi hiển thị). Ghi chú CŨ ("riêng
    #  Tiến độ dòng vẫn đếm đủ") sai với hành vi thật nên bỏ, không thêm chỉ số đếm riêng cho
    #  tỷ lệ hủy (YAGNI — chưa ai cần, xem báo cáo Chi tiết YC mua hàng bản `year` cũ nếu cần).
    data["notes"] = data.get("notes", []) + [
        "Số liệu BỎ dòng đã hủy ở MỌI chỉ số, kể cả khi 'Xem theo' Tiến độ dòng — nhóm 'Đã hủy' "
        "vì vậy luôn hiện 0 dòng.",
    ]
    return data
