"""agent hub: so ghi nho ca nhan hai tang + dau cong ty / ca nhan tren tin nhan (ai-CR-095, nhom C-02 + C-06)

  - tab_agent_memory : MOI NGUOI MOT DONG, `text` Markdown bon muc, tran 8.000 ky tu — nap vao moi cau hoi
  - tab_agent_note   : ghi chu dai cua tung nguoi (khong tran), vector o collection rieng cua Qdrant
  - tab_agent_message.scope : 0 chua phan · 1 viec cong ty · 2 viec ca nhan

Revision ID: pmem01
Revises: wsched01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "pmem01"
down_revision: Union[str, None] = "wsched01"
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
        "tab_agent_memory",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        *_audit_cols(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_agent_memory_user_id", "tab_agent_memory", ["user_id"], unique=True)

    op.create_table(
        "tab_agent_note",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("chars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("indexed_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        *_audit_cols(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_agent_note_user_id", "tab_agent_note", ["user_id"], unique=False)

    op.add_column("tab_agent_message", sa.Column("scope", sa.SmallInteger(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("tab_agent_message", "scope")
    op.drop_index("ix_tab_agent_note_user_id", table_name="tab_agent_note")
    op.drop_table("tab_agent_note")
    op.drop_index("ix_tab_agent_memory_user_id", table_name="tab_agent_memory")
    op.drop_table("tab_agent_memory")
