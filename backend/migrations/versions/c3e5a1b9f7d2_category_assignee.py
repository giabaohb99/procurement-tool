"""category_assignee (phân công NSTM theo phân loại)

Revision ID: c3e5a1b9f7d2
Revises: b2f1a9c7d3e4
Create Date: 2026-07-04 03:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3e5a1b9f7d2'
down_revision: Union[str, None] = 'b2f1a9c7d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_category_assignee',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('item_group_id', sa.BigInteger(), nullable=False),
        sa.Column('primary_employee_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('backup_employee_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_category_assignee_item_group_id'),
                    'tab_category_assignee', ['item_group_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_category_assignee_item_group_id'), table_name='tab_category_assignee')
    op.drop_table('tab_category_assignee')
