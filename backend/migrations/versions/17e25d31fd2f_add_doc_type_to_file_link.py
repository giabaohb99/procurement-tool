"""add doc_type to file_link

Revision ID: 17e25d31fd2f
Revises: c7d8e9f0a1b2
Create Date: 2026-07-17 03:04:32.179791
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '17e25d31fd2f'
down_revision: Union[str, None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Only add the doc_type column to tab_file_link (unrelated schema-drift produced by
    # autogenerate was stripped out). server_default='' so existing rows do not break NOT NULL.
    op.add_column('tab_file_link', sa.Column('doc_type', sa.String(length=50),
                  nullable=False, server_default=''))
    op.create_index(op.f('ix_tab_file_link_doc_type'), 'tab_file_link', ['doc_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_file_link_doc_type'), table_name='tab_file_link')
    op.drop_column('tab_file_link', 'doc_type')
