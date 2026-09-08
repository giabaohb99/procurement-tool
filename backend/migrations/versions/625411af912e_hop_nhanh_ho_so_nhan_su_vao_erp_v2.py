"""hop nhanh ho so nhan su vao erp-v2

Revision ID: 625411af912e
Revises: 32e30ac28788, c5e2a8b31d47
Create Date: 2026-09-08 08:57:02.213712
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '625411af912e'
down_revision: Union[str, None] = ('32e30ac28788', 'c5e2a8b31d47')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
