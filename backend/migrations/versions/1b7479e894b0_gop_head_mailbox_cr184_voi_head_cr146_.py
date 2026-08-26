"""gop head mailbox cr184 voi head cr146 main

Revision ID: 1b7479e894b0
Revises: 37d710c5133e, fbfb0f748739
Create Date: 2026-08-26 08:39:59.801747
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b7479e894b0'
down_revision: Union[str, None] = ('37d710c5133e', 'fbfb0f748739')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
