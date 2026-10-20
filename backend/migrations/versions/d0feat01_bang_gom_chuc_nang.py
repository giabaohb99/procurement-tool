"""tab_feature_usage_daily: bang gom ngay theo chuc nang cho bao cao "Muc dung chuc nang" -- duoc-CR-655

Revision ID: d0feat01
Revises: d0merge01
Create Date: 2026-10-20

VIET TAY (autogenerate repo nay troi ~650 dong moi lan; khong import ma ung dung).

upgrade: tao bang (nguoi x ngay x loai x ma x route, chi so dem) + unique + chi muc (day, kind).
downgrade: drop bang. Tu gac (inspect) nen chay lai sau su co (MySQL DDL tu commit) la an toan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "d0feat01"
down_revision: Union[str, None] = "d0merge01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "tab_feature_usage_daily"


def upgrade() -> None:
    if inspect(op.get_bind()).has_table(_TABLE):
        return
    op.create_table(
        _TABLE,
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("kind", sa.SmallInteger(), nullable=False),
        sa.Column("code", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("route", sa.String(120), nullable=False, server_default=""),
        sa.Column("uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("abandons", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("day", "user_id", "kind", "code", "route", name="uq_feature_daily_day_user_feature"),
    )
    op.create_index("ix_feature_daily_day_kind", _TABLE, ["day", "kind"])


def downgrade() -> None:
    if inspect(op.get_bind()).has_table(_TABLE):
        op.drop_table(_TABLE)
