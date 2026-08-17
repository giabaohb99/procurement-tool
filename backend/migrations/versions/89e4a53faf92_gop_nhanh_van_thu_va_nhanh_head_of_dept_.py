"""gop nhanh van thu va nhanh head_of_dept_id

Revision ID: 89e4a53faf92
Revises: a1c7f4d92e63, b62f3c8d1a04
Create Date: 2026-08-15 08:07:23.902640
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89e4a53faf92'
down_revision: Union[str, None] = ('a1c7f4d92e63', 'b62f3c8d1a04')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
