"""pr_supplier_info (Task 4: NCC 2 cụm JSON)

Revision ID: f3a7c1e9b2d4
Revises: e8b1d3f5a7c9
Create Date: 2026-07-29 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f3a7c1e9b2d4"
down_revision: Union[str, None] = "e8b1d3f5a7c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # MySQL 8 KHÔNG cho DEFAULT '' trực tiếp trên cột TEXT -> thêm nullable, backfill rỗng, rồi NOT NULL.
    # (Backfill DỮ LIỆU NCC cũ sang cụm 'pur' nằm ở migration riêng b4d6f8a02c15 để chạy đồng nhất
    #  ở mọi môi trường, kể cả DB đã áp bản migration này từ trước khi có backfill.)
    op.add_column("tab_purchase_request",
                  sa.Column("supplier_info", sa.Text(), nullable=True))
    op.execute("UPDATE tab_purchase_request SET supplier_info = '' WHERE supplier_info IS NULL")
    op.alter_column("tab_purchase_request", "supplier_info",
                    existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    op.drop_column("tab_purchase_request", "supplier_info")
