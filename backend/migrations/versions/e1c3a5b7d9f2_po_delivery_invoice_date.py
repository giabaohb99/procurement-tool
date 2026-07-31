"""po_delivery_invoice_date — thêm Ngày hóa đơn cho LẦN GIAO (Task: dời số/ngày HĐ về giao hàng)

Số hóa đơn + Ngày hóa đơn nay nhập theo TỪNG LẦN GIAO (tab_po_delivery), không còn
theo dòng sản phẩm (tab_po_item). invoice_no đã có sẵn; migration này bổ sung
invoice_date. VARCHAR nên DEFAULT '' hợp lệ ở cả MySQL 8 (dev) lẫn MariaDB (VPS).

Idempotent: chỉ thêm cột nếu chưa tồn tại (local đã có cột do create_all/ALTER tay).

Revision ID: e1c3a5b7d9f2
Revises: a7b1c2d3e4f5
Create Date: 2026-07-31 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e1c3a5b7d9f2"
down_revision: Union[str, None] = "a7b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if not _has_column("tab_po_delivery", "invoice_date"):
        op.add_column("tab_po_delivery",
                      sa.Column("invoice_date", sa.String(length=10), nullable=False, server_default=""))


def downgrade() -> None:
    if _has_column("tab_po_delivery", "invoice_date"):
        op.drop_column("tab_po_delivery", "invoice_date")
