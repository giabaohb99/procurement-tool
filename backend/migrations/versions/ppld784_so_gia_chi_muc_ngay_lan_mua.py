"""so_gia_chi_muc_ngay_lan_mua: chi muc (price_date, doc_id, id) tren tab_product_price_ledger (duoc-CR-784)

Revision ID: ppld784
Revises: amt784
Create Date: 2026-11-25

Lich su mua hang lay gia lan co gia DAU TIEN / GAN NHAT cua ca tap ma bang `ORDER BY price_date, doc_id, id LIMIT 1` khong theo ma
(truy van con vo huong trong cau so gop). Chi muc phu hien co `ix_ppl_code_latest` bat dau bang `product_code` nen khong doc duoc theo thu
tu do — MySQL xep ca so gia hai lan (~85 ms x 2 tren 11,6 nghin dong, ty le theo kich thuoc so). Chi muc nay cho phep doc tu dau / cuoi
chi muc roi dung o dong dau tien thoa dieu kien (do: mode=code tat ca 320 ms -> 150 ms).

VIET TAY, KHONG autogenerate (repo troi ~650 dong moi lan autogenerate). Chi them chi muc, khong dung du lieu.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "ppld784"
down_revision: Union[str, None] = "amt784"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_product_price_ledger"
INDEX = "ix_ppl_date_latest"


def upgrade() -> None:
    op.create_index(INDEX, TABLE, ["price_date", "doc_id", "id"])


def downgrade() -> None:
    op.drop_index(INDEX, table_name=TABLE)
