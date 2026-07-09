"""pr_soft_delete

Revision ID: 051f616d12bc
Revises: b2e5f9c3a7d4
Create Date: 2026-07-09 04:50:27.981517
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '051f616d12bc'
down_revision: Union[str, None] = 'b2e5f9c3a7d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_purchase_request', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade() -> None:
    op.drop_column('tab_purchase_request', 'is_deleted')
