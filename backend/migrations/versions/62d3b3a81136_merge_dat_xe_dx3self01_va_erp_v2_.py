"""merge dat-xe dx3self01 va erp-v2 5aa663595849

Revision ID: 62d3b3a81136
Revises: dx3self01, 5aa663595849
Create Date: 2026-09-05 01:02:24.283378
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62d3b3a81136'
down_revision: Union[str, None] = ('dx3self01', '5aa663595849')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
