"""gop head cr146 main vao erp-v2

Revision ID: 37d710c5133e
Revises: c5bf3dae51db, d9c4b7a2e510
Create Date: 2026-08-26 08:32:12.876736
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37d710c5133e'
down_revision: Union[str, None] = ('c5bf3dae51db', 'd9c4b7a2e510')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
