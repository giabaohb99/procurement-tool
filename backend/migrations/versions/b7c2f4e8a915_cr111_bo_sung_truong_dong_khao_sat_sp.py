"""CR-111: bo sung 7 truong cho dong khao sat SAN PHAM

Phieu ho tro TK20082604 ("Sua phieu khao sat - lan 2"). Bay o moi tren
`tab_survey_product_line`:

  * `invoice_name`         — Ten tren hoa don
  * `active_ingredient`    — Ham luong hoat chat
  * `last_purchase_price`  — Gia mua gan nhat  (tu dien tu Lich su mua hang)
  * `max_purchase_price`   — Gia mua max       (tu dien tu Lich su mua hang)
  * `extra_shipping_cost`  — Phi VC phat sinh den kho yeu cau
  * `shipping_policy`      — Chinh sach van chuyen
  * `debt_policy`          — Ngay cong no

`extra_shipping_cost` la cot RIENG, khong dung lai `shipping_cost` (phi van
chuyen theo bao gia) — hai khoan nay thuong luong roi nhau.

`debt_policy` dat trung ten voi cot ben dong NCC va dung chung danh sach lua
chon, de bao cao gop hai ben khoi phai anh xa ten cot.

Cot moi deu NOT NULL + default rong/0 nen 5090 dong san co tren prod khong can
don du lieu; them cot vao bang nay la thao tac nhanh (bang nho, khong khoa lau).

Revision ID: b7c2f4e8a915
Revises: c9e4b1a7d260
"""
from alembic import op
import sqlalchemy as sa

revision = "b7c2f4e8a915"
down_revision = "c9e4b1a7d260"
branch_labels = None
depends_on = None

TABLE = "tab_survey_product_line"

# (ten cot, kieu, default dang SQL) — thu tu nay cung la thu tu them cot
COLS = [
    ("invoice_name", sa.String(255), "''"),
    ("active_ingredient", sa.String(255), "''"),
    ("last_purchase_price", sa.Numeric(18, 4), "0"),
    ("max_purchase_price", sa.Numeric(18, 4), "0"),
    ("extra_shipping_cost", sa.Numeric(18, 2), "0"),
    ("shipping_policy", sa.String(255), "''"),
    ("debt_policy", sa.String(50), "''"),
]


def upgrade() -> None:
    for name, type_, default in COLS:
        op.add_column(
            TABLE,
            sa.Column(name, type_, nullable=False, server_default=sa.text(default)),
        )


def downgrade() -> None:
    for name, _type, _default in reversed(COLS):
        op.drop_column(TABLE, name)
