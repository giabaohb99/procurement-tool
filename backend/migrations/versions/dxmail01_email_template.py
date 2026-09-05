"""tab_email_template: mẫu email thông báo theo bước (sửa được ở /system/settings)

Revision ID: dxmail01
Revises: veh2supplier01
Create Date: 2026-09-04

Bảng chỉ chứa các event NGƯỜI DÙNG ĐÃ SỬA; thiếu dòng thì dùng mẫu mặc định trong
code. Viết tay (chỉ tạo đúng bảng này) để khỏi cuốn theo drift autogenerate.
"""
from alembic import op
import sqlalchemy as sa

revision = "dxmail01"
down_revision = "veh2supplier01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tab_email_template",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("event", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=150), nullable=False, server_default=""),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("subject", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("body_html", sa.Text(), nullable=False),
    )
    op.create_index("ix_tab_email_template_event", "tab_email_template", ["event"], unique=True)


def downgrade():
    op.drop_index("ix_tab_email_template_event", table_name="tab_email_template")
    op.drop_table("tab_email_template")
