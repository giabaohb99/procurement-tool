"""db_backup — bảng theo dõi các bản sao lưu CSDL (Task Backup)

Mỗi dòng = 1 lần sao lưu. File dump (.sql.gz) đẩy lên R2 (prefix backups/),
chỉ lưu key + metadata ở đây. Bot (celery-beat) chạy 2 lần/ngày, giữ N bản mới nhất.

Revision ID: d1f2a3b4c5e6
Revises: c5e7092b1d46
Create Date: 2026-07-30 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d1f2a3b4c5e6"
down_revision: Union[str, None] = "c5e7092b1d46"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_db_backup",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("file_key", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_db_backup_status", "tab_db_backup", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tab_db_backup_status", table_name="tab_db_backup")
    op.drop_table("tab_db_backup")
