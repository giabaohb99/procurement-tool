"""gop head van thu f1a6c9d47b23 + CR-111 979479f2229d

Revision ID: e04856157adc
Revises: 979479f2229d, f1a6c9d47b23
Create Date: 2026-08-21 04:52:53.882297
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e04856157adc'
down_revision: Union[str, None] = ('979479f2229d', 'f1a6c9d47b23')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
