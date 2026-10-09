"""agent hub: nen hoi thoai — ban tom tat theo tung cuoc + dau cau tra loi rut tu cong cu (ai-CR-136)

Revision ID: grp04
Revises: grp03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp04"
down_revision: Union[str, None] = "grp03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_agent_message", sa.Column("tool_used", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("tab_assistant_message", sa.Column("tool_used", sa.Boolean(), nullable=False,
                                                     server_default=sa.false()))
    op.create_table(
        "tab_agent_conv_summary",
        sa.Column("scope", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("scope_key", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("user_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("upto_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("folded_turns", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ux_agent_conv_summary_key", "tab_agent_conv_summary", ["scope", "scope_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ux_agent_conv_summary_key", table_name="tab_agent_conv_summary")
    op.drop_table("tab_agent_conv_summary")
    op.drop_column("tab_assistant_message", "tool_used")
    op.drop_column("tab_agent_message", "tool_used")
