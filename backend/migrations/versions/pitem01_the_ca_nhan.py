"""agent hub: the ca nhan — lich trinh, chi tieu, mua sam cua tung nguoi (ai-CR-103, nhom C-05)

Bang moi tab_agent_personal_item; khong dung bang cu.

Revision ID: pitem01
Revises: hq608
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "pitem01"
down_revision: Union[str, None] = "hq608"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_agent_personal_item",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("title", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("category", sa.String(length=60), nullable=False, server_default=""),
        sa.Column("at", sa.DateTime(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_agent_personal_item_user_id", "tab_agent_personal_item", ["user_id"], unique=False)
    op.create_index("ix_agent_personal_item_user_kind", "tab_agent_personal_item", ["user_id", "kind", "status"],
                    unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_personal_item_user_kind", table_name="tab_agent_personal_item")
    op.drop_index("ix_tab_agent_personal_item_user_id", table_name="tab_agent_personal_item")
    op.drop_table("tab_agent_personal_item")
