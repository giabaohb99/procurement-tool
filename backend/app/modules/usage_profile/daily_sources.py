"""ĐÚNG các truy vấn đọc của MỘT ngày, cho tất cả người dùng một lượt (duoc-CR-641, phase 02).

Số truy vấn KHÔNG phụ thuộc số người / số dòng. Chỉ `select(cột)`, lọc trong SQL, không ORM object đầy đủ.
Chỉ đọc: `route`, `method`, `http_status`, `session_id`, `referer`, `ip` của request_log — KHÔNG đọc
`query_string`, `request_body`, `response_body`.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from types import SimpleNamespace

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.logging_codes import ACTOR_KIND_USER, SOURCE_API
from app.modules.approval.instance_model import ApprovalAction
from app.modules.audit.model import AuditLog
from app.modules.employee.model import Employee
from app.modules.export_log.model import ExportLog
from app.modules.leave.constants import LR_APPROVED
from app.modules.leave.holiday_calendar import holiday_names_many
from app.modules.leave.period_spans import span_of
from app.modules.leave.request_model import LeaveRequest, LeaveRequestPeriod
from app.modules.login_session.model import LoginSession
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.request_log.model import RequestLog
from app.modules.seal_request.model import SealRequest
from app.modules.user.model import User
from app.modules.work_schedule.resolver_many import load_day_plans_many

from .daily_window import vn_day_bounds
from .model import UiEvent

PRIOR_LOGIN_DAYS = 90


@dataclass
class DaySources:
    day: date
    users: list = field(default_factory=list)          # (user_id, is_active, employee_id, company_id, department_id, emp_status, resign_date)
    requests: list = field(default_factory=list)       # (user_id, created_at, method, http_status, session_id, route, referer, ip)
    sessions: dict = field(default_factory=dict)       # session_id -> (user_id, ip, device_type, os, browser, created_at)
    prior_logins: list = field(default_factory=list)   # (user_id, ip, device_type, os, browser)
    audits: list = field(default_factory=list)         # (user_id, entity, action, action_group, session_id, created_at)
    exports: list = field(default_factory=list)        # (user_id, row_count)
    ui_events: list = field(default_factory=list)      # (user_id, occurred_at, event_type, route, form_key, duration_ms, result_count)
    plans: object = None
    holidays: dict = field(default_factory=dict)       # company_id -> {date: name}
    leaves: dict = field(default_factory=dict)         # employee_id -> [LeaveSpan]
    proxy_docs: list = field(default_factory=list)     # (created_by_user_id, requester_employee_id)
    approval_proxies: list = field(default_factory=list)   # (actor_employee_id, on_behalf_of_employee_id)


def load_day_sources(db: Session, day: date) -> DaySources:
    lo, hi = vn_day_bounds(day)
    src = DaySources(day=day)

    # Q7 người dùng + hồ sơ nhân sự
    src.users = [tuple(r) for r in db.execute(
        select(User.id, User.is_active, User.employee_id, Employee.company_id, Employee.department_id,
               Employee.status, Employee.resign_date)
        .select_from(User).outerjoin(Employee, Employee.id == User.employee_id)).all()]

    # Q1 request_log (chỉ API của người đã đăng nhập)
    src.requests = [tuple(r) for r in db.execute(
        select(RequestLog.user_id, RequestLog.created_at, RequestLog.method, RequestLog.http_status,
               RequestLog.session_id, RequestLog.route, RequestLog.referer, RequestLog.ip)
        .where(RequestLog.created_at >= lo, RequestLog.created_at < hi,
               RequestLog.user_id > 0, RequestLog.source == SOURCE_API)).all()]

    # Q4 audit do NGƯỜI làm (không tính việc hệ thống tự ghi)
    src.audits = [tuple(r) for r in db.execute(
        select(AuditLog.created_by, AuditLog.entity, AuditLog.action, AuditLog.action_group,
               AuditLog.session_id, AuditLog.created_at)
        .where(AuditLog.created_at >= lo, AuditLog.created_at < hi,
               AuditLog.actor_kind == ACTOR_KIND_USER, AuditLog.created_by > 0)).all()]

    # Q5 xuất dữ liệu
    src.exports = [tuple(r) for r in db.execute(
        select(ExportLog.created_by, ExportLog.row_count)
        .where(ExportLog.created_at >= lo, ExportLog.created_at < hi, ExportLog.created_by > 0)).all()]

    # Q6 sự kiện giao diện (theo occurred_at)
    src.ui_events = [tuple(r) for r in db.execute(
        select(UiEvent.user_id, UiEvent.occurred_at, UiEvent.event_type, UiEvent.route_pattern,
               UiEvent.form_key, UiEvent.duration_ms, UiEvent.result_count)
        .where(UiEvent.occurred_at >= lo, UiEvent.occurred_at < hi)).all()]

    # Q2 phiên: tạo trong ngày + phiên mà request/audit của ngày tham chiếu tới
    ref_ids = {r[4] for r in src.requests if r[4]} | {a[4] for a in src.audits if a[4]}
    cond = and_(LoginSession.created_at >= lo, LoginSession.created_at < hi)
    if ref_ids:
        cond = or_(cond, LoginSession.id.in_(ref_ids))
    for sid, uid, ip, dev, os_, browser, created in db.execute(
            select(LoginSession.id, LoginSession.user_id, LoginSession.ip, LoginSession.device_type,
                   LoginSession.os, LoginSession.browser, LoginSession.created_at).where(cond)).all():
        src.sessions[sid] = (uid, ip, dev, os_, browser, created)

    # Q3 chữ ký đăng nhập 90 ngày trước ngày D của những người có đăng nhập trong D
    login_users = {s[0] for s in src.sessions.values() if lo <= s[5] < hi}
    if login_users:
        src.prior_logins = [tuple(r) for r in db.execute(
            select(LoginSession.user_id, LoginSession.ip, LoginSession.device_type, LoginSession.os,
                   LoginSession.browser)
            .where(LoginSession.user_id.in_(login_users),
                   LoginSession.created_at >= lo - timedelta(days=PRIOR_LOGIN_DAYS),
                   LoginSession.created_at < lo)).all()]

    # Q8–10 lịch làm việc, Q11 ngày lễ
    emps = [SimpleNamespace(id=u[2], company_id=u[3] or 0, department_id=u[4] or 0)
            for u in src.users if u[2]]
    src.plans = load_day_plans_many(db, emps, day, day)
    src.holidays = holiday_names_many(db, {e.company_id for e in emps} | {0}, day, day)

    # Q12 đơn nghỉ ĐÃ DUYỆT chồng ngày D
    emp_ids = {e.id for e in emps}
    leaves: dict = defaultdict(list)
    if emp_ids:
        P = LeaveRequestPeriod
        # OUTER JOIN khoảng: ngày D nằm trong KHE giữa hai khoảng thì không phải ngày nghỉ.
        for req, period in db.execute(
                select(LeaveRequest, P).outerjoin(P, P.request_id == LeaveRequest.id).where(
                    LeaveRequest.employee_id.in_(emp_ids), LeaveRequest.status == LR_APPROVED,
                    LeaveRequest.is_deleted.is_(False), LeaveRequest.from_date <= day,
                    LeaveRequest.to_date >= day,
                    or_(P.id.is_(None), and_(P.from_date <= day, P.to_date >= day)))).all():
            leaves[req.employee_id].append(span_of(req, period))
    src.leaves = dict(leaves)

    # Q13 bấm hộ: phiếu tạo trong D mà người đề nghị ≠ người tạo (cột thứ hai LUÔN là id NHÂN SỰ của người đề nghị)
    for created_by, requester in (
            *db.execute(select(LeaveRequest.created_by, LeaveRequest.employee_id)
                        .where(LeaveRequest.created_at >= lo, LeaveRequest.created_at < hi)).all(),
            *db.execute(select(PurchaseRequest.created_by, PurchaseRequest.requester_id)
                        .where(PurchaseRequest.created_at >= lo, PurchaseRequest.created_at < hi)).all(),
            #  Bug H1 (CR-641 review): `SealRequest.requester_id` là ID TÀI KHOẢN (seal_request/service.py), không phải id
            #  nhân sự như `LeaveRequest.employee_id` / `PurchaseRequest.requester_id` — phải quy ra nhân sự trước khi so.
            *db.execute(select(SealRequest.created_by, User.employee_id)
                        .join(User, User.id == SealRequest.requester_id)
                        .where(SealRequest.created_at >= lo, SealRequest.created_at < hi)).all()):
        src.proxy_docs.append((created_by, requester))

    # Q14 duyệt thay theo ủy quyền
    src.approval_proxies = [tuple(r) for r in db.execute(
        select(ApprovalAction.actor_employee_id, ApprovalAction.on_behalf_of_id)
        .where(ApprovalAction.created_at >= lo, ApprovalAction.created_at < hi,
               ApprovalAction.on_behalf_of_id.is_not(None), ApprovalAction.on_behalf_of_id > 0)).all()]
    return src
