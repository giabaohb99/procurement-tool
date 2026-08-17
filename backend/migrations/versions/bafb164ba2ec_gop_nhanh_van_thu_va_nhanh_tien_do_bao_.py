"""gop nhanh van thu va nhanh tien do bao gia

Revision ID: bafb164ba2ec
Revises: c2b714e7a80a, 4b6d2f0a97c5
Create Date: 2026-08-17 04:16:34.761739
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bafb164ba2ec'
down_revision: Union[str, None] = ('c2b714e7a80a', '4b6d2f0a97c5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
