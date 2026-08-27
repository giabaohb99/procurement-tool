"""forum_post_pinned_cr199 — cột `pinned_at` cho ghim bài + tab Thông báo (F9a).

Viết tay, KHÔNG autogenerate: hai migration forum trước (9eba2501f2c4,
7889a09c627e) autogenerate đều lôi theo drift ~20 bảng cũ phải cắt tay.

Revision ID: b8d4e6f1a2c9
Revises: 3b46d70224ea
Create Date: 2026-08-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b8d4e6f1a2c9'
down_revision: Union[str, None] = '3b46d70224ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_forum_post',
                  sa.Column('pinned_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('tab_forum_post', 'pinned_at')
