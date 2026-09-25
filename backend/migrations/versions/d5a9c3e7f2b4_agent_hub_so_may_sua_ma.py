"""agent hub: bang tab_agent_runner (so may sua ma) + cot runner_id o tab_agent_task (ai-CR-054, D-03)

May sua ma tach roi: dai ca dang ky may bang cau nhan, moi may mot hang doi rieng, viec dinh may.

Revision ID: d5a9c3e7f2b4
Revises: c4f8b2d6e1a3
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd5a9c3e7f2b4'
down_revision: Union[str, None] = 'c4f8b2d6e1a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_agent_runner',
    sa.Column('name', sa.String(length=40), nullable=False),
    sa.Column('owner_user_id', sa.BigInteger(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('can_deploy', sa.Boolean(), nullable=False),
    sa.Column('note', sa.String(length=255), nullable=False),
    sa.Column('version', sa.String(length=50), nullable=False),
    sa.Column('registered_by_chat', sa.String(length=50), nullable=False),
    sa.Column('last_seen_at', sa.DateTime(), nullable=True),
    sa.Column('revoked_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_agent_runner_name'), 'tab_agent_runner', ['name'], unique=False)
    op.create_index(op.f('ix_tab_agent_runner_owner_user_id'), 'tab_agent_runner', ['owner_user_id'], unique=False)
    op.add_column('tab_agent_task', sa.Column('runner_id', sa.BigInteger(), nullable=False, server_default='0'))
    op.create_index(op.f('ix_tab_agent_task_runner_id'), 'tab_agent_task', ['runner_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_agent_task_runner_id'), table_name='tab_agent_task')
    op.drop_column('tab_agent_task', 'runner_id')
    op.drop_index(op.f('ix_tab_agent_runner_owner_user_id'), table_name='tab_agent_runner')
    op.drop_index(op.f('ix_tab_agent_runner_name'), table_name='tab_agent_runner')
    op.drop_table('tab_agent_runner')
