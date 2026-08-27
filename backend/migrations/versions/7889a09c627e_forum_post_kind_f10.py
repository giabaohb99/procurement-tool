"""forum_post_kind_f10 — cột `kind` cho bài sự kiện (F10: đổi ảnh đại diện).

Autogenerate kèm rất nhiều drift alter_column/index của các bảng cũ (khuôn
migration 9eba2501f2c4 cũng phải cắt) — đã bỏ hết, chỉ giữ đúng thay đổi forum.

Revision ID: 7889a09c627e
Revises: 9eba2501f2c4
Create Date: 2026-08-27 05:01:45.662010
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7889a09c627e'
down_revision: Union[str, None] = '9eba2501f2c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_forum_post',
                  sa.Column('kind', sa.SmallInteger(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('tab_forum_post', 'kind')
