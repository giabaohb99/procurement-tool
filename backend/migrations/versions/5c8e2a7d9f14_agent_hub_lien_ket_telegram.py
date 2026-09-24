"""agent hub: bang tab_agent_chat_link — lien ket chat Telegram voi tai khoan ERP (ai-CR-038)

Nguoi dung lay ma mot lan o trang ca nhan ERP roi nhan /dangnhap <ma> cho bot. Chi bang
cua bot, khong dung bang ERP.

Revision ID: 5c8e2a7d9f14
Revises: 9a1f3c5e7b20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5c8e2a7d9f14'
down_revision: Union[str, None] = '9a1f3c5e7b20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_agent_chat_link',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('chat_id', sa.String(length=50), nullable=False),
    sa.Column('tg_name', sa.String(length=255), nullable=False),
    sa.Column('code_hash', sa.String(length=64), nullable=False),
    sa.Column('code_expires_at', sa.DateTime(), nullable=True),
    sa.Column('linked_at', sa.DateTime(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('revoked_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_agent_chat_link_user_id'), 'tab_agent_chat_link', ['user_id'], unique=False)
    op.create_index(op.f('ix_tab_agent_chat_link_chat_id'), 'tab_agent_chat_link', ['chat_id'], unique=False)
    op.create_index(op.f('ix_tab_agent_chat_link_code_hash'), 'tab_agent_chat_link', ['code_hash'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_agent_chat_link_code_hash'), table_name='tab_agent_chat_link')
    op.drop_index(op.f('ix_tab_agent_chat_link_chat_id'), table_name='tab_agent_chat_link')
    op.drop_index(op.f('ix_tab_agent_chat_link_user_id'), table_name='tab_agent_chat_link')
    op.drop_table('tab_agent_chat_link')
