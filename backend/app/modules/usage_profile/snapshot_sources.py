"""Truy vấn CỐ ĐỊNH (không phụ thuộc số người) cho snapshot tuần của cả công ty (duoc-CR-641, phase 04).

Cửa sổ W = 4 tuần kết thúc Chủ nhật của tuần `week_start`. Chỉ `select(cột)`; không đọc nội dung bình luận,
tin nhắn trợ lý, tiêu đề phiếu — chỉ đếm / lấy mốc thời gian.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased
from sqlalchemy import and_, or_

from app.core.logging_codes import ACTION_GROUP_APPROVE, ACTOR_KIND_USER
from app.core.usage_codes import PeriodKind, UiEventType
from app.modules.approval.instance_model import (TASK_APPROVED, TASK_PENDING, TASK_REJECTED, ApprovalInstance,
                                                  ApprovalTask)
from app.modules.assistant.change_model import AssistantChange
from app.modules.assistant.model import AssistantMessage, MessageRole
from app.modules.audit.model import AuditLog
from app.modules.comment.model import Comment, CommentMention
from app.modules.employee.model import Employee
from app.modules.export_log.model import ExportLog
from app.modules.import_tool.model import ImportBatch
from app.modules.notification.model import Notification
from app.modules.role.model import Role
from app.modules.ticket.model import Ticket
from app.modules.user.model import User, UserRole
from app.modules.user_preference.model import UserPreference
from app.modules.work.model import WorkTaskStatus
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

from .daily_docs import APPROVAL_DECISION_ACTIONS, TRACKED_DOC_ENTITIES
from .daily_window import vn_day_bounds
from .model import UiEvent, UsageDaily, UserUsageSnapshot
from .snapshot_sources_ai import AiSources, load_ai_sources

WINDOW_WEEKS = 4
HISTORY_WEEKS = 12      # export_rows_spike so với 12 tuần trước
MONTH_WINDOW_DAYS = 91  # month_end_create_share
SUBMIT_ACTIONS = ("submit", "submitted")


@dataclass
class Window:
    week_start: date   # thứ Hai của tuần cuối cửa sổ
    lo: date = field(init=False)   # ngày VN đầu tiên của W
    hi: date = field(init=False)   # ngày VN SAU ngày cuối của W (loại trừ)
    utc_lo: datetime = field(init=False)
    utc_hi: datetime = field(init=False)

    def __post_init__(self):
        self.lo = self.week_start - timedelta(weeks=WINDOW_WEEKS - 1)
        self.hi = self.week_start + timedelta(days=7)
        self.utc_lo = vn_day_bounds(self.lo)[0]
        self.utc_hi = vn_day_bounds(self.hi)[0]


@dataclass
class SnapshotSources:
    window: Window
    users: list = field(default_factory=list)       # (user_id, is_active, employee_id, company_id, hire_date)
    user_roles: list = field(default_factory=list)  # (user_id, role_id)
    roles: dict = field(default_factory=dict)       # role_id -> (code, name)
    daily: list = field(default_factory=list)       # Row UsageDaily trong W
    daily_old: list = field(default_factory=list)   # (user_id, day, export_rows, docs) trước W
    tracking_since: date | None = None
    chain_audits: list = field(default_factory=list)   # (id, entity, entity_id, action, created_by, created_at)
    decisions: list = field(default_factory=list)   # (created_by, created_at)
    tasks: list = field(default_factory=list)       # (id, instance_id, node_seq, order_no, assignee_emp, status, created_at, decided_at)
    siblings: list = field(default_factory=list)    # (instance_id, node_seq, order_no, decided_at)
    instances: list = field(default_factory=list)   # (instance_id, flow_snapshot) của các phiếu có việc xong trong W
    notifications: list = field(default_factory=list)   # (user_id, is_read, created_at, read_at)
    mentions: list = field(default_factory=list)    # (mentioned_user, entity, entity_id, mentioned_at)
    replies: list = field(default_factory=list)     # (created_by, entity, entity_id, created_at)
    comments: dict = field(default_factory=dict)    # user_id -> n
    assistant_q: dict = field(default_factory=dict)
    assistant_chg: dict = field(default_factory=dict)
    prefs: dict = field(default_factory=dict)
    imports: dict = field(default_factory=dict)     # user_id -> (batches, total_rows, error_count)
    work_tasks: list = field(default_factory=list)  # (employee_id, due_date, completed_at, status)
    tickets: dict = field(default_factory=dict)     # employee_id -> n
    export_entities: list = field(default_factory=list)   # (user_id, entity, created_at)
    pageviews: list = field(default_factory=list)   # (user_id, session_id, tab_key, occurred_at, route)
    prev_snapshots: list = field(default_factory=list)    # (user_id, period_start, metrics)
    ai: AiSources = field(default_factory=AiSources)   # duoc-CR-655: nhóm 3.8 "Dùng AI"


def _counts(db: Session, col, *conds) -> dict:
    return {k: n for k, n in db.execute(select(col, func.count()).where(*conds).group_by(col)).all()}


def load_snapshot_sources(db: Session, week_start: date) -> SnapshotSources:
    w = Window(week_start)
    s = SnapshotSources(w)
    s.users = [tuple(r) for r in db.execute(
        select(User.id, User.is_active, User.employee_id, Employee.company_id, Employee.hire_date)
        .select_from(User).outerjoin(Employee, Employee.id == User.employee_id)).all()]
    s.user_roles = [tuple(r) for r in db.execute(select(UserRole.user_id, UserRole.role_id)).all()]
    s.roles = {r[0]: (r[1], r[2]) for r in db.execute(select(Role.id, Role.code, Role.name)).all()}

    s.daily = list(db.execute(select(UsageDaily).where(UsageDaily.day >= w.lo, UsageDaily.day < w.hi)).scalars())
    old_lo = w.lo - timedelta(days=max(HISTORY_WEEKS * 7, MONTH_WINDOW_DAYS))
    s.daily_old = [tuple(r) for r in db.execute(
        select(UsageDaily.user_id, UsageDaily.day, UsageDaily.export_rows, UsageDaily.docs)
        .where(UsageDaily.day >= old_lo, UsageDaily.day < w.lo)).all()]
    s.tracking_since = db.execute(select(func.min(UsageDaily.day)).where(UsageDaily.page_views > 0)).scalar()

    in_window = (AuditLog.created_at >= w.utc_lo, AuditLog.created_at < w.utc_hi)
    #  alias riêng cho truy vấn con: cùng bảng với truy vấn ngoài nên nếu không SQLAlchemy tự "tương quan" và làm rỗng FROM.
    sub = aliased(AuditLog)
    submitted_ids = select(sub.entity_id).where(
        sub.entity.in_(TRACKED_DOC_ENTITIES), sub.action.in_(SUBMIT_ACTIONS), sub.actor_kind == ACTOR_KIND_USER,
        sub.created_at >= w.utc_lo, sub.created_at < w.utc_hi)
    s.chain_audits = [tuple(r) for r in db.execute(
        select(AuditLog.id, AuditLog.entity, AuditLog.entity_id, AuditLog.action, AuditLog.created_by,
               AuditLog.created_at)
        .where(AuditLog.entity.in_(TRACKED_DOC_ENTITIES), AuditLog.entity_id.in_(submitted_ids),
               AuditLog.actor_kind == ACTOR_KIND_USER).order_by(AuditLog.id)).all()]
    s.decisions = [tuple(r) for r in db.execute(
        select(AuditLog.created_by, AuditLog.created_at)
        .where(AuditLog.action_group == ACTION_GROUP_APPROVE, AuditLog.action.in_(APPROVAL_DECISION_ACTIONS),
               AuditLog.actor_kind == ACTOR_KIND_USER, *in_window)).all()]

    done_cond = (ApprovalTask.status.in_((TASK_APPROVED, TASK_REJECTED)),
                 ApprovalTask.decided_at >= w.utc_lo, ApprovalTask.decided_at < w.utc_hi)
    task_cols = (ApprovalTask.id, ApprovalTask.instance_id, ApprovalTask.node_seq, ApprovalTask.order_no,
                 ApprovalTask.assignee_employee_id, ApprovalTask.status, ApprovalTask.created_at,
                 ApprovalTask.decided_at)
    done_sub = aliased(ApprovalTask)
    s.tasks = [tuple(r) for r in db.execute(
        select(*task_cols).where(or_(and_(*done_cond), ApprovalTask.status == TASK_PENDING))).all()]
    s.siblings = [tuple(r) for r in db.execute(
        select(ApprovalTask.instance_id, ApprovalTask.node_seq, ApprovalTask.order_no, ApprovalTask.decided_at)
        .where(ApprovalTask.instance_id.in_(select(done_sub.instance_id).where(
            done_sub.status.in_((TASK_APPROVED, TASK_REJECTED)), done_sub.decided_at >= w.utc_lo,
            done_sub.decided_at < w.utc_hi)), ApprovalTask.order_no > 0)).all()]

    s.instances = [tuple(r) for r in db.execute(
        select(ApprovalInstance.id, ApprovalInstance.flow_snapshot)
        .where(ApprovalInstance.id.in_(select(done_sub.instance_id).where(
            done_sub.status.in_((TASK_APPROVED, TASK_REJECTED)), done_sub.decided_at >= w.utc_lo,
            done_sub.decided_at < w.utc_hi)))).all()]
    s.notifications = [tuple(r) for r in db.execute(
        select(Notification.user_id, Notification.is_read, Notification.created_at, Notification.read_at)
        .where(Notification.created_at >= w.utc_lo, Notification.created_at < w.utc_hi)).all()]
    s.mentions = [tuple(r) for r in db.execute(
        select(CommentMention.user_id, Comment.entity, Comment.entity_id, CommentMention.created_at)
        .select_from(CommentMention).join(Comment, Comment.id == CommentMention.comment_id)
        .where(CommentMention.created_at >= w.utc_lo, CommentMention.created_at < w.utc_hi)).all()]
    s.replies = [tuple(r) for r in db.execute(
        select(Comment.created_by, Comment.entity, Comment.entity_id, Comment.created_at)
        .where(Comment.created_at >= w.utc_lo, Comment.created_at < w.utc_hi,
               Comment.created_by.in_(select(CommentMention.user_id).where(
                   CommentMention.created_at >= w.utc_lo, CommentMention.created_at < w.utc_hi)))).all()]
    s.comments = _counts(db, Comment.created_by, Comment.created_at >= w.utc_lo, Comment.created_at < w.utc_hi)
    s.assistant_q = _counts(db, AssistantMessage.created_by, AssistantMessage.role == int(MessageRole.USER),
                            AssistantMessage.created_at >= w.utc_lo, AssistantMessage.created_at < w.utc_hi)
    s.assistant_chg = _counts(db, AssistantChange.created_by, AssistantChange.created_at >= w.utc_lo,
                              AssistantChange.created_at < w.utc_hi)
    s.prefs = {k: n for k, n in db.execute(
        select(UserPreference.user_id, func.count()).group_by(UserPreference.user_id)).all()}
    s.imports = {r[0]: (r[1], r[2] or 0, r[3] or 0) for r in db.execute(
        select(ImportBatch.created_by, func.count(), func.sum(ImportBatch.total_rows),
               func.sum(ImportBatch.error_count))
        .where(ImportBatch.created_at >= w.utc_lo, ImportBatch.created_at < w.utc_hi)
        .group_by(ImportBatch.created_by)).all()}
    s.work_tasks = [tuple(r) for r in db.execute(
        select(WorkTaskAssignee.employee_id, WorkTask.due_date, WorkTask.completed_at, WorkTask.status)
        .select_from(WorkTaskAssignee).join(WorkTask, WorkTask.id == WorkTaskAssignee.task_id)
        .where(WorkTask.deleted_at.is_(None), WorkTask.due_date != "",
               ((WorkTask.status == int(WorkTaskStatus.DONE)) & (WorkTask.completed_at >= w.utc_lo)
                & (WorkTask.completed_at < w.utc_hi))
               | (WorkTask.status == int(WorkTaskStatus.OPEN)))).all()]
    s.tickets = _counts(db, Ticket.requester_id, Ticket.created_at >= w.utc_lo, Ticket.created_at < w.utc_hi)
    s.export_entities = [tuple(r) for r in db.execute(
        select(ExportLog.created_by, ExportLog.entity, ExportLog.created_at)
        .where(ExportLog.created_at >= w.utc_lo, ExportLog.created_at < w.utc_hi)).all()]

    last_week_lo = vn_day_bounds(w.week_start)[0]
    s.pageviews = [tuple(r) for r in db.execute(
        select(UiEvent.user_id, UiEvent.session_id, UiEvent.tab_key, UiEvent.occurred_at, UiEvent.route_pattern)
        .where(UiEvent.event_type == int(UiEventType.PAGE_VIEW), UiEvent.occurred_at >= last_week_lo,
               UiEvent.occurred_at < w.utc_hi).order_by(UiEvent.occurred_at)).all()]
    prev_starts = [w.week_start - timedelta(weeks=i) for i in (3, 2, 1)]
    s.prev_snapshots = [tuple(r) for r in db.execute(
        select(UserUsageSnapshot.user_id, UserUsageSnapshot.period_start, UserUsageSnapshot.metrics)
        .where(UserUsageSnapshot.period_kind == int(PeriodKind.WEEK),
               UserUsageSnapshot.period_start.in_(prev_starts))).all()]
    s.ai = load_ai_sources(db, w)
    return s
