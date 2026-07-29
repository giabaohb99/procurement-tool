"""po_item_invoice_date — thêm Ngày hóa đơn cho dòng đơn mua hàng (Task 1)

Ngày hóa đơn (invoice_date) tự set = hôm nay khi nhập Số hóa đơn (backend service),
vẫn sửa tay được. VARCHAR nên DEFAULT '' hợp lệ ở cả MySQL 8 (dev) lẫn MariaDB (VPS).

Revision ID: c5e7092b1d46
Revises: b4d6f8a02c15
Create Date: 2026-07-29 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c5e7092b1d46"
down_revision: Union[str, None] = "b4d6f8a02c15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_po_item",
                  sa.Column("invoice_date", sa.String(length=10), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("tab_po_item", "invoice_date")
