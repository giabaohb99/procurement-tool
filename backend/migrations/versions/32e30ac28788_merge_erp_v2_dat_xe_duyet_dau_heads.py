"""merge erp-v2 + dat-xe/duyet-dau heads

Revision ID: 32e30ac28788
Revises: 6835fb9cfecd, b3f4a1c2d5e6
Create Date: 2026-09-08 03:27:34.542486
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32e30ac28788'
down_revision: Union[str, None] = ('6835fb9cfecd', 'b3f4a1c2d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
