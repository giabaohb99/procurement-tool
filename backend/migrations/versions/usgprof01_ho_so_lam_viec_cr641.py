"""ho_so_lam_viec: 4 bang tracking + cot tab_notification.read_at + 4 chi muc -- duoc-CR-641

Revision ID: usgprof01
Revises: mcplog02
Create Date: 2026-10-19

VIET TAY (autogenerate repo nay troi ~650 dong moi lan; khong import ma ung dung).
Da doi chieu voi `--autogenerate`: phan lech ngoai cac doi tuong duoi day la TROI SAN CO, da cat bo.

upgrade
  - `tab_ui_event`           su kien giao dien tho, giu 90 ngay (khong tu khoa tim kiem, khong id trong route).
  - `tab_usage_daily`        mot dong/nguoi/ngay, giu 3 nam. UNIQUE (user_id, day).
  - `tab_user_usage_snapshot` anh chup tuan (JSON chi chua so + ma, schema v1). UNIQUE (user, kind, start).
  - `tab_user_usage_label`   nhan «kieu lam viec» kem bang chung. UNIQUE (snapshot_id, label).
  - `tab_notification.read_at` DATETIME NULL (chi tu ngay deploy, khong bu).
  - 4 chi muc de gom ngay: tab_notification(created_at), tab_audit_log(created_at),
    tab_export_log(created_at), tab_approval_task(decided_at).
    ⚠️ `ADD INDEX` tren `tab_audit_log` (bang phan vung theo nam): InnoDB online DDL, khong khoa ghi;
    van nen chay ngoai gio cao diem.
downgrade: drop nguoc thu tu (4 chi muc -> cot -> 4 bang). Khong dung du lieu nghiep vu.
Moi buoc tu gac (inspect) nen chay lai sau su co (MySQL DDL tu commit) la an toan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "usgprof01"
down_revision: Union[str, None] = "mcplog02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  (bang, ten chi muc, cac cot) -- ten KHOP DUNG khai bao trong model.
_INDEXES = (
    ("tab_notification", "ix_tab_notification_created_at", ["created_at"]),
    ("tab_audit_log", "ix_tab_audit_log_created_at", ["created_at"]),
    ("tab_export_log", "ix_tab_export_log_created_at", ["created_at"]),
    ("tab_approval_task", "ix_approval_task_decided_at", ["decided_at"]),
)

#  Cot so nguyen cua tab_usage_daily: (ten, kieu).
_DAILY_INTS = (
    ("work_bursts", sa.SmallInteger), ("active_minutes", sa.SmallInteger), ("logins", sa.SmallInteger),
    ("api_reads", sa.Integer), ("api_writes", sa.Integer), ("writes_offhours", sa.Integer),
    ("writes_mobile", sa.Integer), ("approvals", sa.Integer), ("approvals_mobile", sa.Integer),
    ("http_403", sa.Integer), ("http_422", sa.Integer), ("http_5xx", sa.Integer),
    ("exports", sa.Integer), ("export_rows", sa.Integer), ("deletes", sa.Integer),
    ("max_deletes_10min", sa.SmallInteger), ("new_ip_logins", sa.SmallInteger),
    ("new_device_logins", sa.SmallInteger), ("max_parallel_ips", sa.SmallInteger),
    ("docs_created", sa.Integer), ("on_behalf_received", sa.Integer), ("on_behalf_done", sa.Integer),
    ("page_views", sa.Integer), ("searches", sa.Integer), ("searches_empty", sa.Integer),
    ("client_errors", sa.Integer),
)
_DAILY_JSONS = ("hourly", "screens", "docs", "forms", "reports", "forbidden_routes")


def _has_table(name: str) -> bool:
    return inspect(op.get_bind()).has_table(name)


def _index_names(table: str) -> set[str]:
    return {ix["name"] for ix in inspect(op.get_bind()).get_indexes(table)}


def _zero():
    return sa.text("0")


def upgrade() -> None:
    if not _has_table("tab_ui_event"):
        op.create_table(
            "tab_ui_event",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("occurred_at", sa.DateTime(), nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("session_id", sa.BigInteger(), nullable=True),
            sa.Column("tab_key", sa.Integer(), nullable=False, server_default=_zero()),
            sa.Column("event_type", sa.SmallInteger(), nullable=False),
            sa.Column("route_pattern", sa.String(120), nullable=False, server_default=""),
            sa.Column("form_key", sa.SmallInteger(), nullable=False, server_default=_zero()),
            sa.Column("duration_ms", sa.Integer(), nullable=False, server_default=_zero()),
            sa.Column("result_count", sa.Integer(), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_ui_event_occurred_at", "tab_ui_event", ["occurred_at"])
        op.create_index("ix_ui_event_user_occurred", "tab_ui_event", ["user_id", "occurred_at"])

    if not _has_table("tab_usage_daily"):
        cols = [
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("day", sa.Date(), nullable=False),
            sa.Column("employee_id", sa.BigInteger(), nullable=False, server_default=_zero()),
            sa.Column("company_id", sa.BigInteger(), nullable=False, server_default=_zero()),
            sa.Column("department_id", sa.BigInteger(), nullable=False, server_default=_zero()),
            sa.Column("computed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("is_workday", sa.Boolean(), nullable=False, server_default=_zero()),
            sa.Column("is_holiday", sa.Boolean(), nullable=False, server_default=_zero()),
            sa.Column("work_capacity", sa.Float(), nullable=False, server_default=_zero()),
            sa.Column("leave_days", sa.Float(), nullable=False, server_default=_zero()),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=_zero()),
            sa.Column("first_seen_min", sa.SmallInteger(), nullable=True),
            sa.Column("last_action_min", sa.SmallInteger(), nullable=True),
            sa.Column("active_after_resign", sa.Boolean(), nullable=False, server_default=_zero()),
            sa.Column("dwell_ms", sa.BigInteger(), nullable=False, server_default=_zero()),
            sa.Column("first_route", sa.String(120), nullable=False, server_default=""),
        ]
        cols += [sa.Column(n, t(), nullable=False, server_default=_zero()) for n, t in _DAILY_INTS]
        cols += [sa.Column(n, sa.JSON(), nullable=True) for n in _DAILY_JSONS]
        op.create_table("tab_usage_daily", *cols, sa.PrimaryKeyConstraint("id"),
                        sa.UniqueConstraint("user_id", "day", name="uq_usage_daily_user_day"))
        op.create_index("ix_usage_daily_day", "tab_usage_daily", ["day"])

    if not _has_table("tab_user_usage_snapshot"):
        op.create_table(
            "tab_user_usage_snapshot",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("period_kind", sa.SmallInteger(), nullable=False, server_default="1"),
            sa.Column("period_start", sa.Date(), nullable=False),
            sa.Column("window_weeks", sa.SmallInteger(), nullable=False, server_default="4"),
            sa.Column("schema_version", sa.SmallInteger(), nullable=False, server_default="1"),
            sa.Column("cohort_kind", sa.SmallInteger(), nullable=False, server_default="3"),
            sa.Column("cohort_key", sa.BigInteger(), nullable=False, server_default=_zero()),
            sa.Column("cohort_size", sa.SmallInteger(), nullable=False, server_default=_zero()),
            sa.Column("metrics", sa.JSON(), nullable=False),
            sa.Column("computed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "period_kind", "period_start",
                                name="uq_usage_snapshot_user_period"),
        )
        op.create_index("ix_usage_snapshot_period", "tab_user_usage_snapshot",
                        ["period_kind", "period_start"])

    if not _has_table("tab_user_usage_label"):
        op.create_table(
            "tab_user_usage_label",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("snapshot_id", sa.BigInteger(), nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("period_start", sa.Date(), nullable=False),
            sa.Column("label", sa.SmallInteger(), nullable=False),
            sa.Column("score", sa.Float(), nullable=False, server_default=_zero()),
            sa.Column("evidence", sa.JSON(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("snapshot_id", "label", name="uq_usage_label_snapshot_label"),
        )
        op.create_index("ix_usage_label_period_label", "tab_user_usage_label", ["period_start", "label"])
        op.create_index("ix_usage_label_user", "tab_user_usage_label", ["user_id"])

    cols = {c["name"] for c in inspect(op.get_bind()).get_columns("tab_notification")}
    if "read_at" not in cols:
        op.add_column("tab_notification", sa.Column("read_at", sa.DateTime(), nullable=True))

    for table, name, columns in _INDEXES:
        if name not in _index_names(table):
            op.create_index(name, table, columns)


def downgrade() -> None:
    for table, name, _columns in reversed(_INDEXES):
        if name in _index_names(table):
            op.drop_index(name, table_name=table)

    cols = {c["name"] for c in inspect(op.get_bind()).get_columns("tab_notification")}
    if "read_at" in cols:
        op.drop_column("tab_notification", "read_at")

    for table in ("tab_user_usage_label", "tab_user_usage_snapshot", "tab_usage_daily", "tab_ui_event"):
        if _has_table(table):
            op.drop_table(table)
