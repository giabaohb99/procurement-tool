"""agent hub: bang tab_agent_user_key (khoa Gemini ca nhan) + cot owner_id o tab_agent_run (ai-CR-053, D-01)

Moi nguoi dan khoa Gemini cua minh o Trang ca nhan; luot goi ghi ro khoa cua ai de tinh chi phi tung nguoi.

Revision ID: c4f8b2d6e1a3
Revises: b3e7d1a9c5f2
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c4f8b2d6e1a3'
down_revision: Union[str, None] = 'b3e7d1a9c5f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_agent_user_key',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('provider', sa.String(length=30), nullable=False),
    sa.Column('key_enc', sa.Text(), nullable=False),
    sa.Column('key_hint', sa.String(length=8), nullable=False),
    sa.Column('verified_at', sa.DateTime(), nullable=True),
    sa.Column('revoked_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_agent_user_key_user_id'), 'tab_agent_user_key', ['user_id'], unique=False)
    op.add_column('tab_agent_run', sa.Column('owner_id', sa.BigInteger(), nullable=False, server_default='0'))
    op.create_index(op.f('ix_tab_agent_run_owner_id'), 'tab_agent_run', ['owner_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_agent_run_owner_id'), table_name='tab_agent_run')
    op.drop_column('tab_agent_run', 'owner_id')
    op.drop_index(op.f('ix_tab_agent_user_key_user_id'), table_name='tab_agent_user_key')
    op.drop_table('tab_agent_user_key')
