"""department manager_id (trưởng bộ phận chọn cứng)

Revision ID: b2f1a9c7d3e4
Revises: 1c45703bbfd6
Create Date: 2026-07-03 08:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f1a9c7d3e4'
down_revision: Union[str, None] = '1c45703bbfd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_department', sa.Column('manager_id', sa.BigInteger(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('tab_department', 'manager_id')
