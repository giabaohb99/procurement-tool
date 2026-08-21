"""gop head CR-111 (main) vao erp-v2

Revision ID: 979479f2229d
Revises: c66984bcd932, b7c2f4e8a915
Create Date: 2026-08-21 04:48:08.577030
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '979479f2229d'
down_revision: Union[str, None] = ('c66984bcd932', 'b7c2f4e8a915')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
