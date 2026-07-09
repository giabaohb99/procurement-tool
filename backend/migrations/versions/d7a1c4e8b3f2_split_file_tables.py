"""Tách đính kèm thành tab_file + tab_file_link, bỏ tab_attachment

Revision ID: d7a1c4e8b3f2
Revises: 051f616d12bc
Create Date: 2026-07-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd7a1c4e8b3f2'
down_revision: Union[str, None] = '051f616d12bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_cols():
    return [
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_by', sa.BigInteger(), nullable=False, server_default='0'),
    ]


def upgrade() -> None:
    op.create_table(
        'tab_file',
        *_audit_cols(),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_key', sa.String(length=500), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False, server_default=''),
        sa.Column('content_type', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('size', sa.BigInteger(), nullable=False, server_default='0'),
    )
    op.create_table(
        'tab_file_link',
        *_audit_cols(),
        sa.Column('file_id', sa.BigInteger(), nullable=False),
        sa.Column('entity', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.BigInteger(), nullable=False),
        sa.Column('purchase_order_id', sa.BigInteger(), nullable=False, server_default='0'),
    )
    op.create_index('ix_tab_file_link_file_id', 'tab_file_link', ['file_id'])
    op.create_index('ix_tab_file_link_entity', 'tab_file_link', ['entity'])
    op.create_index('ix_tab_file_link_entity_id', 'tab_file_link', ['entity_id'])
    # Clear đính kèm cũ (theo yêu cầu) — bỏ bảng tab_attachment
    op.drop_table('tab_attachment')


def downgrade() -> None:
    op.create_table(
        'tab_attachment',
        *_audit_cols(),
        sa.Column('entity', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.BigInteger(), nullable=False),
        sa.Column('purchase_order_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_key', sa.String(length=500), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False, server_default=''),
        sa.Column('content_type', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('size', sa.BigInteger(), nullable=False, server_default='0'),
    )
    op.drop_table('tab_file_link')
    op.drop_table('tab_file')
