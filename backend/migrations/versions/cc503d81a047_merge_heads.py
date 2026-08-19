"""merge_heads

Revision ID: cc503d81a047
Revises: 020dab131963, d5b2f9c31a08
Create Date: 2026-08-19 04:52:56.186697
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc503d81a047'
down_revision: Union[str, None] = ('020dab131963', 'd5b2f9c31a08')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
