"""import_batch + import_log (hạ tầng công cụ import)

Revision ID: 2bad028f037a
Revises: f7de8fed036a
Create Date: 2026-07-18

Chỉ tạo 2 bảng của công cụ import. (Autogenerate ban đầu dính nhiều thay đổi
drift model↔DB không liên quan — đã bỏ, chỉ giữ phần import.)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2bad028f037a"
down_revision: Union[str, None] = "f7de8fed036a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_import_batch",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("module", sa.SmallInteger(), nullable=False),
        sa.Column("mode", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("filename", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("file_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sheet_info", sa.Text(), nullable=False),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warning_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tab_import_batch_module"), "tab_import_batch", ["module"], unique=False)
    op.create_index(op.f("ix_tab_import_batch_status"), "tab_import_batch", ["status"], unique=False)

    op.create_table(
        "tab_import_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("batch_id", sa.BigInteger(), nullable=False),
        sa.Column("sheet", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("row_no", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("category", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("ref_key", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("target_code", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("raw", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tab_import_log_batch_id"), "tab_import_log", ["batch_id"], unique=False)
    op.create_index(op.f("ix_tab_import_log_level"), "tab_import_log", ["level"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tab_import_log_level"), table_name="tab_import_log")
    op.drop_index(op.f("ix_tab_import_log_batch_id"), table_name="tab_import_log")
    op.drop_table("tab_import_log")
    op.drop_index(op.f("ix_tab_import_batch_status"), table_name="tab_import_batch")
    op.drop_index(op.f("ix_tab_import_batch_module"), table_name="tab_import_batch")
    op.drop_table("tab_import_batch")
