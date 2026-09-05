"""vehicle.capacity Integer -> Float (chứa tải trọng lẻ như 2.4 / 6.8 tấn)

Revision ID: vcap2float01
Revises: 62540f5e1a14
Create Date: 2026-09-03

Chỉ đổi kiểu MỘT cột, không đụng gì khác (autogenerate cuốn theo drift toàn repo nên
viết tay). Số chỗ (chở người) vẫn là số nguyên, lưu trong Float không mất mát.
"""
from alembic import op
import sqlalchemy as sa

revision = "vcap2float01"
down_revision = "62540f5e1a14"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "tab_vehicle", "capacity",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "tab_vehicle", "capacity",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
