"""nguon_so_misa_ten_ncc: cot ten nha cung cap + ten kho tren so gia + chi muc phu them nguon (duoc-CR-784)

Revision ID: misa784
Revises: pkgcost784
Create Date: 2026-11-23

Nap tam so chi tiet mua hang Misa vao so gia (`PriceSourceType.MISA = 3`, script `scripts/import_misa_price_ledger.py`):
  1. them cot `tab_product_price_ledger.supplier_name` (NULL) — ma NCC cua Misa (NCC0019, NCC116...) khong nam trong
     `tab_supplier` nen ten phai di theo dong;
  2. them cot `tab_product_price_ledger.warehouse_name` (NULL) — ten kho nhap hang (Misa co cot kho; nguon 1 / 2 tra tu ma kho);
  3. dung lai chi muc phu `ix_ppl_code_latest` them cot cuoi `source_type` de dieu kien moc cat Misa (`misa_cutoff.py`) cung doc
     duoc tu chi muc, khong phai chay ve bang.

VIET TAY, KHONG autogenerate (repo troi ~650 dong moi lan autogenerate). Khong dung du lieu: chi them cot NULL + dung lai chi muc.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "misa784"
down_revision: Union[str, None] = "pkgcost784"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_product_price_ledger"
INDEX = "ix_ppl_code_latest"
OLD_COLUMNS = ["product_code", "price_date", "doc_id", "id", "price", "company_id"]


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("supplier_name", sa.String(200), nullable=True))
    op.add_column(TABLE, sa.Column("warehouse_name", sa.String(200), nullable=True))
    op.drop_index(INDEX, table_name=TABLE)
    op.create_index(INDEX, TABLE, [*OLD_COLUMNS, "source_type"])


def downgrade() -> None:
    op.drop_index(INDEX, table_name=TABLE)
    op.create_index(INDEX, TABLE, OLD_COLUMNS)
    op.drop_column(TABLE, "warehouse_name")
    op.drop_column(TABLE, "supplier_name")
