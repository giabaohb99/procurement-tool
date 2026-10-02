"""Tầng gom CUỐI của báo cáo Phê duyệt — GROUP BY (ngày VN, loại chứng từ, trạng thái) ngay ở
SQL, trả về ĐÚNG số hàng cần cho `report_aggregate.build_report()` thay vì 1 hàng/PHIÊN như vòng
1 (review hiệu năng "gói B", 01/10/2026, vòng 2: 128k phiên → bench vẫn 2,9s/100MB vì MỖI PHIÊN
còn lên Python 1 lần; mục tiêu < 2s / < 50MB).

`entity` LUÔN có mặt trong khóa GROUP BY bất kể `group_by` người dùng chọn gì — rẻ (≤5 loại
chứng từ) và cần thiết vì `ReportSpec.breakdowns["entity"]` CHẠY VỚI MỌI `group_by` (framework
`aggregate()` tính breakdown cho MỌI chiều khai trong `spec.breakdowns`, không riêng chiều đang
"Xem theo"). `approver`/`node_name` KHÔNG qua đường này — hai chiều đó NHIỀU GIÁ TRỊ/phiên
(fan), gom ở `report_fan_groups.py` và KHÔNG được lẫn vào tập hàng này (lẫn vào sẽ làm Tổng/Xu
hướng đếm dôi theo số người duyệt/bước, xem docstring `report_fan_groups.py`).

Một "hàng" trả về đại diện N phiên đã GOM — `report_service.build_spec()` đọc `r["cnt"]` thay vì
hằng `1`, giống khuôn `work/report_grouped_fetch.py`.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.core.report_period import range_filter
from app.modules.work.report_sql_date import vn_date_str

from . import report_step_metrics as step
from .instance_model import ApprovalInstance, INSTANCE_APPROVED, INSTANCE_REJECTED


def scoped_instance_ids(cond, d_from: date, d_to: date):
    """Subquery (KHÔNG thực thi) — id phiên đã lọc PHẠM VI (`cond`) + KỲ. Dùng CHUNG cho cả
    `instance_metrics_subquery` (tệp này) lẫn `report_fan_groups.py` (cùng phạm vi, join khác
    bảng) — gọi lại hàm này ở mỗi nơi chỉ DỰNG lại câu SQL, không tốn thêm lượt hỏi CSDL nào."""
    return (select(ApprovalInstance.id)
           .where(cond, range_filter(ApprovalInstance.started_at, "datetime_utc", d_from, d_to))
           .subquery())


def instance_metrics_subquery(db: Session, cond, d_from: date, d_to: date):
    """Subquery (KHÔNG thực thi) — 1 hàng/phiên trong phạm vi+kỳ: `id, date (chuỗi ngày VN),
    entity, status, proc_hours_sum/count, step_hours_sum/count, step_overdue, step_due_known`.
    `LEFT JOIN` với `step.step_metrics_subquery` vì phiên không có bước đã quyết nào vẫn phải có
    mặt (góp `sessions` dù không góp giờ bước)."""
    id_subq = scoped_instance_ids(cond, d_from, d_to)
    step_sub = step.step_metrics_subquery(db, id_subq)
    dialect = step.dialect_name(db)
    day = vn_date_str(db, ApprovalInstance.started_at)
    proc_flag = and_(ApprovalInstance.status.in_((INSTANCE_APPROVED, INSTANCE_REJECTED)),
                     ApprovalInstance.finished_at.isnot(None))
    proc_hours = case((proc_flag, step.clip_non_negative(
        dialect, step.hours_diff(dialect, ApprovalInstance.finished_at, ApprovalInstance.started_at))),
        else_=0.0)
    return (select(ApprovalInstance.id.label("id"), day.label("date"),
                  ApprovalInstance.entity.label("entity"), ApprovalInstance.status.label("status"),
                  proc_hours.label("proc_hours_sum"), case((proc_flag, 1), else_=0).label("proc_hours_count"),
                  func.coalesce(step_sub.c.step_hours_sum, 0.0).label("step_hours_sum"),
                  func.coalesce(step_sub.c.step_hours_count, 0).label("step_hours_count"),
                  func.coalesce(step_sub.c.overdue, 0).label("step_overdue"),
                  func.coalesce(step_sub.c.due_known, 0).label("step_due_known"))
           .select_from(ApprovalInstance)
           .outerjoin(step_sub, step_sub.c.instance_id == ApprovalInstance.id)
           .where(ApprovalInstance.id.in_(select(id_subq.c.id)))
           .subquery("instance_metrics"))


def grouped_fetch_rows(db: Session, cond, d_from: date, d_to: date) -> list[dict]:
    """GOM Ở SQL theo (ngày VN, entity, status) — trả list dict cho `build_report()`. Số hàng bị
    chặn trên bởi SỐ NGÀY TRONG KỲ × ≤5 entity × ≤6 status, KHÔNG tăng theo số phiên (khác vòng 1,
    vốn trả đúng 1 hàng/phiên — 128k hàng ở quy mô bench)."""
    m = instance_metrics_subquery(db, cond, d_from, d_to)
    q = (select(m.c.date, m.c.entity, m.c.status, func.count().label("cnt"),
               func.sum(m.c.proc_hours_sum).label("proc_hours_sum"),
               func.sum(m.c.proc_hours_count).label("proc_hours_count"),
               func.sum(m.c.step_hours_sum).label("step_hours_sum"),
               func.sum(m.c.step_hours_count).label("step_hours_count"),
               func.sum(m.c.step_overdue).label("step_overdue"),
               func.sum(m.c.step_due_known).label("step_due_known"))
        .group_by(m.c.date, m.c.entity, m.c.status)
        .order_by(m.c.date, m.c.entity, m.c.status))
    return [{"date": date.fromisoformat(r.date), "entity": r.entity, "status": r.status,
            "cnt": int(r.cnt), "proc_hours_sum": float(r.proc_hours_sum or 0),
            "proc_hours_count": int(r.proc_hours_count or 0),
            "step_hours_sum": float(r.step_hours_sum or 0),
            "step_hours_count": int(r.step_hours_count or 0),
            "step_overdue": int(r.step_overdue or 0), "step_due_known": int(r.step_due_known or 0)}
           for r in db.execute(q).all()]
