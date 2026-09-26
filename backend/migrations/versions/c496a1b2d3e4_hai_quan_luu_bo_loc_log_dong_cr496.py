"""bao-CR-496: luu bo loc rieng tung nguoi + ket cuc tung dong khi nap (Tra cuu gia hai quan)

- tab_customs_saved_filter: bo loc nguoi dung dat ten, rieng tung TAI KHOAN (user_id), cot
  is_shared co san mac dinh tat de sau mo bo loc chung; params giu nguyen chuoi tham so URL.
- tab_import_log.row_status (SMALLINT, ImportRowStatus: 0 dong nhat ky thuong · 1 Them moi ·
  2 Loi · 3 Trung trong lo) + chi muc (batch_id, row_status) de dem / loc tung lo.

Revision ID: c496a1b2d3e4
Revises: b494c1d2e3f4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c496a1b2d3e4'
down_revision: Union[str, None] = 'b494c1d2e3f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_customs_saved_filter',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('name', sa.String(120), nullable=False, server_default=''),
        sa.Column('params', sa.Text(), nullable=False),
        sa.Column('is_shared', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by', sa.BigInteger(), server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_by', sa.BigInteger(), server_default='0'),
    )
    op.create_index('ix_customs_saved_filter_user', 'tab_customs_saved_filter', ['user_id', 'name'])

    op.add_column('tab_import_log',
                  sa.Column('row_status', sa.SmallInteger(), nullable=False, server_default='0'))
    op.create_index('ix_import_log_batch_row_status', 'tab_import_log', ['batch_id', 'row_status'])


def downgrade() -> None:
    op.drop_index('ix_import_log_batch_row_status', table_name='tab_import_log')
    op.drop_column('tab_import_log', 'row_status')
    op.drop_index('ix_customs_saved_filter_user', table_name='tab_customs_saved_filter')
    op.drop_table('tab_customs_saved_filter')
