"""po_item fg_name (Tên HH thành phẩm — tự gắn từ master SP)

Revision ID: a1d4f8b2c6e7
Revises: f7c2b4a9e1d3
Create Date: 2026-07-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1d4f8b2c6e7'
down_revision: Union[str, None] = 'f7c2b4a9e1d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_po_item', sa.Column('fg_name', sa.String(length=255), nullable=False, server_default=''))


def downgrade() -> None:
    op.drop_column('tab_po_item', 'fg_name')
