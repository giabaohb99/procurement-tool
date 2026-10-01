"""Báo cáo Công việc — `groups` của chiều "Người phụ trách" (PIC), GOM Ở SQL
(review hiệu năng "gói B", 01/10/2026). Tách khỏi `report_grouped_fetch.py` vì
PIC là NGOẠI LỆ bắt buộc: một task có N PIC thì TỔNG không được đếm N lần
(luật "totals cộng TRỰC TIẾP, không cộng lại từ groups" của `report_aggregate`),
nhưng NHÓM theo PIC thì PHẢI fan N lần — không thể dùng CHUNG một bộ hàng gộp
sẵn ở SQL cho cả hai như 5 chiều còn lại (list/group/company/status/priority,
đều chỉ MỘT giá trị mỗi task nên gộp ở SQL không có rủi ro đếm dôi).

Vì vậy khi `group_by="pic"`: Tổng/Xu hướng tính từ
`report_grouped_fetch.grouped_fetch_rows(..., group_by=None)` (không PIC, đúng số
việc) như mọi `group_by` khác; CÒN `groups` tính RIÊNG ở đây — GROUP BY
`employee_id` cho CẢ KỲ một lượt (không cần trục ngày: `groups` vốn không có xu
hướng theo thời gian, chỉ Tổng theo kỳ), rồi ghép kỳ so sánh bằng
`report_compute.merge_groups_by_key` — TÁI DÙNG đúng hàm `build_report()` dùng
nội bộ cho mọi dimension khác, không chép lại luật hòa điểm/mẫu số 0 (H2/L1).
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from app.core.report_aggregate import EMPTY_LABEL
from app.core.report_compute import compute_derived, drop_snapshot, merge_groups_by_key
from app.core.report_period import range_filter

from . import report_rows as rows
from .model import WorkAssigneeKind
from .report_sql_date import date_diff_days, vn_date_str
from .task_model import WorkTask, WorkTaskAssignee


def _pic_sums(db: Session, scope_ids, d_from: date, d_to: date) -> dict[int, dict]:
    """GOM theo PIC cho CẢ KỲ — JOIN NGOÀI để task KHÔNG có PIC vẫn góp một nhóm
    `eid=0` (ứng với nhãn "(Chưa gắn)", đúng luật `key_of(r) or [("", empty_label)]`
    của bản cũ `bucket_rows`)."""
    created_cond = range_filter(WorkTask.created_at, "datetime_utc", d_from, d_to)
    completed_cond = and_(WorkTask.completed_at.isnot(None),
                          range_filter(WorkTask.completed_at, "datetime_utc", d_from, d_to))
    completed_date = vn_date_str(db, WorkTask.completed_at)
    created_date = vn_date_str(db, WorkTask.created_at)
    has_due = WorkTask.due_date != ""
    on_time = and_(has_due, completed_date <= WorkTask.due_date)

    q = (rows.base_query(db, scope_ids)
         .outerjoin(WorkTaskAssignee, and_(WorkTaskAssignee.task_id == WorkTask.id,
                                           WorkTaskAssignee.kind == int(WorkAssigneeKind.PIC)))
         .filter(or_(created_cond, completed_cond))
         .with_entities(
             WorkTaskAssignee.employee_id.label("eid"),
             func.sum(case((created_cond, 1), else_=0)).label("created"),
             func.sum(case((completed_cond, 1), else_=0)).label("completed"),
             func.sum(case((and_(completed_cond, on_time), 1), else_=0)).label("on_time_count"),
             func.sum(case((and_(completed_cond, has_due), 1), else_=0)).label("due_completed_count"),
             func.sum(case((completed_cond, date_diff_days(db, completed_date, created_date)), else_=0))
                 .label("handling_days_sum"))
         .group_by(WorkTaskAssignee.employee_id)
         .order_by(WorkTaskAssignee.employee_id))
    out: dict[int, dict] = {}
    for r in q.all():
        eid = int(r.eid) if r.eid is not None else 0
        completed_n = int(r.completed or 0)
        out[eid] = {"created": int(r.created or 0), "completed": completed_n,
                    "on_time_count": int(r.on_time_count or 0),
                    "due_completed_count": int(r.due_completed_count or 0),
                    "handling_days_sum": float(r.handling_days_sum or 0),
                    #  Luôn == "completed": `created_at` NOT NULL nên mọi việc hoàn
                    #  thành đều tính được số ngày xử lý (xem docstring `report_rows`).
                    "handling_days_count": completed_n}
    return out


def pic_groups(db: Session, scope_ids, period, spec) -> list[dict]:
    """`groups` của chiều PIC — thay cho `ReportSpec.dimensions["pic"]` (framework
    chung không dùng được ở đây, xem đầu tệp). `period`/`spec` là
    `report_period.Period`/`report_aggregate.ReportSpec` của `report_service.py`,
    không import kiểu tĩnh ở đây để tránh vòng import (cùng lý do `report_compute.py`
    chỉ gợi ý kiểu qua `TYPE_CHECKING`)."""
    if not scope_ids:
        return []
    cur = _pic_sums(db, scope_ids, period.date_from, period.date_to)
    cmp = (_pic_sums(db, scope_ids, period.compare_from, period.compare_to)
          if period.compare != "none" and period.compare_from and period.compare_to else None)
    names = rows.employee_names(db, {eid for eid in {**cur, **(cmp or {})} if eid})

    def to_groups(sums: dict[int, dict]) -> list[dict]:
        out = []
        for eid in sorted(sums):   # thứ tự ổn định — xem docstring đầu tệp về hòa điểm
            values = drop_snapshot(compute_derived(dict(sums[eid]), spec.derived), spec)
            label = names.get(eid, f"#{eid}") if eid else EMPTY_LABEL
            out.append({"key": str(eid) if eid else "", "label": label, "values": values})
        return out

    return merge_groups_by_key(to_groups(cur), to_groups(cmp) if cmp else None, spec, spec.rank_key())
