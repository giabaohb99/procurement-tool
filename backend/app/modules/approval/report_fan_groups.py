"""`groups`/`breakdowns` của hai chiều NHIỀU GIÁ TRỊ/phiên — "Người duyệt"/"Bước" (review hiệu
năng "gói B", 01/10/2026, vòng 2). Tách khỏi `report_grouped_fetch.py` vì đây là NGOẠI LỆ bắt
buộc, cùng lý do `work/report_pic_groups.py` tách PIC: một phiên nhiều người duyệt/bước thì
TỔNG không được đếm dôi (luật "totals cộng TRỰC TIẾP, không cộng lại từ groups" của
`report_aggregate`), nhưng NHÓM theo người duyệt/bước thì PHẢI fan — mỗi (phiên × giá trị) PHÂN
BIỆT góp TOÀN BỘ số liệu của phiên đó vào nhóm, không chỉ phần "của riêng" bước/người đó (thiết
kế CŨ từ vòng 1, giữ nguyên).

Vì vậy Tổng/Xu hướng/breakdown "entity" LUÔN tính từ `report_grouped_fetch.grouped_fetch_rows`
(không fan); CÒN `groups`/breakdown của "approver"/"node_name" tính RIÊNG ở đây — GROUP BY giá
trị chiều cho CẢ KỲ một lượt (không cần trục ngày — `groups`/`breakdowns` không có xu hướng theo
thời gian), rồi ghép kỳ so sánh bằng `report_compute.merge_groups_by_key` (groups) hoặc tự xếp
hạng + cắt TOP (breakdown) — TÁI DÙNG đúng luật hòa điểm/mẫu số 0 (H2/L1) của framework chung.

THỨ TỰ khi HÒA ĐIỂM: `ORDER BY` giá trị chiều tăng dần để ổn định/tái lập được — bản cũ (vòng 1)
cũng không có `ORDER BY` tường minh nên thứ tự hòa điểm CHƯA BAO GIỜ là hợp đồng (cùng ghi chú ở
`work/report_grouped_fetch.py`); bài kiểm tương đương chọn dữ liệu không hòa điểm đúng ở chỉ số
xếp hạng để so khớp JSON tuyệt đối.
"""
from __future__ import annotations

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.report_aggregate import BREAKDOWN_LIMIT, EMPTY_LABEL
from app.core.report_compute import compute_derived, drop_snapshot, merge_groups_by_key

from . import report_grouped_fetch as grouped
from .instance_model import (ApprovalInstance, INSTANCE_APPROVED, INSTANCE_REJECTED,
                             INSTANCE_RETURNED, INSTANCE_WITHDRAWN)


def _metric_cols(m) -> list:
    """Cột chỉ số đọc từ `instance_metrics_subquery` — dùng CHUNG cho cả nhóm ĐÃ GẮN (GROUP BY
    giá trị chiều) lẫn nhóm "(Chưa gắn)" (xem `_fan_sums`), tránh chép hai lần."""
    return [func.count().label("sessions"),
           func.sum(case((m.c.status == INSTANCE_APPROVED, 1), else_=0)).label("approved"),
           func.sum(case((m.c.status == INSTANCE_REJECTED, 1), else_=0)).label("rejected"),
           func.sum(case((m.c.status == INSTANCE_RETURNED, 1), else_=0)).label("returned"),
           func.sum(case((m.c.status == INSTANCE_WITHDRAWN, 1), else_=0)).label("withdrawn"),
           func.sum(m.c.proc_hours_sum).label("proc_hours_sum"),
           func.sum(m.c.proc_hours_count).label("proc_hours_count"),
           func.sum(m.c.step_hours_sum).label("step_hours_sum"),
           func.sum(m.c.step_hours_count).label("step_hours_count"),
           func.sum(m.c.step_overdue).label("step_overdue"),
           func.sum(m.c.step_due_known).label("step_due_known")]


def _row_to_values(r) -> dict:
    return {"sessions": int(r.sessions or 0), "approved": int(r.approved or 0),
           "rejected": int(r.rejected or 0), "returned": int(r.returned or 0),
           "withdrawn": int(r.withdrawn or 0), "pending": 0,
           "proc_hours_sum": float(r.proc_hours_sum or 0), "proc_hours_count": int(r.proc_hours_count or 0),
           "step_hours_sum": float(r.step_hours_sum or 0), "step_hours_count": int(r.step_hours_count or 0),
           "step_overdue": int(r.step_overdue or 0), "step_due_known": int(r.step_due_known or 0)}


def fan_sums(db: Session, cond, d_from, d_to, pair_builder) -> dict[str, dict]:
    """GOM theo MỘT chiều fan (approver/node_name) cho CẢ KỲ — `pair_builder(id_subq)` trả
    subquery `(instance_id, value, label)` PHÂN BIỆT (xem `report_step_metrics.py`). `status`
    KHÔNG còn là khóa GROUP BY ở đây (khác `report_grouped_fetch`) nên phải tự `SUM(CASE...)`
    cho bốn trạng thái kết thúc.

    MỘT câu `LEFT JOIN` + `GROUP BY` duy nhất (review hiệu năng vòng 2 — bản đầu tách thành 2
    câu "đã gắn"/"(Chưa gắn)" riêng, tốn THÊM một lượt tính lại chuỗi `LAG() OVER` của
    `step_metrics_subquery` cho câu thứ hai, đo được ~1-1.7s/lượt ở quy mô bench 150k task):
    `pairs.value` NULL (phiên không khớp dòng nào bên `pairs` — approver rỗng vì
    `assignee_employee_id=0`, hoặc về lý thuyết phiên chưa có bước nào) tự nhiên gom thành MỘT
    nhóm NULL qua `GROUP BY` (cả SQLite lẫn MySQL coi mọi NULL bằng nhau khi gộp nhóm) — đúng
    luật `bucket_rows` cũ `key_of(row) or [("", empty_label)]`: phiên không có giá trị chiều nào
    vẫn phải góp một khóa rỗng "(Chưa gắn)", không được biến mất. Người gọi NÊN tính 1 lần/kỳ rồi
    DÙNG LẠI cho cả `groups` lẫn `breakdowns` (xem `report_service.build_summary`) — gọi lặp lại
    với cùng `(d_from, d_to, pair_builder)` là tính lại chuỗi cửa sổ một cách lãng phí."""
    if d_from is None or d_to is None:
        return {}
    id_subq = grouped.scoped_instance_ids(cond, d_from, d_to)
    m = grouped.instance_metrics_subquery(db, cond, d_from, d_to)
    pairs = pair_builder(id_subq)
    q = (select(pairs.c.value.label("value"), func.max(pairs.c.label).label("label"), *_metric_cols(m))
        .select_from(m.outerjoin(pairs, pairs.c.instance_id == m.c.id))
        .group_by(pairs.c.value)
        .order_by(pairs.c.value))
    out: dict[str, dict] = {}
    for r in db.execute(q).all():
        key = "" if r.value is None else str(r.value)
        label = r.label if r.label else key
        out[key] = {"label": label, "values": _row_to_values(r)}
    return out


def format_groups(cur: dict[str, dict], cmp: dict[str, dict] | None, spec) -> list[dict]:
    """`groups` của một chiều fan từ sẵn `fan_sums(...)` của kỳ này/kỳ so sánh — thay cho
    `ReportSpec.dimensions[...]` (framework chung không dùng được ở đây, xem đầu tệp). Tách khỏi
    việc GỌI `fan_sums` để `report_service.build_summary` tính SUM một lần rồi dùng lại cho cả
    `groups` lẫn `breakdowns` (xem docstring `fan_sums`)."""
    def to_groups(sums: dict[str, dict]) -> list[dict]:
        out = []
        for key in sorted(sums):   # thứ tự ổn định — xem docstring đầu tệp về hòa điểm
            values = drop_snapshot(compute_derived(dict(sums[key]["values"]), spec.derived), spec)
            out.append({"key": key, "label": sums[key]["label"] or EMPTY_LABEL, "values": values})
        return out

    return merge_groups_by_key(to_groups(cur), to_groups(cmp) if cmp else None, spec, spec.rank_key())


def format_breakdown(cur: dict[str, dict], spec) -> list[dict]:
    """Breakdown "Top" của một chiều fan từ sẵn `fan_sums(...)` kỳ hiện tại — breakdown KHÔNG
    ghép kỳ so sánh (đúng hợp đồng chung của `report_aggregate.aggregate()`), cắt
    `BREAKDOWN_LIMIT`."""
    rank = spec.rank_key()
    items = [{"key": key, "label": v["label"] or EMPTY_LABEL,
             "value": compute_derived(dict(v["values"]), spec.derived).get(rank, 0) or 0}
            for key, v in cur.items()]
    items = sorted((i for i in items if i["value"]), key=lambda x: x["value"], reverse=True)
    return items[:BREAKDOWN_LIMIT]
