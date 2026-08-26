"""them deleted_count cho tab_import_batch

Revision ID: b2d9f1c47a30
Revises: 16a85b39ddcf
Create Date: 2026-08-26

Đếm số dòng import bị đánh dấu xóa (__/delete/__). Cột nullable + default 0 để
bản ghi cũ không cần điền.
"""
from alembic import op
import sqlalchemy as sa

revision = "b2d9f1c47a30"
down_revision = "16a85b39ddcf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tab_import_batch",
        sa.Column("deleted_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("tab_import_batch", "deleted_count")
