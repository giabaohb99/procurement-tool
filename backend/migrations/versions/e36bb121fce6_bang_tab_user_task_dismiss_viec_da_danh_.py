"""bang tab_user_task_dismiss viec da danh dau xong CR-215

Bang luu task_key ma tung tai khoan da "Danh dau lam xong" o tab Viec can lam
— chuong canh bao (/api/alerts) va /api/dashboard/tasks cung doc de an dong do.

Autogenerate keo theo nhieu alter_column drift khong lien quan (ticket, backup,
survey_request...) — da cat bo, chi giu bang moi.

Revision ID: e36bb121fce6
Revises: c7e2a9f4d1b3
Create Date: 2026-08-28 02:45:38.796972
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e36bb121fce6'
down_revision: Union[str, None] = 'c7e2a9f4d1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_user_task_dismiss',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('task_key', sa.String(length=64), nullable=False),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'task_key', name='uq_user_task_key'),
    )
    op.create_index(op.f('ix_tab_user_task_dismiss_user_id'), 'tab_user_task_dismiss', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_user_task_dismiss_user_id'), table_name='tab_user_task_dismiss')
    op.drop_table('tab_user_task_dismiss')
