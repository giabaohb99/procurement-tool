"""tab_vehicle_booking: thêm chế độ TỰ LÁI (is_self_drive + GPLX người yêu cầu)

Revision ID: dx3self01
Revises: dxmail03
Create Date: 2026-09-04

Chỉ THÊM cột (viết tay để khỏi cuốn theo drift autogenerate).
"""
from alembic import op
import sqlalchemy as sa

revision = "dx3self01"
down_revision = "dxmail03"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tab_vehicle_booking",
                  sa.Column("is_self_drive", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("tab_vehicle_booking",
                  sa.Column("license_number", sa.String(length=50), nullable=False, server_default=""))
    op.add_column("tab_vehicle_booking",
                  sa.Column("license_class", sa.String(length=20), nullable=False, server_default=""))


def downgrade():
    op.drop_column("tab_vehicle_booking", "license_class")
    op.drop_column("tab_vehicle_booking", "license_number")
    op.drop_column("tab_vehicle_booking", "is_self_drive")
