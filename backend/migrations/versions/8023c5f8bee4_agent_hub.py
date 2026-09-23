"""agent_hub: nam bang so cua Agent Hub (ai-CR-002)

Sinh bang autogenerate roi CAT TAY: chi giu 5 bang tab_agent_* (task, task_item, run,
message, cursor). Bo het phan lech chi muc / NOT NULL ma autogenerate nhat duoc tu
cac migration cu - khong thuoc CR nay.

Revision ID: 8023c5f8bee4
Revises: 9f8e7d6c5b4a
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '8023c5f8bee4'
down_revision: Union[str, None] = '9f8e7d6c5b4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_agent_cursor',
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('value', sa.BigInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_agent_cursor_name'), 'tab_agent_cursor', ['name'], unique=True)
    op.create_table('tab_agent_message',
    sa.Column('task_id', sa.BigInteger(), nullable=False),
    sa.Column('direction', sa.SmallInteger(), nullable=False),
    sa.Column('chat_id', sa.String(length=50), nullable=False),
    sa.Column('tg_message_id', sa.BigInteger(), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_msg_pending', 'tab_agent_message', ['direction', 'task_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_tab_agent_message_task_id'), 'tab_agent_message', ['task_id'], unique=False)
    op.create_table('tab_agent_run',
    sa.Column('task_id', sa.BigInteger(), nullable=False),
    sa.Column('stage', sa.SmallInteger(), nullable=False),
    sa.Column('provider', sa.String(length=30), nullable=False),
    sa.Column('model', sa.String(length=80), nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('finished_at', sa.DateTime(), nullable=True),
    sa.Column('duration_ms', sa.Integer(), nullable=False),
    sa.Column('input_tokens', sa.Integer(), nullable=False),
    sa.Column('output_tokens', sa.Integer(), nullable=False),
    sa.Column('cost_usd', sa.Float(), nullable=False),
    sa.Column('error', sa.Text(), nullable=False),
    sa.Column('artifact', sa.JSON(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_agent_run_task_id'), 'tab_agent_run', ['task_id'], unique=False)
    op.create_table('tab_agent_task',
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('source', sa.SmallInteger(), nullable=False),
    sa.Column('status', sa.SmallInteger(), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('plan', sa.Text(), nullable=False),
    sa.Column('plan_files', sa.JSON(), nullable=False),
    sa.Column('test_plan', sa.Text(), nullable=False),
    sa.Column('related_docs', sa.JSON(), nullable=False),
    sa.Column('questions', sa.JSON(), nullable=False),
    sa.Column('risk_level', sa.SmallInteger(), nullable=False),
    sa.Column('branch_name', sa.String(length=120), nullable=False),
    sa.Column('pr_url', sa.String(length=255), nullable=False),
    sa.Column('deployed_dev_at', sa.DateTime(), nullable=True),
    sa.Column('deployed_prod_at', sa.DateTime(), nullable=True),
    sa.Column('approved_by_chat', sa.String(length=50), nullable=False),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.Column('closed_at', sa.DateTime(), nullable=True),
    sa.Column('note', sa.Text(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_task_status_created', 'tab_agent_task', ['status', 'created_at'], unique=False)
    op.create_index(op.f('ix_tab_agent_task_code'), 'tab_agent_task', ['code'], unique=True)
    op.create_table('tab_agent_task_item',
    sa.Column('task_id', sa.BigInteger(), nullable=False),
    sa.Column('source', sa.SmallInteger(), nullable=False),
    sa.Column('ref_id', sa.BigInteger(), nullable=False),
    sa.Column('merged_by', sa.SmallInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_agent_task_item_task_id'), 'tab_agent_task_item', ['task_id'], unique=False)
    op.create_index('uq_agent_task_item_ref', 'tab_agent_task_item', ['source', 'ref_id'], unique=True)


def downgrade() -> None:
    op.drop_table('tab_agent_task_item')
    op.drop_table('tab_agent_task')
    op.drop_table('tab_agent_run')
    op.drop_table('tab_agent_message')
    op.drop_table('tab_agent_cursor')
