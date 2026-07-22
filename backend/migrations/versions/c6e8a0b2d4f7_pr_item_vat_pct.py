"""them vat_pct (% VAT theo dong) vao tab_purchase_request_item

Revision ID: c6e8a0b2d4f7
Revises: b4d6f8a0c2e5
Create Date: 2026-07-22

Task 4 (CR-007): them lai VAT vao PYC — % VAT theo tung dong, thanh tien gom VAT.
Row cu vat_pct=0 -> amount = qty*price khong doi (giu nguyen du lieu).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c6e8a0b2d4f7"
down_revision: Union[str, None] = "b4d6f8a0c2e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_purchase_request_item",
                  sa.Column("vat_pct", sa.Numeric(5, 2), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("tab_purchase_request_item", "vat_pct")
