"""hoat dong AI vao ho so cach lam viec: tab_ai_usage_daily + tab_audit_log.ai_channel (ai-CR-230)

Revision ID: aiusage01
Revises: usgprof02
Create Date: 2026-10-20

VIET TAY (autogenerate repo nay troi nhieu; khong import ma ung dung). doc/erp/22 §5.

upgrade
  - `tab_audit_log.ai_channel` SMALLINT NOT NULL DEFAULT 0 (0 = nguoi tu bam; 1 web · 2 Telegram · 3 MCP · 4 Zalo).
    Khong chi muc (bang lon, cot it gia tri). MySQL 8 them cot co mac dinh theo kieu INSTANT, khong chep bang.
  - Bang `tab_ai_usage_daily` (nguoi × ngay × kenh, chi so dem) — dich vu AI day sang qua cong B.
  - `tab_agent_intent.tool_calls_n` + `denied_n` (che do nhung: so y dinh nam o DB ERP; che do tach co agent0016).
downgrade: bo ca ba. Tu gac (inspect) nen chay lai sau su co (MySQL DDL tu commit) la an toan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "aiusage01"
down_revision: Union[str, None] = "usgprof02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_USAGE = "tab_ai_usage_daily"
_INTENT = "tab_agent_intent"


def _cols(table: str) -> set[str]:
    insp = inspect(op.get_bind())
    return {c["name"] for c in insp.get_columns(table)} if insp.has_table(table) else set()


def upgrade() -> None:
    if "ai_channel" not in _cols("tab_audit_log"):
        op.add_column("tab_audit_log", sa.Column("ai_channel", sa.SmallInteger(), nullable=False, server_default="0"))
    if not inspect(op.get_bind()).has_table(_USAGE):
        op.create_table(
            _USAGE,
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("day", sa.Date(), nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("employee_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("channel", sa.SmallInteger(), nullable=False),
            sa.Column("turns", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("tool_calls", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("denied", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("errors", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("drafts_created", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("drafts_confirmed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("clients", sa.JSON(), nullable=True),
            sa.Column("tool_groups", sa.JSON(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("day", "user_id", "channel", name="uq_ai_usage_daily_day_user_channel"),
        )
        op.create_index("ix_tab_ai_usage_daily_day", _USAGE, ["day"])
        op.create_index("ix_tab_ai_usage_daily_user_id", _USAGE, ["user_id"])
        op.create_index("ix_tab_ai_usage_daily_employee_id", _USAGE, ["employee_id"])
    have = _cols(_INTENT)
    if have and "tool_calls_n" not in have:
        op.add_column(_INTENT, sa.Column("tool_calls_n", sa.SmallInteger(), nullable=False, server_default="0"))
    if have and "denied_n" not in have:
        op.add_column(_INTENT, sa.Column("denied_n", sa.SmallInteger(), nullable=False, server_default="0"))


def downgrade() -> None:
    have = _cols(_INTENT)
    for col in ("denied_n", "tool_calls_n"):
        if col in have:
            op.drop_column(_INTENT, col)
    if inspect(op.get_bind()).has_table(_USAGE):
        op.drop_table(_USAGE)
    if "ai_channel" in _cols("tab_audit_log"):
        op.drop_column("tab_audit_log", "ai_channel")
