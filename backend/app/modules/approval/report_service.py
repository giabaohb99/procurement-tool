"""Báo cáo Phê duyệt (phase 05, mục 5.4) — khung `report_aggregate.build_report`.

Phiên duyệt KHÔNG mang `company_id` — phạm vi mượn từ chứng từ gốc: mỗi loại đã đăng ký vào
bộ máy duyệt (`APPROVAL_REPORT_SOURCES`) mà người xem CÓ quyền đọc thì chỉ lấy phiên có
`entity_id` nằm trong id ĐÃ LỌC PHẠM VI của module đó (văn bản: `visible_condition`, `None` =
không lọc gì — PHẢI guard `is not None` kẻo `.filter(None)` ra 0 dòng, M5; còn lại:
`apply_scope`). Loại thiếu quyền đọc LOẠI HẲN khỏi mọi số (Q5.4), vắng mặt khỏi
`groups`/`breakdowns` chứ không rơi về 0. Gác bằng `require('approval_flow', 'read'|'export')`.

Review hiệu năng "gói B" (01/10/2026, vòng 2 — vòng 1 chỉ đẩy giờ BƯỚC xuống SQL nhưng vẫn trả
1 hàng/PHIÊN lên Python, 2,9s/100MB ở quy mô bench, chưa đạt mục tiêu <2s/<50MB): `fetch()` nay
GOM THẲNG theo (ngày, entity, status) qua `report_grouped_fetch.grouped_fetch_rows` — số hàng
Python KHÔNG còn tăng theo số phiên nữa (khác vòng 1). Hai chiều NHIỀU GIÁ TRỊ (`approver`/
`node_name`) không gộp chung được với Tổng (fan làm đếm dôi) nên tính RIÊNG ở
`report_fan_groups.py`, cùng khuôn `work/report_pic_groups.py` xử lý PIC.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, false, or_, select
from sqlalchemy.orm import Session

from app.core.auth import user_has_permission
from app.core.export_xlsx import VN_OFFSET
from app.core.report_aggregate import (DerivedSpec, DimensionSpec, MetricSpec, ReportSpec,
                                       build_report)
from app.core.report_period import Period
from app.core.scoping import apply_scope
from app.modules.leave.request_model import LeaveRequest
from app.modules.meeting_room.model import RoomBooking
from app.modules.seal_request.model import SealRequest
from app.modules.vehicle_booking.model import VehicleBooking

from . import report_fan_groups, report_grouped_fetch, report_step_metrics
from .instance_model import (INSTANCE_APPROVED, INSTANCE_REJECTED, INSTANCE_RETURNED,
                             INSTANCE_WITHDRAWN, ApprovalInstance)
from .task_notification import ENTITY_LABELS

#  Hai chiều NHIỀU GIÁ TRỊ/phiên (một phiên nhiều người duyệt/bước) — `build_summary` ép
#  `sql_group_by=None` khi `group_by` là một trong hai khóa này (xem docstring `report_fan_groups.py`
#  vì sao không gộp chung được với Tổng/Xu hướng), rồi tính `groups`/breakdown RIÊNG bằng hàm ở
#  cột tương ứng (`report_step_metrics.<fn>` dựng cặp (instance_id, giá trị) PHÂN BIỆT).
FAN_DIMENSIONS = {"approver": report_step_metrics.approver_pairs_subquery,
                  "node_name": report_step_metrics.node_name_pairs_subquery}

def _document_ids(db: Session, user, profile):
    from app.modules.document.access_service import visible_condition
    from app.modules.document.model import Document
    from app.modules.document.query import documents_query

    q = documents_query(db)
    visible = visible_condition(user, profile, "read")
    return (q.filter(visible) if visible is not None else q).with_entities(Document.id).subquery()

def _scoped_ids(model, entity: str):
    def fn(db: Session, user, profile):
        q = apply_scope(db.query(model).filter(model.is_deleted.is_(False)), model, entity,
                        user, profile)
        return q.with_entities(model.id).subquery()
    return fn

#  Nguồn (Q5.4) PHẢI khớp entity đã `entity_hooks.register(...)`; khóa quyền = tên entity.
APPROVAL_REPORT_SOURCES = {
    "document": _document_ids,
    "seal_request": _scoped_ids(SealRequest, "seal_request"),
    "vehicle_booking": _scoped_ids(VehicleBooking, "vehicle_booking"),
    "leave_request": _scoped_ids(LeaveRequest, "leave_request"),
    "room_booking": _scoped_ids(RoomBooking, "room_booking"),
}

def allowed_source_entities(db: Session, user) -> list[str]:
    """Loại chứng từ mà người xem CÓ quyền đọc — entity khác bị loại khỏi báo cáo (Q5.4)."""
    return [e for e in APPROVAL_REPORT_SOURCES if user_has_permission(db, user, e, "read")]

def _visibility_cond(db: Session, user, profile, allowed: list[str]):
    #  Rỗng -> `false()` (chặn hết, không im lặng rơi về "thấy tất").
    conds = [and_(ApprovalInstance.entity == e,
                 ApprovalInstance.entity_id.in_(select(APPROVAL_REPORT_SOURCES[e](db, user, profile).c.id)))
            for e in allowed]
    return or_(*conds) if conds else false()

def build_spec() -> ReportSpec:
    #  `value_of` đọc `r["cnt"]`/`r["status"]` — một "hàng" từ `report_grouped_fetch` đại diện N
    #  phiên đã GOM Ở SQL theo (ngày, entity, status), không phải 1 phiên (review hiệu năng "gói
    #  B" vòng 2). `proc_hours_sum`/`proc_hours_count`/`step_hours_*`/`step_overdue`/
    #  `step_due_known` đã CỘNG SẴN ở SQL cho cả nhóm.
    def status_is(code):
        return lambda r: r["cnt"] if r["status"] == code else 0

    metrics = [
        MetricSpec("sessions", "Phiên duyệt", kind="int", value_of=lambda r: r["cnt"]),
        MetricSpec("approved", "Đã duyệt", kind="int", value_of=status_is(INSTANCE_APPROVED)),
        MetricSpec("rejected", "Từ chối", kind="int", value_of=status_is(INSTANCE_REJECTED)),
        MetricSpec("returned", "Trả về", kind="int", value_of=status_is(INSTANCE_RETURNED)),
        MetricSpec("withdrawn", "Rút", kind="int", value_of=status_is(INSTANCE_WITHDRAWN)),
        MetricSpec("pending", "Đang chờ", kind="int", good="down", snapshot=True, value_of=lambda r: 0),
        MetricSpec("proc_hours_sum", "Tổng giờ xử lý phiên", kind="hours", helper=True,
                  value_of=lambda r: r["proc_hours_sum"]),
        MetricSpec("proc_hours_count", "Số phiên có thời gian xử lý", kind="int", helper=True,
                  value_of=lambda r: r["proc_hours_count"]),
        MetricSpec("step_hours_sum", "Tổng giờ mỗi bước", kind="hours", helper=True,
                  value_of=lambda r: r["step_hours_sum"]),
        MetricSpec("step_hours_count", "Số bước có thời gian", kind="int", helper=True,
                  value_of=lambda r: r["step_hours_count"]),
        MetricSpec("step_overdue", "Số bước quá hạn", kind="int", helper=True,
                  value_of=lambda r: r["step_overdue"]),
        MetricSpec("step_due_known", "Số bước có hạn", kind="int", helper=True,
                  value_of=lambda r: r["step_due_known"]),
    ]
    derived = [
        DerivedSpec("avg_proc_hours", "Thời gian xử lý phiên TB", num="proc_hours_sum",
                   den="proc_hours_count", kind="hours", good="down", scale=1),
        DerivedSpec("avg_step_hours", "Thời gian mỗi bước TB", num="step_hours_sum",
                   den="step_hours_count", kind="hours", good="down", scale=1),
        DerivedSpec("step_overdue_rate", "Tỷ lệ bước quá hạn", num="step_overdue",
                   den="step_due_known", good="down"),
    ]
    entity_dim = DimensionSpec("entity", "Loại chứng từ", key_of=lambda r: (
        [(r["entity"], ENTITY_LABELS.get(r["entity"], r["entity"]))] if r.get("entity") else []))
    dimensions = {
        "entity": entity_dim,
        #  `key_of` KHÔNG BAO GIỜ được `aggregate()` gọi tới nữa: `build_summary` ép
        #  `sql_group_by=None` khi `group_by` là approver/node_name (`FAN_DIMENSIONS`), và hai
        #  chiều này KHÔNG nằm trong `breakdowns` bên dưới — khai ở đây CHỈ để `meta.dimensions`
        #  còn liệt kê cho FE (cùng khuôn `work/report_service.py` xử lý PIC).
        "approver": DimensionSpec("approver", "Người duyệt", key_of=lambda r: []),
        "node_name": DimensionSpec("node_name", "Bước", key_of=lambda r: []),
    }
    #  `breakdowns` CHỈ "entity" đi qua framework chung — approver/node_name GHÉP TAY vào
    #  `data["breakdowns"]` sau khi `build_report()` chạy xong (xem `build_summary`), vì hàng
    #  GOM Ở SQL cho Tổng/Xu hướng không mang thông tin approver/node_name (không fan).
    return ReportSpec(date_of=lambda r: r["date"], metrics=metrics, derived=derived,
                      dimensions=dimensions, breakdowns={"entity": entity_dim})

def make_snapshot(db: Session, user, profile, allowed: list[str], period: Period):
    """"Đang chờ" đúng TẠI MỐC `as_of` (M2), không đọc `status` hiện tại: phiên ĐANG MỞ tại
    `as_of` là phiên BẮT ĐẦU trước `cutoff` (nửa đêm VN ngày SAU `as_of`, quy UTC) và CHƯA
    KẾT THÚC tính tới lúc đó (`finished_at` rỗng, hoặc kết thúc TỪ `cutoff` trở về sau)."""
    def snap(as_of: date) -> dict:
        cond = _visibility_cond(db, user, profile, allowed)
        cutoff = datetime.combine(as_of + timedelta(days=1), time.min) - VN_OFFSET
        still_open = or_(ApprovalInstance.finished_at.is_(None), ApprovalInstance.finished_at >= cutoff)
        pending = db.query(ApprovalInstance).filter(cond, ApprovalInstance.started_at < cutoff, still_open).count()
        return {"pending": pending}
    return snap

def build_summary(db: Session, user, profile, period: Period, group_by: str | None) -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/approvals/summary` (+ `/export`).

    `group_by` approver/node_name KHÔNG truyền cho `build_report`: GOM Ở SQL theo chiều đó sẽ
    fan Tổng/Xu hướng theo số người duyệt/bước (sai, đếm dôi) — xem docstring đầu
    `report_fan_groups.py`. Tổng/Xu hướng ở đây luôn tính KHÔNG fan, `groups`/breakdown của hai
    chiều đó ghép tay bên dưới (cùng khuôn `work/report_service.compute_work_summary` xử lý PIC).

    `fan_sums(...)` của kỳ HIỆN TẠI gọi ĐÚNG MỘT LẦN mỗi chiều (dù vừa cần cho `breakdowns` vừa
    có thể cần cho `groups`) — gọi lặp lại tính LẠI chuỗi cửa sổ `LAG() OVER` của
    `report_step_metrics.step_metrics_subquery`, tốn thêm ~1-1.7s/lượt ở quy mô bench (review
    hiệu năng vòng 2, phát hiện qua benchmark trước khi vá). Kỳ SO SÁNH của `fan_sums` chỉ tính
    khi THỰC SỰ cần (đang "Xem theo" đúng chiều fan đó), không tính thừa cho chiều không active.
    """
    allowed = allowed_source_entities(db, user)
    cond = _visibility_cond(db, user, profile, allowed)
    spec = build_spec()
    sql_group_by = None if group_by in FAN_DIMENSIONS else group_by
    has_cmp = period.compare != "none" and period.compare_from and period.compare_to

    def fetch(d_from, d_to):
        return report_grouped_fetch.grouped_fetch_rows(db, cond, d_from, d_to)

    data = build_report(fetch, spec, period, group_by=sql_group_by,
                        snapshot=make_snapshot(db, user, profile, allowed, period))
    fan_current = {dim: report_fan_groups.fan_sums(db, cond, period.date_from, period.date_to, builder)
                  for dim, builder in FAN_DIMENSIONS.items()}
    if group_by in FAN_DIMENSIONS:
        fan_compare = (report_fan_groups.fan_sums(db, cond, period.compare_from, period.compare_to,
                                                  FAN_DIMENSIONS[group_by]) if has_cmp else None)
        data["meta"]["group_by"] = group_by
        data["groups"] = report_fan_groups.format_groups(fan_current[group_by], fan_compare, spec)
    for dim_name in FAN_DIMENSIONS:
        data["breakdowns"][dim_name] = report_fan_groups.format_breakdown(fan_current[dim_name], spec)
    missing = [e for e in APPROVAL_REPORT_SOURCES if e not in allowed]
    if missing:
        labels = ", ".join(ENTITY_LABELS.get(e, e) for e in missing)
        data["notes"] = data.get("notes", []) + [f"Không có quyền đọc nên KHÔNG tính: {labels}."]
    return data
