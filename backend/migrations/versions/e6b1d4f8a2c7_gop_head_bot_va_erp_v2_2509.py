"""gop head nhanh bot va erp-v2 (25/09/2026)

Migration GOP, khong doi bang: noi head cua nhanh bot (`d5a9c3e7f2b4`, so may sua ma) voi head
cua erp-v2 (`0ddb3327bc42`, gop thu muc van ban + CR-470) sau lan gop origin/erp-v2 vao
agent-hub-bac-1 ngay 25/09/2026. Thieu no thi `alembic upgrade head` bao nhieu head.

Revision ID: e6b1d4f8a2c7
Revises: d5a9c3e7f2b4, 0ddb3327bc42
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6b1d4f8a2c7'
down_revision: Union[str, None] = ('d5a9c3e7f2b4', '0ddb3327bc42')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
