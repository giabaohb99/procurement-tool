"""Các truy vấn «tải đang ôm» — mỗi hàm MỘT câu `GROUP BY người` có lọc `IN (nhân sự trong phạm vi)` (duoc-CR-656, D1c).

Không hàm nào lặp theo người. Hằng trạng thái lấy từ chính module sở hữu bảng (không gõ tay chuỗi).
Chỉ ĐỌC; không gác quyền (xem `workload_service.current_load`).
"""
from datetime import date, datetime

from sqlalchemy import and_, case, distinct, func, or_, select
from sqlalchemy.orm import Session

from app.core.base_model import Base
from app.modules.approval.instance_model import INSTANCE_OPEN_STATUSES, TASK_PENDING
from app.modules.document.model import STATUS_PENDING_ISSUE
from app.modules.leave.constants import LR_APPROVED
from app.modules.work.model import WorkAssigneeKind, WorkTaskStatus

#  Trạng thái chứng từ Thu mua KHÔNG còn là «đang xử lý» (mã chuỗi, xem `core/status_codes.py` và các service).
PR_NOT_HANDLING = ("draft", "submitted", "completed", "done", "cancelled", "rejected")
#  `received` (Đã nhận đủ) = đã xong, không còn «đang xử lý» (đại ca chốt 20/10/2026).
PO_NOT_HANDLING = ("draft", "received", "completed", "cancelled", "rejected")
SR_ACTIVE = ("submitted", "approved", "processing")
PR_LINE_DONE = ("completed", "cancelled")


def _t(name: str):
    return Base.metadata.tables[name]


def employees_in_scope(db: Session, company_id, department_ids, employee_ids) -> list:
    """Q1 — nhân sự đang làm trong phạm vi (đã loại «Nghỉ việc»). Phải có ÍT NHẤT một điều kiện lọc."""
    e = _t("tab_employee")
    q = select(e.c.id, e.c.code, e.c.full_name, e.c.company_id, e.c.department_id).where(e.c.status != "resigned")
    if company_id:
        q = q.where(e.c.company_id == company_id)
    if department_ids:
        q = q.where(e.c.department_id.in_(list(department_ids)))
    if employee_ids:
        q = q.where(e.c.id.in_(list(employee_ids)))
    return list(db.execute(q.order_by(e.c.id)).all())


def delegations_today(db: Session, emp_ids: list[int], today: date) -> list:
    """Q3 — ủy quyền còn hiệu lực hôm nay mà một đầu thuộc phạm vi: `(from, to, entity)`."""
    d = _t("tab_delegation")
    q = select(d.c.from_employee_id, d.c.to_employee_id, d.c.entity).where(
        d.c.is_active.is_(True), d.c.from_date <= today, d.c.to_date >= today,
        or_(d.c.from_employee_id.in_(emp_ids), d.c.to_employee_id.in_(emp_ids)))
    return list(db.execute(q).all())


def approvals_by_assignee(db: Session, assignee_ids: list[int], now: datetime) -> dict[tuple[int, str], tuple[int, int]]:
    """Q2 — `{(người được giao, loại chứng từ): (đang chờ, quá hạn)}`. Chỉ phiên duyệt còn MỞ (như `my_tasks`)."""
    t, i = _t("tab_approval_task"), _t("tab_approval_instance")
    overdue = func.sum(case((and_(t.c.due_at.isnot(None), t.c.due_at < now), 1), else_=0))
    q = (select(t.c.assignee_employee_id, i.c.entity, func.count(t.c.id), overdue)
         .join(i, i.c.id == t.c.instance_id)
         .where(t.c.assignee_employee_id.in_(assignee_ids), t.c.status == TASK_PENDING,
                i.c.status.in_(INSTANCE_OPEN_STATUSES))
         .group_by(t.c.assignee_employee_id, i.c.entity))
    return {(a, ent): (int(n), int(o or 0)) for a, ent, n, o in db.execute(q)}


def work_by_pic(db: Session, emp_ids: list[int], today_iso: str) -> dict[int, tuple[int, int, float]]:
    """Q4 — `{người: (việc dự án đang mở, quá hạn, Σ giờ ước lượng)}`; bỏ việc đã xóa mềm."""
    a, w = _t("tab_work_task_assignee"), _t("tab_work_task")
    overdue = func.sum(case((and_(w.c.due_date != "", w.c.due_date < today_iso), 1), else_=0))
    q = (select(a.c.employee_id, func.count(w.c.id), overdue, func.coalesce(func.sum(w.c.estimate_hours), 0))
         .join(w, w.c.id == a.c.task_id)
         .where(a.c.employee_id.in_(emp_ids), a.c.kind == int(WorkAssigneeKind.PIC),
                w.c.status == int(WorkTaskStatus.OPEN), w.c.deleted_at.is_(None))
         .group_by(a.c.employee_id))
    return {e: (int(n), int(o or 0), float(h or 0)) for e, n, o, h in db.execute(q)}


def pr_handling_by_code(db: Session, codes: list[str]) -> dict[str, int]:
    """Q5 — `{mã NV: số YCMH đang xử lý}` theo người phụ trách TỪNG DÒNG hàng.

    Không dùng `tab_purchase_request.assignee_id`: cột này gần như luôn 0, người phụ trách thật nằm ở dòng.
    """
    it, pr = _t("tab_purchase_request_item"), _t("tab_purchase_request")
    q = (select(it.c.assignee, func.count(distinct(pr.c.id)))
         .join(pr, pr.c.id == it.c.pr_id)
         .where(it.c.assignee.in_(codes), pr.c.is_deleted.is_(False), pr.c.status.notin_(PR_NOT_HANDLING),
                it.c.line_status.notin_(PR_LINE_DONE))
         .group_by(it.c.assignee))
    return {c: int(n) for c, n in db.execute(q)}


def pr_approval_pending(db: Session, emp_ids: list[int]) -> dict[int, int]:
    """Q6 — YCMH chờ trưởng phòng duyệt, tính cho `head_of_dept_id` (ĐẠI DIỆN: bộ máy duyệt Thu mua không gán người)."""
    pr = _t("tab_purchase_request")
    q = (select(pr.c.head_of_dept_id, func.count(pr.c.id))
         .where(pr.c.head_of_dept_id.in_(emp_ids), pr.c.status == "submitted", pr.c.is_deleted.is_(False))
         .group_by(pr.c.head_of_dept_id))
    return {e: int(n) for e, n in db.execute(q)}


def po_handling(db: Session, emp_ids: list[int]) -> dict[int, int]:
    """Q7 — ĐMH đang xử lý theo `nspt_id` (người phụ trách); đã nhận đủ / hoàn thành thì không tính."""
    po = _t("tab_purchase_order")
    q = (select(po.c.nspt_id, func.count(po.c.id))
         .where(po.c.nspt_id.in_(emp_ids), po.c.is_deleted.is_(False), po.c.status.notin_(PO_NOT_HANDLING))
         .group_by(po.c.nspt_id))
    return {e: int(n) for e, n in db.execute(q)}


def survey_lines_handling(db: Session, codes: list[str]) -> dict[str, int]:
    """Q8 — `{mã NV: số dòng YCBG đang giữ}` — dòng chưa hoàn thành, chưa tạo YCMH, phiếu cha còn chạy."""
    ln, sr = _t("tab_survey_request_line"), _t("tab_survey_request")
    q = (select(ln.c.assignee, func.count(ln.c.id))
         .join(sr, sr.c.id == ln.c.survey_request_id)
         .where(ln.c.assignee.in_(codes), ln.c.line_status != "completed", ln.c.pr_code == "",
                sr.c.is_deleted.is_(False), sr.c.status.in_(SR_ACTIVE))
         .group_by(ln.c.assignee))
    return {c: int(n) for c, n in db.execute(q)}


def docs_pending_issue(db: Session, emp_ids: list[int]) -> dict[int, int]:
    """Q9 — văn bản đã ký đủ, chờ NGƯỜI SOẠN THẢO bấm ban hành (`can_issue` so `drafter_employee_id`)."""
    d = _t("tab_document")
    q = (select(d.c.drafter_employee_id, func.count(d.c.id))
         .where(d.c.drafter_employee_id.in_(emp_ids), d.c.status == STATUS_PENDING_ISSUE, d.c.is_deleted.is_(False))
         .group_by(d.c.drafter_employee_id))
    return {e: int(n) for e, n in db.execute(q)}


def leaves_in_window(db: Session, emp_ids: list[int], start: date, end: date) -> list:
    """Q10 — đơn nghỉ ĐÃ DUYỆT giao khoảng `[start, end]`: `(employee_id, from_date, to_date)`."""
    lv = _t("tab_leave_request")
    q = select(lv.c.employee_id, lv.c.from_date, lv.c.to_date).where(
        lv.c.employee_id.in_(emp_ids), lv.c.status == LR_APPROVED, lv.c.is_deleted.is_(False),
        lv.c.from_date <= end, lv.c.to_date >= start)
    return list(db.execute(q).all())
