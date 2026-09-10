"""merge local seal_clerk status + coffee heads

Revision ID: 735068a0f19a
Revises: c7e9c0b82f02, sealclerk02a2
Create Date: 2026-09-09 09:42:39.748303
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '735068a0f19a'
down_revision: Union[str, None] = ('c7e9c0b82f02', 'sealclerk02a2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
