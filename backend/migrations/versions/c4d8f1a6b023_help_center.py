"""module help_center — bang tab_help_article + tab_help_article_slide (HDSD)

Cay bai viet huong dan su dung: tab_help_article tu tham chieu parent_id,
moi bai co the co nhieu slide anh huong dan tung buoc (xoa bai -> xoa slide).

Revision ID: c4d8f1a6b023
Revises: e1c3a5b7d9f2
Create Date: 2026-08-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4d8f1a6b023"
down_revision: Union[str, None] = "e1c3a5b7d9f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_help_article",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["parent_id"], ["tab_help_article.id"]),
    )
    op.create_index(op.f("ix_tab_help_article_parent_id"), "tab_help_article", ["parent_id"], unique=False)

    op.create_table(
        "tab_help_article_slide",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("step_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["article_id"], ["tab_help_article.id"], ondelete="CASCADE"),
    )
    op.create_index(
        op.f("ix_tab_help_article_slide_article_id"), "tab_help_article_slide", ["article_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tab_help_article_slide_article_id"), table_name="tab_help_article_slide")
    op.drop_table("tab_help_article_slide")
    op.drop_index(op.f("ix_tab_help_article_parent_id"), table_name="tab_help_article")
    op.drop_table("tab_help_article")
