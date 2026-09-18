"""gop head cong_no_cr414 va custom_fields_dossier

Revision ID: 9f8e7d6c5b4a
Revises: c9f4a2b7d1e5, f3b8c05a2d91
Create Date: 2026-09-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f8e7d6c5b4a'
down_revision: Union[str, None] = ('c9f4a2b7d1e5', 'f3b8c05a2d91')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
