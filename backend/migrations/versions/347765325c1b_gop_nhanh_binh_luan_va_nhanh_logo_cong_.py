"""gop nhanh binh luan va nhanh logo cong ty

Revision ID: 347765325c1b
Revises: 54409d230b95, 9b41c7e0d5a2
Create Date: 2026-08-06 08:26:26.625325
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '347765325c1b'
down_revision: Union[str, None] = ('54409d230b95', '9b41c7e0d5a2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
