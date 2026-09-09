"""bao_cr321_dieu_khoan_in_theo_ncc

Ba điều khoản in trên Đơn đặt hàng (số ngày kiểm tra hàng, số ngày đổi trả, hạn xuất
hóa đơn) từng chốt cứng trong bản in, nay khai theo từng nhà cung cấp và chép xuống đơn
lúc chọn NCC. Cột thêm ở cả `tab_supplier` (nguồn) lẫn `tab_purchase_order` (bản chép,
sửa riêng từng đơn). 0 / rỗng = chưa khai, bản in lùi về mặc định cũ nên dữ liệu đang có
in ra y hệt trước.

Revision ID: c9d3e7a1f5b6
Revises: b7e2c4d9a1f3
Create Date: 2026-09-09 14:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d3e7a1f5b6'
down_revision: Union[str, None] = 'b7e2c4d9a1f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ('tab_supplier', 'tab_purchase_order')


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column('inspection_days', sa.SmallInteger(), nullable=False, server_default='0'))
        op.add_column(table, sa.Column('return_days', sa.SmallInteger(), nullable=False, server_default='0'))
        op.add_column(table, sa.Column('invoice_deadline', sa.String(length=255), nullable=False, server_default=''))


def downgrade() -> None:
    for table in _TABLES:
        op.drop_column(table, 'invoice_deadline')
        op.drop_column(table, 'return_days')
        op.drop_column(table, 'inspection_days')
