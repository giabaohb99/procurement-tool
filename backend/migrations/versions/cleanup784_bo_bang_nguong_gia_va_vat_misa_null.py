"""bo_bang_nguong_gia_va_vat_misa_null: bo `tab_product_price_limit`, VAT dong Misa = NULL (duoc-CR-784, phase 04)

Revision ID: cleanup784
Revises: quotesrc784
Create Date: 2026-11-25

Chu du an chot 25/11/2026:
  C6 - BO HAN bang nguong san / tran (dang tat o ca hai giao dien tu 21/11, 0 dong): bang, API `/api/product-price-limits`,
       canh bao 6 / 7, cot Excel, truong cong cu Tro ly deu bo. Min / max tu tinh tu so gia GIU NGUYEN (khong lien quan bang nay).
  C7 = A - VAT cua dong so gia Misa (`source_type = 3`) la NULL = khong biet (so chi tiet mua hang Misa khong co VAT; truoc day ghi 0,
       de nhin nhu "0%"). Giao dien hien trong; khong cho nao tinh toan tren VAT cua so gia.

upgrade:
  1. DROP `tab_product_price_limit` (in so dong bi bo neu co - du lieu ngong khong con noi nao dung);
  2. `tab_product_price_ledger.vat` cho phep NULL;  3. dong Misa: `vat = NULL`.
downgrade (dung nguoc, dung nhu truoc phase nay): dong `vat IS NULL` -> 0 roi NOT NULL (mat phan biet "khong biet" / 0%);
  dung lai `tab_product_price_limit` RONG, dung cau truc cu cua `pkgcost784` (khong khoi phuc duoc dong da bo).

VIET TAY, KHONG autogenerate (repo troi ~650 dong moi lan autogenerate). Chay duoc tren MySQL 8 va SQLite (bai kiem).
`synced_at` khong doi o CSDL (da la `DEFAULT CURRENT_TIMESTAMP`): phase nay chi bo `default=datetime.utcnow` phia ORM.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "cleanup784"
down_revision: Union[str, None] = "quotesrc784"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LIMIT = "tab_product_price_limit"
LEDGER = "tab_product_price_ledger"
MISA_SOURCE_TYPE = 3          # PriceSourceType.MISA - chep tay (migration phai dung yen theo thoi gian)


def _audit_columns() -> list[sa.Column]:
    """Cot chuan cua AuditMixin (id + 4 cot kiem toan) — y het `pkgcost784`."""
    return [
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
    ]


def upgrade() -> None:
    conn = op.get_bind()
    if sa.inspect(conn).has_table(LIMIT):
        dropped = conn.execute(sa.text(f"SELECT COUNT(*) FROM {LIMIT}")).scalar() or 0
        op.drop_table(LIMIT)
        print(f"[cleanup784] bo bang {LIMIT} ({dropped} dong nguong bi bo)")
    with op.batch_alter_table(LEDGER) as batch:     # batch: SQLite dung lai bang, MySQL chay ALTER thuong
        #  Bỏ luôn mặc định 0 của CSDL: cột cho phép NULL = "không biết", ghi thiếu `vat` không được tự thành 0%.
        batch.alter_column("vat", existing_type=sa.Numeric(5, 2), nullable=True, existing_nullable=False,
                           existing_server_default=sa.text("0"), server_default=None)
    misa = conn.execute(sa.text(f"UPDATE {LEDGER} SET vat = NULL WHERE source_type = :t"), {"t": MISA_SOURCE_TYPE}).rowcount
    print(f"[cleanup784] VAT dong Misa -> NULL: {misa} dong")


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(f"UPDATE {LEDGER} SET vat = 0 WHERE vat IS NULL"))
    with op.batch_alter_table(LEDGER) as batch:
        batch.alter_column("vat", existing_type=sa.Numeric(5, 2), nullable=False, existing_nullable=True,
                           server_default=sa.text("0"))
    if not sa.inspect(conn).has_table(LIMIT):
        op.create_table(
            LIMIT,
            *_audit_columns(),
            sa.Column("product_code", sa.String(50), nullable=False),
            sa.Column("floor_price", sa.Numeric(18, 4), nullable=True),
            sa.Column("ceiling_price", sa.Numeric(18, 4), nullable=True),
            sa.Column("note", sa.String(500), nullable=False, server_default=""),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("product_code", name="uq_tab_product_price_limit_product_code"),
        )
