"""gop head nhanh bot (b7e2f4c9d1a5) va bao-CR-490 (a490b1c2d3e4) — 25/09/2026

Migration GOP, khong doi bang. Hai nhanh cung re tu e6b1d4f8a2c7: agent-hub-bac-1 them ba
migration ai-CR-057..062 (f7c2e9a1b5d4 -> a1c4e7f9b2d6 -> b7e2f4c9d1a5), erp-v2 them cot
truong phong phe duyet (a490b1c2d3e4). Dev da chay nhanh bot truoc, nen noi hai head o day.

Revision ID: c490e1f2a3b4
Revises: b7e2f4c9d1a5, a490b1c2d3e4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c490e1f2a3b4'
down_revision: Union[str, None] = ('b7e2f4c9d1a5', 'a490b1c2d3e4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
