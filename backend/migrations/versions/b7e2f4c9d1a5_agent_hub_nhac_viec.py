"""agent hub: bang tab_agent_reminder — nhac viec bang cau noi (ai-CR-060, T-10)

Revision ID: b7e2f4c9d1a5
Revises: a1c4e7f9b2d6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7e2f4c9d1a5'
down_revision: Union[str, None] = 'a1c4e7f9b2d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_agent_reminder',
    sa.Column('chat_id', sa.String(length=50), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(length=500), nullable=False),
    sa.Column('due_at', sa.DateTime(), nullable=True),
    sa.Column('sent_at', sa.DateTime(), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_agent_reminder_chat_id'), 'tab_agent_reminder', ['chat_id'], unique=False)
    op.create_index(op.f('ix_tab_agent_reminder_user_id'), 'tab_agent_reminder', ['user_id'], unique=False)
    op.create_index(op.f('ix_tab_agent_reminder_due_at'), 'tab_agent_reminder', ['due_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_agent_reminder_due_at'), table_name='tab_agent_reminder')
    op.drop_index(op.f('ix_tab_agent_reminder_user_id'), table_name='tab_agent_reminder')
    op.drop_index(op.f('ix_tab_agent_reminder_chat_id'), table_name='tab_agent_reminder')
    op.drop_table('tab_agent_reminder')
