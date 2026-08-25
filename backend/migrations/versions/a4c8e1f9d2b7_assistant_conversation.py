"""tao bang lich su hoi thoai tro ly AI (conversation + message)

Module MOI -> cot role luu SmallInteger theo IntEnum (MessageRole), khong luu chu.

Revision ID: a4c8e1f9d2b7
Revises: a3f7c012e9b5
Create Date: 2026-08-25
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a4c8e1f9d2b7"
down_revision: Union[str, None] = "a3f7c012e9b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_assistant_conversation",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("provider", sa.String(length=30), nullable=False, server_default=""),
        sa.Column("model", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_assistant_conversation_last_message_at",
                    "tab_assistant_conversation", ["last_message_at"])
    # loc danh sach theo chinh chu (created_by) -> danh index
    op.create_index("ix_tab_assistant_conversation_created_by",
                    "tab_assistant_conversation", ["created_by"])

    op.create_table(
        "tab_assistant_message",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("role", sa.SmallInteger(), nullable=False, server_default="1"),  # MessageRole.USER
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(length=30), nullable=False, server_default=""),
        sa.Column("model", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("thinking_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_write_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_assistant_message_conversation_id",
                    "tab_assistant_message", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_tab_assistant_message_conversation_id", table_name="tab_assistant_message")
    op.drop_table("tab_assistant_message")
    op.drop_index("ix_tab_assistant_conversation_created_by",
                  table_name="tab_assistant_conversation")
    op.drop_index("ix_tab_assistant_conversation_last_message_at",
                  table_name="tab_assistant_conversation")
    op.drop_table("tab_assistant_conversation")
