"""merge seal_clerk + coffee_point heads (LOCAL)

Revision ID: c7e9c0b82f02
Revises: coffee1cp1a01, sealclerk01a1
Create Date: 2026-09-09 06:48:07.372073
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7e9c0b82f02'
down_revision: Union[str, None] = ('coffee1cp1a01', 'sealclerk01a1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
