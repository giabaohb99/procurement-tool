"""agent hub: nhom Telegram bot dang o + tin nhom (ai-CR-105)

Hai bang moi tab_agent_group, tab_agent_group_message; khong dung bang cu.

Revision ID: grp01
Revises: meet01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp01"
down_revision: Union[str, None] = "meet01"
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
    op.create_table(
        "tab_agent_group",
        sa.Column("chat_id", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("title", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("owner_tg_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.Column("left_at", sa.DateTime(), nullable=True),
        *_audit_cols(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_agent_group_chat_id", "tab_agent_group", ["chat_id"], unique=True)
    op.create_index("ix_tab_agent_group_owner_user_id", "tab_agent_group", ["owner_user_id"], unique=False)
    op.create_table(
        "tab_agent_group_message",
        sa.Column("group_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("tg_message_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("from_tg_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("from_name", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("file", sa.JSON(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        *_audit_cols(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_group_msg_group_sent", "tab_agent_group_message", ["group_id", "sent_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_group_msg_group_sent", table_name="tab_agent_group_message")
    op.drop_table("tab_agent_group_message")
    op.drop_index("ix_tab_agent_group_owner_user_id", table_name="tab_agent_group")
    op.drop_index("ix_tab_agent_group_chat_id", table_name="tab_agent_group")
    op.drop_table("tab_agent_group")
