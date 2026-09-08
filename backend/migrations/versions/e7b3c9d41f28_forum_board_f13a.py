"""forum_board_f13a

Chuyên mục kiểu VOZ (F13a, QĐ-D7 — doc/erp/dien-dan/02-lo-trinh-phase.md):
bảng `tab_forum_board` (nhóm tiêu đề + box, hai tầng qua `parent_id`) và ba cột
mới trên `tab_forum_post`: `board_id` (NULL = bài Bảng tin thuần), `title`
(bắt buộc khi có board_id — luật ở service), `prefix` (ForumPrefix).

CHÚ Ý nhánh: phiên song song "tiền treo trả trước" đang giữ migration chưa
commit `d5e8f2a71c04` cũng rẽ từ `7e93b1977593` — phiên đó phải re-parent
(đổi `down_revision` thành đầu mới) trước khi commit, không thì hai đầu.

Revision ID: e7b3c9d41f28
Revises: c3a91d47f2b8
Create Date: 2026-09-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e7b3c9d41f28'
down_revision: Union[str, None] = 'c3a91d47f2b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_forum_board',
        sa.Column('parent_id', sa.BigInteger(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('icon', sa.String(length=50), nullable=False),
        sa.Column('sort_order', sa.SmallInteger(), nullable=False),
        sa.Column('status', sa.SmallInteger(), nullable=False),
        sa.Column('audience', sa.SmallInteger(), nullable=False),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.add_column('tab_forum_post', sa.Column('board_id', sa.BigInteger(), nullable=True))
    op.add_column('tab_forum_post', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('tab_forum_post',
                  sa.Column('prefix', sa.SmallInteger(), server_default='0', nullable=False))
    op.create_index('ix_forum_post_board_id', 'tab_forum_post', ['board_id', 'id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_forum_post_board_id', table_name='tab_forum_post')
    op.drop_column('tab_forum_post', 'prefix')
    op.drop_column('tab_forum_post', 'title')
    op.drop_column('tab_forum_post', 'board_id')
    op.drop_table('tab_forum_board')
