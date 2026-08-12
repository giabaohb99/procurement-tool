"""Them cot tab_payment_request_line.invoice_date (ngay hoa don tren dong YCTT)

CR-066. Trước bản này, dòng phiếu yêu cầu thanh toán chỉ lưu `payable_id`, `po_code`,
`invoice_no`, `amount`; cột "Ngày PS" trên màn hình và cột "Ngày" (chứng từ) trên bản in
được suy ra lúc đọc — thực chất lấy `created_at` của dòng, tức NGÀY TẠO PHIẾU chứ không
phải ngày hóa đơn. Nay ngày hóa đơn là dữ liệu nhập tay được trên bản nháp nên phải lưu.

Ô để trống thì lúc đọc vẫn lấy `tab_po_delivery.invoice_date` của lần giao sinh ra khoản
nợ, nên các phiếu cũ KHÔNG cần điền ngược dữ liệu.

Revision ID: f4d1a6c92e08
Revises: e2c5a81f7b60
Create Date: 2026-08-12 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4d1a6c92e08'
down_revision: Union[str, None] = 'e2c5a81f7b60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_col(table: str, col: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if table not in set(insp.get_table_names()):
        return False
    return any(c["name"] == col for c in insp.get_columns(table))


def upgrade() -> None:
    if not _has_col("tab_payment_request_line", "invoice_date"):
        op.add_column("tab_payment_request_line",
                      sa.Column("invoice_date", sa.String(10),
                                nullable=False, server_default=""))


def downgrade() -> None:
    if _has_col("tab_payment_request_line", "invoice_date"):
        op.drop_column("tab_payment_request_line", "invoice_date")
