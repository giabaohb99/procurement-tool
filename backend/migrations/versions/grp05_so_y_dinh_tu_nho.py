"""agent hub: so y dinh + diem tu rut ghi nho (ai-CR-137, phase 13.1-13.3)

Revision ID: grp05
Revises: rpttpl01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp05"
down_revision: Union[str, None] = "rpttpl01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit() -> list:
    return [
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    ]


def upgrade() -> None:
    op.create_table(
        "tab_agent_intent",
        sa.Column("user_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("channel", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("scope", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("scope_key", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("intent", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("sub_intent", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("entities", sa.JSON(), nullable=False),
        sa.Column("tools", sa.JSON(), nullable=False),
        sa.Column("outcome", sa.SmallInteger(), nullable=False, server_default="0"),
        *_audit(),
    )
    op.create_index("ix_agent_intent_user", "tab_agent_intent", ["user_id", "created_at"])
    op.create_index("ix_agent_intent_created", "tab_agent_intent", ["created_at"])
    op.create_table(
        "tab_agent_memory_candidate",
        sa.Column("user_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("section", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("line", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("key_hash", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("hits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("day_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_day", sa.String(length=10), nullable=False, server_default=""),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("source", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("written_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        *_audit(),
    )
    op.create_index("ux_agent_memory_candidate_key", "tab_agent_memory_candidate", ["user_id", "key_hash"],
                    unique=True)


def downgrade() -> None:
    op.drop_index("ux_agent_memory_candidate_key", table_name="tab_agent_memory_candidate")
    op.drop_table("tab_agent_memory_candidate")
    op.drop_index("ix_agent_intent_created", table_name="tab_agent_intent")
    op.drop_index("ix_agent_intent_user", table_name="tab_agent_intent")
    op.drop_table("tab_agent_intent")
