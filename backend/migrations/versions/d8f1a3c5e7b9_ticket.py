"""tao bang phieu ho tro (ticket + ticket_message)

Revision ID: d8f1a3c5e7b9
Revises: c4d8f1a6b023
Create Date: 2026-08-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd8f1a3c5e7b9'
down_revision: Union[str, None] = 'c4d8f1a6b023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_ticket',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('subject', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('department', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='normal'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='open'),
        sa.Column('company_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('requester_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('assignee_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('origin_url', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tab_ticket_code', 'tab_ticket', ['code'], unique=True)
    op.create_index('ix_tab_ticket_department', 'tab_ticket', ['department'])
    op.create_index('ix_tab_ticket_priority', 'tab_ticket', ['priority'])
    op.create_index('ix_tab_ticket_status', 'tab_ticket', ['status'])
    op.create_index('ix_tab_ticket_assignee_id', 'tab_ticket', ['assignee_id'])

    op.create_table(
        'tab_ticket_message',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('ticket_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('is_staff', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tab_ticket_message_ticket_id', 'tab_ticket_message', ['ticket_id'])


def downgrade() -> None:
    op.drop_index('ix_tab_ticket_message_ticket_id', table_name='tab_ticket_message')
    op.drop_table('tab_ticket_message')
    op.drop_index('ix_tab_ticket_assignee_id', table_name='tab_ticket')
    op.drop_index('ix_tab_ticket_status', table_name='tab_ticket')
    op.drop_index('ix_tab_ticket_priority', table_name='tab_ticket')
    op.drop_index('ix_tab_ticket_department', table_name='tab_ticket')
    op.drop_index('ix_tab_ticket_code', table_name='tab_ticket')
    op.drop_table('tab_ticket')
