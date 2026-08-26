"""them tab_export_log

Revision ID: 16a85b39ddcf
Revises: 1b7479e894b0
Create Date: 2026-08-26 01:19:30.933350

Chỉ THÊM bảng nhật ký Xuất dữ liệu (Đ-13b). Các alter_column/drop_index mà
autogenerate bắt thêm là DRIFT của bảng khác — cố ý bỏ hết, không đụng.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '16a85b39ddcf'
down_revision: Union[str, None] = '1b7479e894b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_export_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('entity', sa.String(length=50), nullable=False),
        sa.Column('fmt', sa.String(length=10), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
        sa.Column('filter_summary', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_export_log_entity'), 'tab_export_log', ['entity'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_export_log_entity'), table_name='tab_export_log')
    op.drop_table('tab_export_log')
