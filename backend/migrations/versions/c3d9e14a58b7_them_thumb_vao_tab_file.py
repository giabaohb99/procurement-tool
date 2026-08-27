"""them_thumb_vao_tab_file — cột thumb_key/thumb_url cho bản thumbnail sinh lúc upload.

Viết tay (không autogenerate — khuôn 9eba2501f2c4/7889a09c627e: autogenerate lôi
drift các bảng cũ). Tệp cũ để rỗng: bên đọc fallback về `url`, không backfill.

Revision ID: c3d9e14a58b7
Revises: 7889a09c627e
Create Date: 2026-08-27 09:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3d9e14a58b7'
down_revision: Union[str, None] = '7889a09c627e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_file',
                  sa.Column('thumb_key', sa.String(length=500), server_default='', nullable=False))
    op.add_column('tab_file',
                  sa.Column('thumb_url', sa.String(length=1000), server_default='', nullable=False))


def downgrade() -> None:
    op.drop_column('tab_file', 'thumb_url')
    op.drop_column('tab_file', 'thumb_key')
