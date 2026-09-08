"""hop nhat dat xe va cum gantt

Revision ID: 7e93b1977593
Revises: 550132b5e0e4, a9931ac87513
Create Date: 2026-08-31 01:37:18.418871
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e93b1977593'
down_revision: Union[str, None] = ('550132b5e0e4', 'a9931ac87513')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
