"""gop nhanh don gia 4 so le va lich su mua hang

Revision ID: b8a33f9d2bd3
Revises: 5b85be0c2b48, d4b9e7c1a305
Create Date: 2026-08-07 09:04:00.768305
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8a33f9d2bd3'
down_revision: Union[str, None] = ('5b85be0c2b48', 'd4b9e7c1a305')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
