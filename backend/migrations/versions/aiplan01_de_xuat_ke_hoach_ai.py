"""kh-AI1-3 — bảng đề xuất kế hoạch AI chờ duyệt `tab_ai_plan_proposal` (doc/erp/tai-lieu-ai/22 §5.2)

Revision ID: aiplan01
Revises: cr663hdname01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aiplan01"
down_revision: Union[str, Sequence[str], None] = "cr663hdname01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_ai_plan_proposal",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("owner_employee_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("channel", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("title", sa.String(200), nullable=False, server_default=""),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("plan_ai", sa.JSON(), nullable=True),
        sa.Column("plan_final", sa.JSON(), nullable=True),
        sa.Column("diff", sa.JSON(), nullable=True),
        sa.Column("list_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decided_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("reject_reason", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.create_index("ix_ai_plan_owner_status", "tab_ai_plan_proposal", ["owner_user_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_ai_plan_owner_status", table_name="tab_ai_plan_proposal")
    op.drop_table("tab_ai_plan_proposal")
