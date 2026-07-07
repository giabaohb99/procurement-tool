"""product hh_code + hh_name (đồng bộ sản phẩm — liên kết Mã HH)

Revision ID: f7c2b4a9e1d3
Revises: e5b3d9a1c8f0
Create Date: 2026-07-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f7c2b4a9e1d3'
down_revision: Union[str, None] = 'e5b3d9a1c8f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_product', sa.Column('hh_code', sa.String(length=50), nullable=False, server_default=''))
    op.add_column('tab_product', sa.Column('hh_name', sa.String(length=255), nullable=False, server_default=''))
    op.create_index('ix_tab_product_hh_code', 'tab_product', ['hh_code'])


def downgrade() -> None:
    op.drop_index('ix_tab_product_hh_code', table_name='tab_product')
    op.drop_column('tab_product', 'hh_name')
    op.drop_column('tab_product', 'hh_code')
