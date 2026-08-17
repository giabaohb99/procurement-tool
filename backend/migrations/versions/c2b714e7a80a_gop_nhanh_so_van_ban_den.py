"""gop nhanh so van ban den

Revision ID: c2b714e7a80a
Revises: 89e4a53faf92, 85fd48d984db
Create Date: 2026-08-17 03:16:40.999429
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2b714e7a80a'
down_revision: Union[str, None] = ('89e4a53faf92', '85fd48d984db')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
