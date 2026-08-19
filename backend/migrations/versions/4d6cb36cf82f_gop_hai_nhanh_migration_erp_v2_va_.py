"""gop hai nhanh migration erp-v2 va pltgiang

Revision ID: 4d6cb36cf82f
Revises: 9fd918454b1e, cc503d81a047
Create Date: 2026-08-19 07:22:15.237942
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d6cb36cf82f'
down_revision: Union[str, None] = ('9fd918454b1e', 'cc503d81a047')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
