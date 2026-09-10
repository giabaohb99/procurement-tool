"""merge erp-v2 va pltgiang heads (seal_clerk/coffee_point)

Revision ID: bee157de2ec8
Revises: 735068a0f19a, a7c5e91d3b04
Create Date: 2026-09-10 09:56:36.431804
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bee157de2ec8'
down_revision: Union[str, None] = ('735068a0f19a', 'a7c5e91d3b04')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
