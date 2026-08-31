"""hop nhat dat_xe va tag_custom_field

Revision ID: 550132b5e0e4
Revises: c8a1d4f60b72, fbccaf4e4e31
Create Date: 2026-08-29 05:29:44.376650
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '550132b5e0e4'
down_revision: Union[str, None] = ('c8a1d4f60b72', 'fbccaf4e4e31')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
