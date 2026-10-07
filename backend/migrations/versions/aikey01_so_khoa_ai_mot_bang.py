"""agent hub: so khoa AI mot bang cho cong ty + ca nhan, nhieu hang, uu tien (ai-CR-098, nhom C-04)

  - tab_agent_user_key -> tab_ai_key; user_id -> owner_id
  - them owner_type (1 cong ty · 2 ca nhan; dong cu = 2), model, priority (1 = chinh), daily_cap (0 = tran chung)
  - tab_agent_run.key_id: dong khoa da tra loi luot do (ap tran rieng tung khoa)
  Khong dung du lieu: moi dong cu giu nguyen khoa ma hoa, thanh dong ca nhan uu tien 1.

Revision ID: aikey01
Revises: hq603
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "aikey01"
down_revision: Union[str, None] = "hq603"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_tab_agent_user_key_user_id", table_name="tab_agent_user_key")
    op.rename_table("tab_agent_user_key", "tab_ai_key")
    op.alter_column("tab_ai_key", "user_id", new_column_name="owner_id", existing_type=sa.BigInteger(),
                    existing_nullable=False)
    op.add_column("tab_ai_key", sa.Column("owner_type", sa.SmallInteger(), nullable=False, server_default="2"))
    op.add_column("tab_ai_key", sa.Column("model", sa.String(length=80), nullable=False, server_default=""))
    op.add_column("tab_ai_key", sa.Column("priority", sa.SmallInteger(), nullable=False, server_default="1"))
    op.add_column("tab_ai_key", sa.Column("daily_cap", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_tab_ai_key_owner", "tab_ai_key", ["owner_type", "owner_id"], unique=False)
    op.add_column("tab_agent_run", sa.Column("key_id", sa.BigInteger(), nullable=False, server_default="0"))
    op.create_index("ix_tab_agent_run_key_id", "tab_agent_run", ["key_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tab_agent_run_key_id", table_name="tab_agent_run")
    op.drop_column("tab_agent_run", "key_id")
    op.drop_index("ix_tab_ai_key_owner", table_name="tab_ai_key")
    op.drop_column("tab_ai_key", "daily_cap")
    op.drop_column("tab_ai_key", "priority")
    op.drop_column("tab_ai_key", "model")
    op.drop_column("tab_ai_key", "owner_type")
    op.alter_column("tab_ai_key", "owner_id", new_column_name="user_id", existing_type=sa.BigInteger(),
                    existing_nullable=False)
    op.rename_table("tab_ai_key", "tab_agent_user_key")
    op.create_index("ix_tab_agent_user_key_user_id", "tab_agent_user_key", ["user_id"], unique=False)
