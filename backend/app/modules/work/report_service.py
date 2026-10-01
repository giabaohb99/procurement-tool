"""Báo cáo Công việc / Dự án (phase 06) — khung `report_aggregate.build_report`.

Chốt THẬT là `list_id IN visible_list_ids(...)` (`work_task` khai PUBLIC ở
`SCOPE_FIELDS`, xem đầu `membership_service.py`) — route gọi `compute_work_summary`
PHẢI tự lấy `employee_id` qua `require_employee` trước (0 bị chặn ở đó, không
phải ở đây). `report_rows.py` giữ phần NỀN dùng chung (phạm vi, tra tên) + docstring
giải thích vì sao MỘT việc góp tối đa HAI hàng; hai luồng sự kiện (tạo mới/hoàn
thành) GOM Ở SQL nằm ở `report_grouped_fetch.py` (+ `report_pic_groups.py` riêng
cho chiều PIC) — xem đoạn "Review hiệu năng" dưới đây.

Hai breakdown "Top dự án theo quá hạn"/"Top PIC theo việc mở" dùng HAI chỉ số
THỜI ĐIỂM (snapshot) khác nhau — khung `report_aggregate` chỉ hỗ trợ MỘT
`rank_by` dùng chung cho mọi breakdown, và snapshot bị `drop_snapshot` gạt khỏi
`groups`/`breakdowns` chung (M1). Nên hai khối này tính TAY ở `_breakdowns` rồi
ghi đè vào `data["breakdowns"]` sau khi `build_report` chạy xong, không đi qua
`ReportSpec.breakdowns`.

Review hiệu năng "gói B" (01/10/2026): `fetch()` GOM Ở SQL qua
`report_grouped_fetch.grouped_fetch_rows` thay vì nạp từng task (xem docstring
đầu tệp đó + `report_pic_groups.py` cho riêng chiều PIC — chiều duy nhất không
gộp chung được với Tổng vì fan nhiều giá trị).
"""
from __future__ import annotations

from datetime import date
from typing import Mapping

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.report_aggregate import (BREAKDOWN_LIMIT, EMPTY_LABEL, DerivedSpec, DimensionSpec,
                                       MetricSpec, ReportSpec, build_report)
from app.core.report_period import Period

from . import report_grouped_fetch as grouped
from . import report_pic_groups
from . import report_rows as rows
from .membership_service import visible_list_ids
from .model import WorkAssigneeKind
from .task_model import WorkTask, WorkTaskAssignee

NOTES = [
    "'Đang mở'/'Quá hạn' tính TẠI MỐC (đã tạo trước mốc, và lúc đó chưa xong: đang OPEN hoặc "
    "DONE sau mốc) — việc đã HỦY không có dấu thời gian 'lúc hủy' nên bị loại khỏi cả hai chỉ "
    "số; không tính việc con/cột mốc — có thể khác màn Tổng quan nếu đang có cột mốc quá hạn.",
    "'Trạng thái'/'Độ ưu tiên' nhóm theo giá trị HIỆN TẠI của việc, không phải tại thời điểm "
    "sự kiện (tạo mới/hoàn thành).",
]


def _snapshot_fn(db: Session, scope_ids):
    """`snapshot(as_of)` — "Đang mở"/"Quá hạn" tính TẠI MỐC `min(as_of, hôm nay
    VN)` qua `report_rows.open_at_query` (M1, review 01/10/2026) — KHÔNG còn chỉ
    đọc trạng thái hiện tại (sai với mọi mốc không phải hôm nay, vd kỳ so sánh)."""

    def snap(as_of: date) -> dict:
        if not scope_ids:
            return {"open_tasks": 0, "overdue_tasks": 0}
        effective = min(as_of, rows.today_vn())
        open_at = rows.open_at_query(db, scope_ids, effective)
        overdue = open_at.filter(WorkTask.due_date != "", WorkTask.due_date < effective.isoformat())
        return {"open_tasks": open_at.count(), "overdue_tasks": overdue.count()}

    return snap


def _breakdowns(db: Session, scope_ids, metas: dict, at: date) -> dict:
    """Hai khối "Top" tính TAY — xem docstring đầu tệp vì sao không đi qua
    `ReportSpec.breakdowns` chung. Dùng CHUNG `open_at_query` với `_snapshot_fn`
    (M1) để "Top dự án theo quá hạn"/"Top PIC theo việc mở" khớp đúng luật với
    hai chỉ số Tổng "Đang mở"/"Quá hạn", không lệch nhau ở một mốc quá khứ."""
    if not scope_ids:
        return {"overdue_by_list": [], "open_by_pic": []}

    overdue_rows = (rows.open_at_query(db, scope_ids, at)
                    .filter(WorkTask.due_date != "", WorkTask.due_date < at.isoformat())
                    .with_entities(WorkTask.list_id, func.count(WorkTask.id))
                    .group_by(WorkTask.list_id).all())
    overdue_by_list = sorted(
        ({"key": str(lid), "label": metas.get(lid, rows.EMPTY_LIST_META)["name"] or EMPTY_LABEL,
          "value": int(n)} for lid, n in overdue_rows if n),
        key=lambda x: x["value"], reverse=True)[:BREAKDOWN_LIMIT]

    #  Subquery id việc đang mở TẠI MỐC — JOIN người phụ trách vào đúng tập đó,
    #  vẫn MỘT câu SQL (không tăng số lượt hỏi CSDL).
    open_task_ids = rows.open_at_query(db, scope_ids, at).with_entities(WorkTask.id).subquery()
    open_rows = (db.query(WorkTaskAssignee.employee_id, func.count(func.distinct(WorkTaskAssignee.task_id)))
                .filter(WorkTaskAssignee.task_id.in_(db.query(open_task_ids.c.id)),
                        WorkTaskAssignee.kind == int(WorkAssigneeKind.PIC))
                .group_by(WorkTaskAssignee.employee_id).all())
    names = rows.employee_names(db, {eid for eid, _ in open_rows})
    open_by_pic = sorted(
        ({"key": str(eid), "label": names.get(eid, f"#{eid}"), "value": int(n)}
         for eid, n in open_rows if n),
        key=lambda x: x["value"], reverse=True)[:BREAKDOWN_LIMIT]

    return {"overdue_by_list": overdue_by_list, "open_by_pic": open_by_pic}


def _build_spec() -> ReportSpec:
    #  `value_of` đọc `r["cnt"]`/`r.get(...)` chứ không còn hằng `1` (review hiệu
    #  năng "gói B", 01/10/2026): một "hàng" từ `report_grouped_fetch` nay đại
    #  diện N task đã GOM Ở SQL (GROUP BY ngày + chiều Xem theo), không phải 1
    #  task — `compute_metrics` cộng đúng N vì đọc thẳng cột đã SUM/COUNT sẵn.
    #  `handling_days_count` == `cnt` của hàng "completed": `created_at` NOT NULL
    #  nên MỌI việc hoàn thành đều tính được số ngày xử lý (không có "thiếu dữ
    #  liệu" như định nghĩa cũ `r.get("handling_days") is not None` ngụ ý).
    metrics = [
        MetricSpec("created", "Việc tạo mới", kind="int",
                  value_of=lambda r: r["cnt"] if r["event"] == "created" else 0),
        MetricSpec("completed", "Việc hoàn thành", kind="int", good="up",
                  value_of=lambda r: r["cnt"] if r["event"] == "completed" else 0),
        #  Hai chỉ số THỜI ĐIỂM (M1) — `value_of` luôn 0 (bị `drop_snapshot` gạt khỏi
        #  trend/groups), `_snapshot_fn` ghi đè giá trị thật lên `totals`. Khai ở đây chỉ
        #  để `meta` có nhãn/loại cho FE và cột Excel.
        MetricSpec("open_tasks", "Đang mở", kind="int", snapshot=True, value_of=lambda r: 0),
        MetricSpec("overdue_tasks", "Quá hạn", kind="int", good="down", snapshot=True,
                  value_of=lambda r: 0),
        #  Bốn chỉ số PHỤ — chỉ làm mẫu số/tử số của hai `derived` dưới đây (L4).
        MetricSpec("on_time_count", "Hoàn thành đúng hạn", kind="int", helper=True,
                  value_of=lambda r: r.get("on_time_cnt", 0) if r["event"] == "completed" else 0),
        MetricSpec("due_completed_count", "Hoàn thành có hạn", kind="int", helper=True,
                  value_of=lambda r: r.get("due_completed_cnt", 0) if r["event"] == "completed" else 0),
        MetricSpec("handling_days_sum", "Tổng ngày hoàn thành", kind="days", helper=True,
                  value_of=lambda r: r.get("handling_days_sum", 0) if r["event"] == "completed" else 0),
        MetricSpec("handling_days_count", "Số việc có ngày hoàn thành", kind="int", helper=True,
                  value_of=lambda r: r["cnt"] if r["event"] == "completed" else 0),
    ]
    derived = [
        DerivedSpec("on_time_rate", "Tỷ lệ đúng hạn", num="on_time_count",
                    den="due_completed_count", kind="percent", good="up"),
        #  `scale=1`: mặc định của DerivedSpec là ×100 cho tỷ lệ % — đây là TRUNG BÌNH ngày.
        DerivedSpec("avg_handling_days", "Ngày hoàn thành TB", num="handling_days_sum",
                    den="handling_days_count", kind="days", good="down", scale=1),
    ]
    dimensions = {
        "list": DimensionSpec("list", "Dự án",
                              key_of=lambda r: [(r["list_id"], r["list_name"])] if r["list_id"] else []),
        "group": DimensionSpec("group", "Nhóm dự án",
                               key_of=lambda r: [(r["group_id"], r["group_name"])] if r["group_id"] else []),
        #  `key_of` không bao giờ được `aggregate()` gọi tới nữa (compute_work_summary
        #  luôn rewrite group_by="pic" -> None trước khi gọi `build_report`, xem bên
        #  dưới) — khai ở đây CHỈ để `meta.dimensions` còn liệt kê "pic" cho FE.
        "pic": DimensionSpec("pic", "Người phụ trách", key_of=lambda r: r.get("pics", [])),
        "company": DimensionSpec("company", "Công ty",
                                 key_of=(lambda r: [(r["company_id"], r["company_name"])]
                                        if r["company_id"] else [])),
        "status": DimensionSpec("status", "Trạng thái",
                                key_of=lambda r: [(r["status"], r["status_label"])]),
        "priority": DimensionSpec("priority", "Độ ưu tiên",
                                  key_of=(lambda r: [(r["priority_name"], r["priority_name"])]
                                         if r["priority_name"] else [])),
    }
    return ReportSpec(date_of=lambda r: r["date"], metrics=metrics, derived=derived, dimensions=dimensions)


def compute_work_summary(db: Session, employee_id: int, period: Period, params: Mapping) -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/work/summary` (+ `/export`).

    `employee_id` phải đã qua `require_employee` ở route gọi (0 bị chặn trước đó).
    """
    visible_ids = visible_list_ids(db, employee_id)
    scope_ids = rows.valid_scope_ids(visible_ids, params.get("list_id"))
    group_by = params.get("group_by") or None

    #  Điểm 4 (review hiệu năng 01/10/2026): tên NHÓM dự án và tên CÔNG TY chỉ hỏi
    #  khi đang "Xem theo" đúng chiều đó — Tổng quan (`group_by=none`) bỏ cả hai.
    metas = rows.list_meta(db, scope_ids, need_group_names=(group_by == "group"))
    companies = rows.company_names(db) if group_by == "company" else {}
    spec = _build_spec()

    #  "pic" KHÔNG truyền cho `build_report`: GOM theo PIC ở SQL sẽ fan Tổng/Xu
    #  hướng theo số PIC (sai, đếm dôi) — xem docstring đầu `report_pic_groups.py`.
    #  Tổng/Xu hướng ở đây luôn tính KHÔNG PIC, `groups` của "pic" ghép tay bên dưới.
    sql_group_by = None if group_by == "pic" else group_by

    def fetch(d_from: date, d_to: date) -> list[dict]:
        return grouped.grouped_fetch_rows(db, scope_ids, d_from, d_to, metas, companies, sql_group_by)

    data = build_report(fetch, spec, period, group_by=sql_group_by, snapshot=_snapshot_fn(db, scope_ids))
    if group_by == "pic":
        data["meta"]["group_by"] = "pic"
        data["groups"] = report_pic_groups.pic_groups(db, scope_ids, period, spec)
    data["breakdowns"] = _breakdowns(db, scope_ids, metas, min(period.date_to, rows.today_vn()))
    data["notes"] = data.get("notes", []) + NOTES
    return data
