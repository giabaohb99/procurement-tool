"""merge contract_type a1c7 vao head e048

Revision ID: 08d4f35a52a5
Revises: e04856157adc, a1c7e5d90f42
Create Date: 2026-08-21 07:39:22.875454
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08d4f35a52a5'
down_revision: Union[str, None] = ('e04856157adc', 'a1c7e5d90f42')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
