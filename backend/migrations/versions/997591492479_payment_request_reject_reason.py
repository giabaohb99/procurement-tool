"""payment_request_reject_reason

Revision ID: 997591492479
Revises: f2c9a4e1b7d3
Create Date: 2026-07-14 04:50:33.739009
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '997591492479'
down_revision: Union[str, None] = 'f2c9a4e1b7d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_payment_request', sa.Column('reject_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('tab_payment_request', 'reject_reason')
