"""Nhac ten nhieu nguoi trong mot binh luan (CR-031)

Them bang `tab_comment_mention`. Khong dung toi bang nao khac, khong doi cot cua
`tab_comment` — the `@[<user_id>]` nam ngay trong cot `body` san co.

Viet tay thay vi autogenerate: `alembic revision --autogenerate` sinh kem hang tram dong
`alter_column ... nullable=False` cua cac bang cu (drift co san tu truoc), khong lien quan
CR nay va chay len se doi schema ngoai y muon.

Revision ID: 9b41c7e0d5a2
Revises: 7ac2e5d0b418
"""
from alembic import op
import sqlalchemy as sa

revision = '9b41c7e0d5a2'
down_revision = '7ac2e5d0b418'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tab_comment_mention',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('comment_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('comment_id', 'user_id', name='uq_comment_mention'),
    )
    op.create_index('ix_tab_comment_mention_comment_id', 'tab_comment_mention', ['comment_id'])
    op.create_index('ix_tab_comment_mention_user_id', 'tab_comment_mention', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_tab_comment_mention_user_id', table_name='tab_comment_mention')
    op.drop_index('ix_tab_comment_mention_comment_id', table_name='tab_comment_mention')
    op.drop_table('tab_comment_mention')
