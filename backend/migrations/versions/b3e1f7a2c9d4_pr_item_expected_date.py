"""them cot expected_date cho tab_purchase_request_item

Revision ID: b3e1f7a2c9d4
Revises: 17e25d31fd2f
Create Date: 2026-07-17

Thời gian dự kiến có hàng — NSTM phụ trách cập nhật; đổi giá trị đã có phải kèm lý do.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3e1f7a2c9d4"
down_revision: Union[str, None] = "17e25d31fd2f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_purchase_request_item",
                  sa.Column("expected_date", sa.String(length=10), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("tab_purchase_request_item", "expected_date")
