"""tab_email_exclusion: loại trừ email theo cá nhân / phòng ban / công ty

Revision ID: dxmail02
Revises: dxmail01
Create Date: 2026-09-04

Viết tay (chỉ tạo đúng bảng này) để khỏi cuốn theo drift autogenerate.
"""
from alembic import op
import sqlalchemy as sa

revision = "dxmail02"
down_revision = "dxmail01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tab_email_exclusion",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("ref_id", sa.BigInteger(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False, server_default=""),
        sa.UniqueConstraint("scope", "ref_id", name="uq_email_exclusion_scope_ref"),
    )
    op.create_index("ix_tab_email_exclusion_scope", "tab_email_exclusion", ["scope"])
    op.create_index("ix_tab_email_exclusion_ref_id", "tab_email_exclusion", ["ref_id"])


def downgrade():
    op.drop_index("ix_tab_email_exclusion_ref_id", table_name="tab_email_exclusion")
    op.drop_index("ix_tab_email_exclusion_scope", table_name="tab_email_exclusion")
    op.drop_table("tab_email_exclusion")
