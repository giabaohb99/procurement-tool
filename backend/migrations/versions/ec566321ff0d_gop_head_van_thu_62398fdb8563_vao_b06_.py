"""gop head van thu 62398fdb8563 vao B06 b6e9c4801fa2

Revision ID: ec566321ff0d
Revises: 62398fdb8563, b6e9c4801fa2
Create Date: 2026-08-24 05:03:38.440781
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec566321ff0d'
down_revision: Union[str, None] = ('62398fdb8563', 'b6e9c4801fa2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
