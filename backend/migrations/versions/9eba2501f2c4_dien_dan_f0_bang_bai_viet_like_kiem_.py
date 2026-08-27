"""dien_dan_f0_bang_bai_viet_like_kiem_duyet

Diễn đàn nội bộ F0 (doc/erp/dien-dan/02-lo-trinh-phase.md): ba bảng
tab_forum_post / tab_forum_reaction / tab_forum_moderation_log.

Tệp autogenerate gốc kèm theo cả trăm dòng alter_column NOT NULL + đảo index
của các bảng CŨ (drift giữa model và DB có từ trước, không thuộc F0) — đã cắt
sạch, chỉ giữ đúng phần forum.

Revision ID: 9eba2501f2c4
Revises: b2d9f1c47a30
Create Date: 2026-08-27 02:54:54.273619
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9eba2501f2c4'
down_revision: Union[str, None] = 'c4d8a2f9e617'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_forum_post',
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.SmallInteger(), nullable=False),
        sa.Column('audience', sa.SmallInteger(), nullable=False),
        sa.Column('dept_id', sa.BigInteger(), nullable=False),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_forum_post_status_id', 'tab_forum_post', ['status', 'id'], unique=False)
    op.create_index('ix_forum_post_author_id', 'tab_forum_post', ['created_by', 'id'], unique=False)

    op.create_table('tab_forum_reaction',
        sa.Column('post_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('kind', sa.SmallInteger(), nullable=False),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id', 'user_id', name='uq_forum_reaction'),
    )
    op.create_index(op.f('ix_tab_forum_reaction_post_id'), 'tab_forum_reaction', ['post_id'], unique=False)
    op.create_index(op.f('ix_tab_forum_reaction_user_id'), 'tab_forum_reaction', ['user_id'], unique=False)

    op.create_table('tab_forum_moderation_log',
        sa.Column('post_id', sa.BigInteger(), nullable=False),
        sa.Column('action', sa.SmallInteger(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('notified_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_forum_moderation_log_post_id'), 'tab_forum_moderation_log', ['post_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_forum_moderation_log_post_id'), table_name='tab_forum_moderation_log')
    op.drop_table('tab_forum_moderation_log')
    op.drop_index(op.f('ix_tab_forum_reaction_user_id'), table_name='tab_forum_reaction')
    op.drop_index(op.f('ix_tab_forum_reaction_post_id'), table_name='tab_forum_reaction')
    op.drop_table('tab_forum_reaction')
    op.drop_index('ix_forum_post_author_id', table_name='tab_forum_post')
    op.drop_index('ix_forum_post_status_id', table_name='tab_forum_post')
    op.drop_table('tab_forum_post')
