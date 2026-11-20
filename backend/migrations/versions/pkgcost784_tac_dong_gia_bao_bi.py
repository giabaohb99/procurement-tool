"""tac_dong_gia_bao_bi: so gia + bao gia + nguong gia + dinh muc bao bi (duoc-CR-784)

Revision ID: pkgcost784
Revises: mrg761a
Create Date: 2026-11-20

Bon bang moi, KHONG sua cot bang cu: `tab_product_price_ledger` (so gia da giao dich, dan xuat — dung lai duoc bang
`scripts/backfill_product_price_ledger.py`), `tab_product_price_quote` (bao gia), `tab_product_price_limit` (nguong
san / tran, mot dong moi ma) va `tab_packaging_bom` (dinh muc bao bi theo ma hang hoa). Thiet ke:
`doc/erp/thu-mua/plans/261120-tac-dong-gia-bao-bi/phase-01-be-mo-hinh-du-lieu-migration-quyen.md`.

VIET TAY, KHONG autogenerate: repo nay troi ~650 dong moi lan autogenerate (NOT NULL created_at/updated_at cua hai chuc
bang + doi ten chi muc), nen chi khai dung bon bang cua CR nay + chi muc cua chung. Noi bang bang CHUOI `product_code`
(khong ForeignKey thuc) theo quy uoc repo (`mo-hinh-du-lieu-san-pham.md` §2).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "pkgcost784"
down_revision: Union[str, None] = "mrg761a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    """Cot chuan cua AuditMixin (id + 4 cot kiem toan)."""
    return [
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
    ]


def upgrade() -> None:
    op.create_table(
        "tab_product_price_ledger",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_type", sa.SmallInteger(), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("doc_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("product_code", sa.String(50), nullable=False),
        sa.Column("supplier_code", sa.String(50), nullable=False, server_default=""),
        sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("vat", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("qty", sa.Numeric(18, 3), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(25), nullable=False, server_default=""),
        sa.Column("synced_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_type", "source_id", name="uq_ppl_source"),
    )
    op.create_index("ix_tab_product_price_ledger_doc_id", "tab_product_price_ledger", ["doc_id"])
    # Chỉ mục PHỦ (đo trên sổ 650 nghìn dòng, `backend/app/modules/product_price/latest_priced_query.py`): đúng thứ tự "lần mua gần
    # nhất" (ngày, doc_id, id) + `price` + `company_id` nên điều kiện giá > 0 / phạm vi pháp nhân và truy vấn gộp theo mã chỉ đọc
    # chỉ mục, không chạm bảng. Một chỉ mục thay hai cái cũ `(mã, ngày, id)` — tiền tố `(mã, ngày)` vẫn phục vụ tra cứu theo mã.
    op.create_index("ix_ppl_code_latest", "tab_product_price_ledger",
                    ["product_code", "price_date", "doc_id", "id", "price", "company_id"])

    op.create_table(
        "tab_product_price_quote",
        *_audit_columns(),
        sa.Column("product_code", sa.String(50), nullable=False),
        sa.Column("supplier_code", sa.String(50), nullable=False, server_default=""),
        sa.Column("price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("vat", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ppq_code_from", "tab_product_price_quote", ["product_code", "valid_from", "id"])

    op.create_table(
        "tab_product_price_limit",
        *_audit_columns(),
        sa.Column("product_code", sa.String(50), nullable=False),
        sa.Column("floor_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("ceiling_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_code", name="uq_tab_product_price_limit_product_code"),
    )

    op.create_table(
        "tab_packaging_bom",
        *_audit_columns(),
        sa.Column("hh_code", sa.String(50), nullable=False),
        sa.Column("hh_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("legal_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("bottle_code", sa.String(50), nullable=False, server_default=""),
        sa.Column("cap_code", sa.String(50), nullable=False, server_default=""),
        sa.Column("label_code", sa.String(50), nullable=False, server_default=""),
        sa.Column("carton_label_code", sa.String(50), nullable=False, server_default=""),
        sa.Column("carton_code", sa.String(50), nullable=False, server_default=""),
        sa.Column("carton_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hh_code", name="uq_tab_packaging_bom_hh_code"),
    )
    for name, col in (("ix_pbom_bottle", "bottle_code"), ("ix_pbom_cap", "cap_code"),
                      ("ix_pbom_label", "label_code"), ("ix_pbom_carton_label", "carton_label_code"),
                      ("ix_pbom_carton", "carton_code")):
        op.create_index(name, "tab_packaging_bom", [col])


def downgrade() -> None:
    for name in ("ix_pbom_carton", "ix_pbom_carton_label", "ix_pbom_label", "ix_pbom_cap", "ix_pbom_bottle"):
        op.drop_index(name, table_name="tab_packaging_bom")
    op.drop_table("tab_packaging_bom")
    op.drop_table("tab_product_price_limit")
    op.drop_index("ix_ppq_code_from", table_name="tab_product_price_quote")
    op.drop_table("tab_product_price_quote")
    op.drop_index("ix_ppl_code_latest", table_name="tab_product_price_ledger")
    op.drop_index("ix_tab_product_price_ledger_doc_id", table_name="tab_product_price_ledger")
    op.drop_table("tab_product_price_ledger")
