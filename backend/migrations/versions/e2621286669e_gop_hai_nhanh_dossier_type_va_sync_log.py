"""gop hai nhanh dossier_type va sync_log

Revision ID: e2621286669e
Revises: e4b7bc674d61, e5a1b9c73d04
Create Date: 2026-09-17 01:42:58.077768
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2621286669e'
down_revision: Union[str, None] = ('e4b7bc674d61', 'e5a1b9c73d04')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
