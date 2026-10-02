"""Khối SQL cấp TASK dùng chung cho `report_grouped_fetch.py` + `report_fan_groups.py` — phần
"gom bước cuối" của báo cáo Phê duyệt (review hiệu năng "gói B", 01/10/2026, vòng 2: đạt < 2s /
< 50MB ở quy mô bench bằng cách KHÔNG trả mỗi PHIÊN một hàng lên Python nữa — xem
`report_grouped_fetch.py` cho tầng gom cuối theo ngày/chiều).

Mọi hàm ở đây trả **subquery CHƯA THỰC THI** (không `.all()`) để tầng gọi tự JOIN/GROUP BY tiếp
— khác vòng 1 (đã xóa) từng thực thi rồi trả `dict[instance_id, ...]` cho Python lặp qua.

  · `step_metrics_subquery`: giờ mỗi BƯỚC (song song đo từ lúc MỞ bước, KHÔNG từ nhau — M6) +
    quá hạn/có hạn, gom theo PHIÊN bằng `LAG()/MAX() OVER` (cửa sổ) — y hệt vòng 1, chỉ đổi từ
    thực thi ngay sang trả subquery. SUM ở SQL có thể lệch BIT CUỐI dấu phẩy động so với cộng
    tuần tự của Python cũ — chấp nhận, xem bài kiểm tương đương dùng dung sai nhỏ.
  · `approver_pairs_subquery`/`node_name_pairs_subquery`: cặp (phiên, giá trị chiều) PHÂN BIỆT —
    một phiên nhiều bước/người góp NHIỀU khóa khi gom nhóm (thiết kế CŨ, không phải lỗi mới).
    KHÔNG resolve nhãn "không có tên → hiện id" ở đây nữa (vòng 1 JOIN tên ngay) — để tầng gọi
    tự `MAX(label)` sau GROUP BY rồi fallback `str(value)` trong Python, vì SQL `CAST(... AS
    VARCHAR)` không portable giữa SQLite/MySQL (MySQL chỉ nhận CHAR/SIGNED/... trong `CAST`).

`id_subq` truyền vào PHẢI là subquery `SELECT id FROM tab_approval_instance WHERE <đã lọc
phạm vi + kỳ>` (không phải list id Python) — tránh câu `IN (...)` hàng trăm nghìn tham số (chậm
trên MySQL, và SQLite có trần số biến bind ~32.766 — xem `report_turnaround.py` cùng lý do).
"""
from __future__ import annotations

from sqlalchemy import and_, case, func, select, text
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee

from .instance_model import (ApprovalInstance, ApprovalTask, TASK_CANCELLED,
                             TASK_SKIPPED_DUPLICATE)

REAL_STATUS = ApprovalTask.status.notin_((TASK_SKIPPED_DUPLICATE, TASK_CANCELLED))


def dialect_name(db: Session) -> str:
    bind = db.get_bind()
    return bind.dialect.name if bind is not None else "sqlite"


def hours_diff(dialect: str, end_col, start_col):
    """`end - start` tính bằng GIỜ, CHƯA cắt âm — cổng SQLite (`julianday`, đơn vị NGÀY, nhân
    24) / MySQL 8 (`TIMESTAMPDIFF(SECOND,...)`, chia 3600 — cùng độ chính xác GIÂY với
    `.total_seconds()` của Python)."""
    if dialect == "mysql":
        return func.timestampdiff(text("SECOND"), start_col, end_col) / 3600.0
    return (func.julianday(end_col) - func.julianday(start_col)) * 24.0


def clip_non_negative(dialect: str, expr):
    """`max(x, 0)` kiểu VÔ HƯỚNG (2 đối số) — SQLite dùng `max()` đa đối số sẵn có, MySQL
    KHÔNG hỗ trợ kiểu đó (`MAX()` của MySQL chỉ là hàm TỔNG HỢP 1 đối số) nên phải đổi sang
    `GREATEST()`."""
    fn = func.greatest if dialect == "mysql" else func.max
    return fn(expr, 0.0)


def step_metrics_subquery(db: Session, id_subq):
    """Subquery (KHÔNG thực thi) — 1 hàng/phiên: `instance_id, step_hours_sum, step_hours_count,
    due_known, overdue`. Phiên không có bước ĐÃ QUYẾT ĐỊNH nào thì VẮNG MẶT khỏi kết quả (tầng
    gọi tự `LEFT JOIN` + `COALESCE(...,0)`)."""
    dialect = dialect_name(db)
    decided = ApprovalTask.decided_at.isnot(None)
    in_scope = ApprovalTask.instance_id.in_(select(id_subq.c.id))

    #  B1: giờ ĐÓNG của mỗi BƯỚC (node_seq) — muộn nhất trong các task THẬT đã quyết của bước đó.
    group_close = (select(ApprovalTask.instance_id.label("instance_id"),
                          ApprovalTask.node_seq.label("node_seq"),
                          func.max(ApprovalTask.decided_at).label("seq_close"))
                  .where(in_scope, REAL_STATUS, decided)
                  .group_by(ApprovalTask.instance_id, ApprovalTask.node_seq)
                  .subquery("gc"))

    #  B2: giờ MỞ của mỗi bước = giờ ĐÓNG của bước liền trước TRONG DANH SÁCH BƯỚC CÓ QUYẾT ĐỊNH,
    #  bước ĐẦU TIÊN mở lúc phiên bắt đầu.
    prev_close = func.coalesce(
        func.lag(group_close.c.seq_close).over(partition_by=group_close.c.instance_id,
                                               order_by=group_close.c.node_seq),
        ApprovalInstance.started_at).label("prev_close")
    group_prev = (select(group_close.c.instance_id.label("instance_id"),
                        group_close.c.node_seq.label("node_seq"), prev_close)
                 .join(ApprovalInstance, ApprovalInstance.id == group_close.c.instance_id)
                 .subquery("gp"))

    #  B3: mỗi task THẬT đã quyết nối với giờ MỞ của bước nó — giờ bước = quyết − mở, cắt về 0.
    step_hours = case((group_prev.c.prev_close.isnot(None),
                       clip_non_negative(dialect, hours_diff(dialect, ApprovalTask.decided_at,
                                                             group_prev.c.prev_close))),
                      else_=None).label("step_hours")
    task_step = (select(ApprovalTask.instance_id.label("instance_id"), step_hours,
                       ApprovalTask.due_at.label("due_at"),
                       ApprovalTask.decided_at.label("decided_at"))
                .join(group_prev, and_(group_prev.c.instance_id == ApprovalTask.instance_id,
                                       group_prev.c.node_seq == ApprovalTask.node_seq))
                .where(in_scope, REAL_STATUS, decided)
                .subquery("ts"))

    #  B4: cộng theo PHIÊN — quá hạn/có hạn đếm trên MỌI task thật đã quyết, KHÔNG phụ thuộc
    #  `step_hours` có tính được hay không (bước đầu của phiên thiếu `started_at`, hiếm).
    return (select(task_step.c.instance_id.label("instance_id"),
                  func.sum(func.coalesce(task_step.c.step_hours, 0.0)).label("step_hours_sum"),
                  func.sum(case((task_step.c.step_hours.isnot(None), 1), else_=0))
                      .label("step_hours_count"),
                  func.sum(case((task_step.c.due_at.isnot(None), 1), else_=0)).label("due_known"),
                  func.sum(case((and_(task_step.c.due_at.isnot(None),
                                     task_step.c.decided_at > task_step.c.due_at), 1), else_=0))
                      .label("overdue"))
           .group_by(task_step.c.instance_id)
           .subquery("step_metrics"))


def approver_pairs_subquery(id_subq):
    """Subquery (KHÔNG thực thi) — `instance_id, value=employee_id, label=tên` PHÂN BIỆT, của
    các task THẬT (bỏ tự-qua-vì-trùng/đã-hủy, M6). `label` NULL nếu không tra được tên — tầng
    gọi tự fallback `str(value)` (khớp bản cũ `names.get(e_id, str(e_id))`)."""
    return (select(ApprovalTask.instance_id.label("instance_id"),
                  ApprovalTask.assignee_employee_id.label("value"),
                  Employee.full_name.label("label"))
           .outerjoin(Employee, Employee.id == ApprovalTask.assignee_employee_id)
           .where(ApprovalTask.instance_id.in_(select(id_subq.c.id)), REAL_STATUS,
                  ApprovalTask.assignee_employee_id != 0)
           .distinct()
           .subquery("approver_pairs"))


def node_name_pairs_subquery(id_subq):
    """Subquery (KHÔNG thực thi) — `instance_id, value=tên bước, label=tên bước` PHÂN BIỆT, của
    MỌI task (kể cả tự-qua/đã-hủy — khác `approver_pairs_subquery`: bản cũ dùng biến `tasks`
    chứ không phải `real` cho chiều này)."""
    return (select(ApprovalTask.instance_id.label("instance_id"),
                  ApprovalTask.node_name.label("value"), ApprovalTask.node_name.label("label"))
           .where(ApprovalTask.instance_id.in_(select(id_subq.c.id)), ApprovalTask.node_name != "")
           .distinct()
           .subquery("node_name_pairs"))
