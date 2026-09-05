"""tab_driver: thêm cột license_class (HẠNG GPLX, tách khỏi số GPLX)

Revision ID: drv1class01
Revises: vcap2float01
Create Date: 2026-09-03

Chỉ THÊM một cột, không đụng gì khác (viết tay để khỏi cuốn theo drift autogenerate).
"""
from alembic import op
import sqlalchemy as sa

revision = "drv1class01"
down_revision = "vcap2float01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "tab_driver",
        sa.Column("license_class", sa.String(length=20), nullable=False, server_default=""),
    )


def downgrade():
    op.drop_column("tab_driver", "license_class")
