"""Binh luan 2 cap + luot thich (CR-030)

Them cot `parent_id` / `reply_to_user_id` vao `tab_comment` va bang moi
`tab_comment_reaction`. Khong dung toi bang nao khac.

Viet tay thay vi autogenerate: `alembic revision --autogenerate` sinh kem hang tram dong
`alter_column ... nullable=False` cua cac bang cu (drift co san tu truoc), khong lien quan
CR nay va chay len se doi schema ngoai y muon.

Revision ID: 7ac2e5d0b418
Revises: 4fbb4f65df99
"""
from alembic import op
import sqlalchemy as sa

revision = '7ac2e5d0b418'
down_revision = '4fbb4f65df99'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tab_comment', sa.Column('parent_id', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('tab_comment', sa.Column('reply_to_user_id', sa.BigInteger(), nullable=False, server_default='0'))
    op.create_index('ix_tab_comment_parent_id', 'tab_comment', ['parent_id'])

    op.create_table(
        'tab_comment_reaction',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('comment_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('comment_id', 'user_id', name='uq_comment_reaction'),
    )
    op.create_index('ix_tab_comment_reaction_comment_id', 'tab_comment_reaction', ['comment_id'])
    op.create_index('ix_tab_comment_reaction_user_id', 'tab_comment_reaction', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_tab_comment_reaction_user_id', table_name='tab_comment_reaction')
    op.drop_index('ix_tab_comment_reaction_comment_id', table_name='tab_comment_reaction')
    op.drop_table('tab_comment_reaction')
    op.drop_index('ix_tab_comment_parent_id', table_name='tab_comment')
    op.drop_column('tab_comment', 'reply_to_user_id')
    op.drop_column('tab_comment', 'parent_id')
