"""forum_body_format_cr261

Rich text cho bài diễn đàn (CR-261): cột `body_format` trên `tab_forum_post` —
0 = chữ trơn (toàn bộ bài cũ, giữ nguyên đường vẽ), 1 = HTML đã qua
`sanitize_html` của help_center ngay tại service. Áp cho CẢ Bảng tin lẫn
chủ đề trong box; bình luận vẫn chữ trơn, không đụng.

Viết TAY, không autogenerate — autogenerate trên DB dev kéo theo drift ~20 bảng
kèm cả lệnh drop cột thật (bài học F13a).

Revision ID: f8b3d6a2c714
Revises: a1c58f27d3e6
Create Date: 2026-09-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f8b3d6a2c714'
down_revision: Union[str, None] = 'a1c58f27d3e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_forum_post',
                  sa.Column('body_format', sa.SmallInteger(),
                            server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('tab_forum_post', 'body_format')
