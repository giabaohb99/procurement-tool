"""gop agent hub va erp v2

Migration GỘP, không đổi bảng: nối head của nhánh bot (`5c8e2a7d9f14`, liên kết Telegram)
với head của erp-v2 (`d7a3f9c2b481`, chỉ mục partner_id hải quan) sau lần gộp erp-v2 vào
`agent-hub-bac-1` ngày 24/09/2026. Thiếu nó thì `alembic upgrade head` báo nhiều head.

Revision ID: 4812d6b8d334
Revises: 5c8e2a7d9f14, d7a3f9c2b481
Create Date: 2026-09-24 09:26:14.800509
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4812d6b8d334'
down_revision: Union[str, None] = ('5c8e2a7d9f14', 'd7a3f9c2b481')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
