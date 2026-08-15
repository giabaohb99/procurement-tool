"""thu vien van ban mau

Revision ID: b62f3c8d1a04
Revises: a41c7d5e9b02
Create Date: 2026-08-14 10:30:00.000000

Mỗi mẫu thuộc một loại văn bản. Khi tạo văn bản, nội dung mẫu được chép vào
phiên bản 1.0 nên bảng văn bản không cần giữ khóa tham chiếu về mẫu.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "b62f3c8d1a04"
down_revision: Union[str, None] = "a41c7d5e9b02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_document_template",
        sa.Column("doc_type_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("content_html", mysql.MEDIUMTEXT(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "doc_type_id",
            "name",
            name="uq_document_template_type_name",
        ),
    )
    op.create_index(
        "ix_document_template_type_active",
        "tab_document_template",
        ["doc_type_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_table("tab_document_template")
