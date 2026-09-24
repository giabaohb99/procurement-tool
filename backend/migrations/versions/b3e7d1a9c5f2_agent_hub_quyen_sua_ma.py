"""agent hub: bang tab_agent_grant — ai duoc ra lenh sua ma qua bot, cap nao (ai-CR-051, K-01)

Dai ca cap bang cau nhan tren Telegram; bot ghi so. Chi bang cua bot, khong dung bang ERP.

Revision ID: b3e7d1a9c5f2
Revises: 4812d6b8d334
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b3e7d1a9c5f2'
down_revision: Union[str, None] = '4812d6b8d334'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_agent_grant',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('level', sa.SmallInteger(), nullable=False),
    sa.Column('granted_by_chat', sa.String(length=50), nullable=False),
    sa.Column('note', sa.String(length=255), nullable=False),
    sa.Column('revoked_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_agent_grant_user_id'), 'tab_agent_grant', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_agent_grant_user_id'), table_name='tab_agent_grant')
    op.drop_table('tab_agent_grant')
