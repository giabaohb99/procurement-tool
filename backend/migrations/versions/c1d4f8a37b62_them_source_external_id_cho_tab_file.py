"""Them cot source + external_id cho tab_file (tep dinh kem app dat xe cu)

Revision ID: c1d4f8a37b62
Revises: b7c2e4a91f30
Create Date: 2026-09-16

Tep dinh kem cua app cu nam trong MOT KHO R2 KHAC — khoa R2 cua ERP khong voi
sang duoc (da thu: HeadObject 404, ListBuckets AccessDenied). Nap sang ERP thi
`file_key` tro toi kho cu, nen duong doc byte PHAI biet dong nay khong phai cua
minh truoc khi goi `download_bytes`. Do la viec cua cot `source`:

* `source` rong  = tep cua chinh ERP, doc thang tu R2 cua ERP (nhu tu truoc toi nay);
* `source` = "datxe" = tep con nam ben app cu, phai hoi app cu lay duong dan moi.

`external_id` giu khoa nhanh `files` ben Firebase. KHONG dung `legacy_id` cua
`LegacyIdMixin` vi `tab_file` khong ke thua mixin do va cung khong nen: tep dinh
kem co the den tu nhieu nguon khac nhau (app dat xe hom nay, nguon khac ngay mai),
nen cap (`source`, `external_id`) moi la thu nhan dang duy nhat mot tep ngoai.
Chi danh index tren `external_id`, KHONG dat UNIQUE — cung ly do o `LegacyIdMixin`:
chong trung lam trong ma nguon bang cach tra `external_id` truoc khi ghi.
"""

from alembic import op
import sqlalchemy as sa

revision = "c1d4f8a37b62"
down_revision = "b7c2e4a91f30"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tab_file",
        sa.Column("source", sa.String(length=20), nullable=False, server_default=""),
    )
    op.add_column(
        "tab_file",
        sa.Column("external_id", sa.String(length=64), nullable=False, server_default=""),
    )
    op.create_index("ix_tab_file_external_id", "tab_file", ["external_id"])


def downgrade() -> None:
    op.drop_index("ix_tab_file_external_id", table_name="tab_file")
    op.drop_column("tab_file", "external_id")
    op.drop_column("tab_file", "source")
