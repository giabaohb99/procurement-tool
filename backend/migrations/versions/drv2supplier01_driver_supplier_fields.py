"""tab_driver: thêm nguồn thuê ngoài (doanh nghiệp/cá nhân) + MST, địa chỉ thuế, CCCD

Revision ID: drv2supplier01
Revises: drv1class01
Create Date: 2026-09-03

Chỉ THÊM cột, không đụng gì khác (viết tay để khỏi cuốn theo drift autogenerate).
"""
from alembic import op
import sqlalchemy as sa

revision = "drv2supplier01"
down_revision = "drv1class01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tab_driver", sa.Column("supplier_type", sa.SmallInteger(), nullable=False, server_default="0"))
    op.add_column("tab_driver", sa.Column("tax_code", sa.String(length=50), nullable=False, server_default=""))
    op.add_column("tab_driver", sa.Column("tax_address", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("tab_driver", sa.Column("id_number", sa.String(length=50), nullable=False, server_default=""))


def downgrade():
    op.drop_column("tab_driver", "id_number")
    op.drop_column("tab_driver", "tax_address")
    op.drop_column("tab_driver", "tax_code")
    op.drop_column("tab_driver", "supplier_type")
