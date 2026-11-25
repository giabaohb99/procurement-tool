"""so_gia_them_cot_thanh_tien: cot amount (thanh tien Misa) tren tab_product_price_ledger (duoc-CR-784)

Revision ID: amt784
Revises: misa784
Create Date: 2026-11-25

Lich su mua hang can hien "Gia tri mua" dung bang cot "Gia tri" cua so chi tiet mua hang Misa (VD dong 2326 NHG3790 18/08/2025:
7.121.169 chu khong phai 9.204 x 773,7 = 7.121.134,8). So gia truoc day khong luu thanh tien nen them mot cot:

  - `amount` DECIMAL(18,2) NULL — VND, chua VAT. NULL = chua co -> man hinh dung gia x so luong.

VIET TAY, KHONG autogenerate (repo troi ~650 dong moi lan autogenerate). Chi them cot NULL, khong dung du lieu:
dien `amount` cho dong da co bang `scripts/backfill_product_price_ledger.py --apply` (nguon 1) va nap lai tep Excel so Misa (nguon 3).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "amt784"
down_revision: Union[str, None] = "misa784"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_product_price_ledger"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("amount", sa.Numeric(18, 2), nullable=True))


def downgrade() -> None:
    op.drop_column(TABLE, "amount")
