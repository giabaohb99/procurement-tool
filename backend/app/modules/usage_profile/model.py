"""Bốn bảng của hồ sơ cách làm việc (duoc-CR-641). Cả bốn là bảng CHỈ-THÊM/ghi-lại-được, không dùng
`AuditMixin` (cùng tiền lệ `tab_request_log`): người ghi là hệ thống, `updated_by` là cột chết.

- `tab_ui_event`: sự kiện giao diện thô, GIỮ 90 NGÀY. Không có từ khóa tìm kiếm, không có id trong route,
  không có nội dung form. `user_id` lấy từ token, không bao giờ từ body.
- `tab_usage_daily`: một dòng/người/ngày — số gom từ nhật ký sẵn có + sự kiện giao diện. Giữ 3 NĂM.
- `tab_user_usage_snapshot`: ảnh chụp theo tuần (JSON chỉ chứa số + mã, schema v1, sẵn cho pha 4 AI).
- `tab_user_usage_label`: nhãn «kiểu làm việc» kèm bằng chứng.
"""
from datetime import date, datetime

from sqlalchemy import (JSON, BigInteger, Boolean, Date, DateTime, Float, Index, Integer, SmallInteger,
                        String, UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base


class UiEvent(Base):
    __tablename__ = "tab_ui_event"
    __table_args__ = (
        Index("ix_ui_event_occurred_at", "occurred_at"),
        Index("ix_ui_event_user_occurred", "user_id", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())  # server nhận (UTC)
    occurred_at: Mapped[datetime] = mapped_column(DateTime)   # created_at − clamp(age_ms)
    user_id: Mapped[int] = mapped_column(BigInteger)
    session_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tab_key: Mapped[int] = mapped_column(Integer, default=0)  # số ngẫu nhiên mỗi lần nạp trang
    event_type: Mapped[int] = mapped_column(SmallInteger)     # UiEventType
    route_pattern: Mapped[str] = mapped_column(String(120), default="")
    form_key: Mapped[int] = mapped_column(SmallInteger, default=0)   # UiForm, 0 = không phải form
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    result_count: Mapped[int | None] = mapped_column(Integer, nullable=True)   # chỉ SEARCH
    meta: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)  # chỉ CLIENT_ERROR


def _int(default: int = 0):
    return mapped_column(Integer, default=default)


def _small(default: int = 0):
    return mapped_column(SmallInteger, default=default)


class UsageDaily(Base):
    __tablename__ = "tab_usage_daily"
    __table_args__ = (
        UniqueConstraint("user_id", "day", name="uq_usage_daily_user_day"),
        Index("ix_usage_daily_day", "day"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    day: Mapped[date] = mapped_column(Date)   # ngày theo giờ VN
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    computed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # lịch
    is_workday: Mapped[bool] = mapped_column(Boolean, default=False)
    is_holiday: Mapped[bool] = mapped_column(Boolean, default=False)
    work_capacity: Mapped[float] = mapped_column(Float, default=0.0)
    leave_days: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    # nhịp
    first_seen_min: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    last_action_min: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    work_bursts: Mapped[int] = _small()
    active_minutes: Mapped[int] = _small()
    logins: Mapped[int] = _small()
    # API
    api_reads: Mapped[int] = _int()
    api_writes: Mapped[int] = _int()
    writes_offhours: Mapped[int] = _int()
    writes_mobile: Mapped[int] = _int()
    approvals: Mapped[int] = _int()
    approvals_mobile: Mapped[int] = _int()
    http_403: Mapped[int] = _int()
    http_422: Mapped[int] = _int()
    http_5xx: Mapped[int] = _int()
    # khác
    exports: Mapped[int] = _int()
    export_rows: Mapped[int] = _int()
    deletes: Mapped[int] = _int()
    max_deletes_10min: Mapped[int] = _small()
    new_ip_logins: Mapped[int] = _small()
    new_device_logins: Mapped[int] = _small()
    max_parallel_ips: Mapped[int] = _small()
    docs_created: Mapped[int] = _int()   # Σ lập mới (c) của mọi phiếu theo dõi — để danh sách cộng được bằng SQL
    on_behalf_received: Mapped[int] = _int()
    on_behalf_done: Mapped[int] = _int()
    active_after_resign: Mapped[bool] = mapped_column(Boolean, default=False)
    # UI (từ tab_ui_event) — NULL-able không cần: 0 và «chưa thu» phân biệt ở tầng snapshot (tracking_since)
    page_views: Mapped[int] = _int()
    dwell_ms: Mapped[int] = mapped_column(BigInteger, default=0)
    searches: Mapped[int] = _int()
    searches_empty: Mapped[int] = _int()
    client_errors: Mapped[int] = _int()
    first_route: Mapped[str] = mapped_column(String(120), default="")
    # JSON có trần (builder cắt, tổng ≤ 16 KB)
    hourly: Mapped[list | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    screens: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    docs: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    forms: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    reports: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    forbidden_routes: Mapped[dict | None] = mapped_column(JSON(none_as_null=True), nullable=True)


class UserUsageSnapshot(Base):
    __tablename__ = "tab_user_usage_snapshot"
    __table_args__ = (
        UniqueConstraint("user_id", "period_kind", "period_start", name="uq_usage_snapshot_user_period"),
        Index("ix_usage_snapshot_period", "period_kind", "period_start"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    period_kind: Mapped[int] = _small(1)    # PeriodKind
    period_start: Mapped[date] = mapped_column(Date)   # thứ Hai của tuần kết thúc cửa sổ
    window_weeks: Mapped[int] = _small(4)
    schema_version: Mapped[int] = _small(1)
    cohort_kind: Mapped[int] = _small(3)    # CohortKind
    cohort_key: Mapped[int] = mapped_column(BigInteger, default=0)
    cohort_size: Mapped[int] = _small()
    metrics: Mapped[dict] = mapped_column(JSON)
    computed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserUsageLabel(Base):
    __tablename__ = "tab_user_usage_label"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "label", name="uq_usage_label_snapshot_label"),
        Index("ix_usage_label_period_label", "period_start", "label"),
        Index("ix_usage_label_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(BigInteger)
    period_start: Mapped[date] = mapped_column(Date)
    label: Mapped[int] = mapped_column(SmallInteger)    # UsageStyle
    score: Mapped[float] = mapped_column(Float, default=0.0)
    evidence: Mapped[list | None] = mapped_column(JSON(none_as_null=True), nullable=True)
