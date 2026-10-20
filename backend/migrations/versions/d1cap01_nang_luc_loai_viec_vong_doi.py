"""nang luc theo loai viec: loai viec/gio/ket qua cua task + vong doi phieu + chi muc tai dang om -- duoc-CR-656

Revision ID: d1cap01
Revises: d0merge01
Create Date: 2026-10-20

VIET TAY (autogenerate repo nay troi ~650 dong moi lan; khong import ma ung dung).

upgrade (moi buoc tu gac bang inspect -> chay lai sau su co la an toan, MySQL DDL tu commit)
  - tab_work_task_type: danh muc loai viec (UNIQUE (company_id, code)).
  - tab_work_task: + task_type_id, estimate_hours, actual_hours, outcome (deu co mac dinh/NULL -> khong khoa bang lau)
    + ix_work_task_type_status, ix_work_task_completed_at.
  - tab_work_cycle: vong doi phieu da tinh san (UNIQUE (kind, entity_id, role, employee_id) + 3 chi muc).
  - Chi muc D1c (tai dang om): ix_pr_head_status, ix_po_nspt_status, ix_srl_assignee_status, ix_document_drafter_status.
downgrade: go nguoc lai (mat du lieu loai viec/gio/ket qua da nhap tay -- chi lam khi chua ai nhap).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "d1cap01"
down_revision: Union[str, None] = "d0merge01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TASK = "tab_work_task"
_TASK_COLS = (
    ("task_type_id", lambda: sa.Column("task_type_id", sa.BigInteger(), nullable=False, server_default="0")),
    ("estimate_hours", lambda: sa.Column("estimate_hours", sa.Numeric(6, 2), nullable=True)),
    ("actual_hours", lambda: sa.Column("actual_hours", sa.Numeric(6, 2), nullable=True)),
    ("outcome", lambda: sa.Column("outcome", sa.SmallInteger(), nullable=False, server_default="0")),
)
_TASK_INDEXES = (
    ("ix_work_task_type_status", ["task_type_id", "status"]),
    ("ix_work_task_completed_at", ["completed_at"]),
)
#  (bảng, tên chỉ mục, cột) — phục vụ `workload_sources` (D1c).
_LOAD_INDEXES = (
    ("tab_purchase_request", "ix_pr_head_status", ["head_of_dept_id", "status"]),
    ("tab_purchase_order", "ix_po_nspt_status", ["nspt_id", "status"]),
    ("tab_survey_request_line", "ix_srl_assignee_status", ["assignee", "line_status"]),
    ("tab_document", "ix_document_drafter_status", ["drafter_employee_id", "status"]),
)


def _has_index(insp, table: str, name: str) -> bool:
    return any(i["name"] == name for i in insp.get_indexes(table))


def upgrade() -> None:
    insp = inspect(op.get_bind())

    if not insp.has_table("tab_work_task_type"):
        op.create_table(
            "tab_work_task_type",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("code", sa.String(30), nullable=False, server_default=""),
            sa.Column("name", sa.String(120), nullable=False, server_default=""),
            sa.Column("default_estimate_hours", sa.Numeric(6, 2), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("company_id", "code", name="uq_work_task_type_code"),
        )
        op.create_index("ix_work_task_type_company", "tab_work_task_type", ["company_id", "is_active"])

    have = {c["name"] for c in insp.get_columns(_TASK)}
    for name, make in _TASK_COLS:
        if name not in have:
            op.add_column(_TASK, make())
    insp = inspect(op.get_bind())
    for name, cols in _TASK_INDEXES:
        if not _has_index(insp, _TASK, name):
            op.create_index(name, _TASK, cols)

    if not insp.has_table("tab_work_cycle"):
        op.create_table(
            "tab_work_cycle",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("kind", sa.SmallInteger(), nullable=False),
            sa.Column("entity_id", sa.BigInteger(), nullable=False),
            sa.Column("role", sa.SmallInteger(), nullable=False),
            sa.Column("employee_id", sa.BigInteger(), nullable=False),
            sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("task_type_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("done_at", sa.DateTime(), nullable=True),
            sa.Column("outcome", sa.SmallInteger(), nullable=False),
            sa.Column("cycle_hours", sa.Float(), nullable=True),
            sa.Column("rework_count", sa.SmallInteger(), nullable=False, server_default="0"),
            sa.Column("is_estimated", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("is_late", sa.Boolean(), nullable=True),
            sa.Column("estimate_hours", sa.Numeric(6, 2), nullable=True),
            sa.Column("actual_hours", sa.Numeric(6, 2), nullable=True),
            sa.Column("review_outcome", sa.SmallInteger(), nullable=False, server_default="0"),
            sa.Column("computed_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("kind", "entity_id", "role", "employee_id", name="uq_work_cycle_key"),
        )
        op.create_index("ix_work_cycle_done", "tab_work_cycle", ["done_at", "kind"])
        op.create_index("ix_work_cycle_emp", "tab_work_cycle", ["employee_id", "kind", "done_at"])
        op.create_index("ix_work_cycle_type", "tab_work_cycle", ["task_type_id", "done_at"])

    insp = inspect(op.get_bind())
    for table, name, cols in _LOAD_INDEXES:
        if insp.has_table(table) and not _has_index(insp, table, name):
            op.create_index(name, table, cols)


def downgrade() -> None:
    insp = inspect(op.get_bind())
    for table, name, _cols in _LOAD_INDEXES:
        if insp.has_table(table) and _has_index(insp, table, name):
            op.drop_index(name, table_name=table)
    if insp.has_table("tab_work_cycle"):
        op.drop_table("tab_work_cycle")
    for name, _cols in _TASK_INDEXES:
        if _has_index(insp, _TASK, name):
            op.drop_index(name, table_name=_TASK)
    insp = inspect(op.get_bind())
    have = {c["name"] for c in insp.get_columns(_TASK)}
    for name, _make in reversed(_TASK_COLS):
        if name in have:
            op.drop_column(_TASK, name)
    if insp.has_table("tab_work_task_type"):
        op.drop_table("tab_work_task_type")
