"""agent hub: quan ly nhom tren web — loai nhom, ngung ghi, ban tom tat, nhat ky xem (ai-CR-123)

Revision ID: grp03
Revises: grp02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp03"
down_revision: Union[str, None] = "grp02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_cols() -> list:
    return [
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
    ]


def upgrade() -> None:
    op.add_column("tab_agent_group", sa.Column("category", sa.SmallInteger(), nullable=False, server_default="0"))
    op.add_column("tab_agent_group", sa.Column("paused", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table(
        "tab_agent_group_summary",
        sa.Column("group_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("source", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("question", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("text", sa.Text(), nullable=False),
        *_audit_cols(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_group_sum_group", "tab_agent_group_summary", ["group_id", "id"], unique=False)
    op.create_index("ix_tab_agent_group_summary_user_id", "tab_agent_group_summary", ["user_id"], unique=False)
    op.create_table(
        "tab_agent_group_view",
        sa.Column("group_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("what", sa.String(length=40), nullable=False, server_default=""),
        *_audit_cols(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_agent_group_view_group_id", "tab_agent_group_view", ["group_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tab_agent_group_view_group_id", table_name="tab_agent_group_view")
    op.drop_table("tab_agent_group_view")
    op.drop_index("ix_tab_agent_group_summary_user_id", table_name="tab_agent_group_summary")
    op.drop_index("ix_agent_group_sum_group", table_name="tab_agent_group_summary")
    op.drop_table("tab_agent_group_summary")
    op.drop_column("tab_agent_group", "paused")
    op.drop_column("tab_agent_group", "category")
