"""bao-CR-319 - nen tien te + loai don (don hang nhap khau), phase P1 + P2

P1 - NEN TIEN TE. Tu truoc toi nay moi con so tien trong he deu ngam hieu la VND, khong
cot nao ghi lai la tien gi. Don nhap khau mua bang ngoai te nen phai co cho ghi loai tien
va ty gia. Dat o CA HAI cap:
  - Don (`tab_purchase_order`): loai tien + ty gia MAC DINH, dong hang moi chep xuong.
  - Dong hang (`tab_po_item`): loai tien + ty gia THUC SU dung de quy doi, vi mot don
    van co the lan dong VND (vi du phi noi dia tra bang tien Viet).
`price` va `amount` cua dong hang giu nghia NGUYEN TE; `base_amount` la ban QUY DOI cho
cong no / ton kho / bao cao doc. KHONG dat ten cot kieu `amount_vnd` - khoa cung mot loai
tien la sai huong ngay tu ten cot.

Them `weight_kg` + `dimension` cho dong hang: hai so nay la can cu chia chi phi lo hang
theo khoi luong o phase sau, khong phai o trang tri.

P2 - LOAI DON. `order_type` la cot MOI nen luu SMALLINT theo luat R2/QD-11 (1 = trong nuoc,
2 = nhap khau), kem so + ngay to khai hai quan.

An toan voi du lieu cu: moi dong hien co nhan ty gia 1 va loai tien VND, `base_amount`
duoc backfill bang dung `amount`, `order_type` = 1. Nghia la khong mot con so nao dang
chay bi doi sau khi nang cap.

Revision ID: c5a81b3f6d24
Revises: a7c3e91f5b28
Create Date: 2026-09-08
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c5a81b3f6d24"
down_revision: Union[str, None] = "a7c3e91f5b28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_CURRENCY = "VND"


def upgrade() -> None:
    # --- P2: loai don + to khai hai quan (header) ---
    op.add_column("tab_purchase_order", sa.Column(
        "order_type", sa.SmallInteger(), nullable=False, server_default="1"))
    op.create_index("ix_tab_purchase_order_order_type", "tab_purchase_order", ["order_type"])
    op.add_column("tab_purchase_order", sa.Column(
        "customs_decl_no", sa.String(length=50), nullable=False, server_default=""))
    op.add_column("tab_purchase_order", sa.Column(
        "customs_decl_date", sa.String(length=10), nullable=False, server_default=""))

    # --- P1: tien te (header) ---
    op.add_column("tab_purchase_order", sa.Column(
        "currency", sa.String(length=10), nullable=False, server_default=DEFAULT_CURRENCY))
    op.add_column("tab_purchase_order", sa.Column(
        "exchange_rate", sa.Numeric(18, 6), nullable=False, server_default="1"))

    # --- P1: tien te + khoi luong (dong hang) ---
    op.add_column("tab_po_item", sa.Column(
        "currency", sa.String(length=10), nullable=False, server_default=DEFAULT_CURRENCY))
    op.add_column("tab_po_item", sa.Column(
        "exchange_rate", sa.Numeric(18, 6), nullable=False, server_default="1"))
    op.add_column("tab_po_item", sa.Column(
        "base_amount", sa.Numeric(18, 2), nullable=False, server_default="0"))
    op.add_column("tab_po_item", sa.Column(
        "weight_kg", sa.Numeric(18, 3), nullable=False, server_default="0"))
    op.add_column("tab_po_item", sa.Column(
        "dimension", sa.String(length=100), nullable=False, server_default=""))

    # Backfill: dong cu deu la VND ty gia 1 nen so quy doi bang dung so nguyen te.
    # Khong lam buoc nay thi mau bao cao doc `base_amount` se thay 0 dong cho toan bo
    # lich su mua hang cho toi luc don do duoc luu lai lan nua.
    op.execute("UPDATE tab_po_item SET base_amount = amount")


def downgrade() -> None:
    op.drop_column("tab_po_item", "dimension")
    op.drop_column("tab_po_item", "weight_kg")
    op.drop_column("tab_po_item", "base_amount")
    op.drop_column("tab_po_item", "exchange_rate")
    op.drop_column("tab_po_item", "currency")
    op.drop_column("tab_purchase_order", "exchange_rate")
    op.drop_column("tab_purchase_order", "currency")
    op.drop_column("tab_purchase_order", "customs_decl_date")
    op.drop_column("tab_purchase_order", "customs_decl_no")
    op.drop_index("ix_tab_purchase_order_order_type", table_name="tab_purchase_order")
    op.drop_column("tab_purchase_order", "order_type")
