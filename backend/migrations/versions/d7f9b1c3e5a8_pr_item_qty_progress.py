"""them qty_ordered/qty_received (tien do SL) vao tab_purchase_request_item

Revision ID: d7f9b1c3e5a8
Revises: c6e8a0b2d4f7
Create Date: 2026-07-22

CR-007 #3: cot "Tien do" tren YCMH — tong SL da dat / tong SL da nhan,
dong bo tu cac dong DMH lien ket (sync_from_purchase_orders). Row cu = 0.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d7f9b1c3e5a8"
down_revision: Union[str, None] = "c6e8a0b2d4f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_purchase_request_item",
                  sa.Column("qty_ordered", sa.Numeric(18, 3), nullable=False, server_default="0"))
    op.add_column("tab_purchase_request_item",
                  sa.Column("qty_received", sa.Numeric(18, 3), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("tab_purchase_request_item", "qty_received")
    op.drop_column("tab_purchase_request_item", "qty_ordered")
