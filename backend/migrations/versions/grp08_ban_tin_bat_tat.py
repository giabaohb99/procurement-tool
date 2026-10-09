"""agent hub: dang ky ban tin bat / tat trong chat (ai-CR-140)

Revision ID: grp08
Revises: grp07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp08"
down_revision: Union[str, None] = "grp07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_agent_brief_sub",
        sa.Column("user_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("kind", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("hour", sa.SmallInteger(), nullable=False, server_default="7"),
        sa.Column("minute", sa.SmallInteger(), nullable=False, server_default="30"),
        sa.Column("days", sa.SmallInteger(), nullable=False, server_default="127"),
        sa.Column("topic", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("sub_code", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("last_sent_on", sa.String(length=10), nullable=False, server_default=""),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_brief_sub_user", "tab_agent_brief_sub", ["user_id", "kind"])


def downgrade() -> None:
    op.drop_index("ix_agent_brief_sub_user", table_name="tab_agent_brief_sub")
    op.drop_table("tab_agent_brief_sub")
