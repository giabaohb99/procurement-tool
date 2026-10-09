"""agent hub: so sao luu DB cua dich vu AI (ai-CR-139)

Revision ID: grp07
Revises: grp06

Bảng chỉ có dữ liệu khi bot chạy tách DB; tạo ở cây ERP cho hai cây cùng hình.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp07"
down_revision: Union[str, None] = "grp06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_agent_db_backup",
        sa.Column("kind", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("source", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("file_key", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_db_backup_kind", "tab_agent_db_backup", ["kind", "status", "id"])


def downgrade() -> None:
    op.drop_index("ix_agent_db_backup_kind", table_name="tab_agent_db_backup")
    op.drop_table("tab_agent_db_backup")
