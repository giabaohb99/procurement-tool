"""bao_cr347_gia_von_lo_hang_nhap_khau

Nền dữ liệu cho báo cáo giá vốn lô hàng nhập khẩu:

- `tab_po_import_cost.cost_status` — khoản chi phí là số DỰ KIẾN hay số THỰC TẾ. Dòng
  đang có đều là số thật (đã sinh công nợ ở bao-CR-319 P5) nên điền 2 = Thực tế; đó cũng
  là mặc định của cột, nên luồng cũ không đổi hành vi.
- `tab_purchase_order.etd_date` — ngày hàng rời cảng xuất (ETD), dòng "Ngày gửi" trên mẫu
  báo cáo khách đưa. Rỗng = chưa khai.

Không đụng vào ba loại chi phí mới (12/13/14): chúng chỉ là giá trị của cột `cost_type`
đã có, khai trong mã nguồn.

Revision ID: a1c6f80b2d47
Revises: c9d3e7a1f5b6
Create Date: 2026-09-10 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c6f80b2d47'
down_revision: Union[str, None] = 'c9d3e7a1f5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_po_import_cost',
                  sa.Column('cost_status', sa.SmallInteger(), nullable=False, server_default='2'))
    op.create_index('ix_tab_po_import_cost_cost_status', 'tab_po_import_cost', ['cost_status'])
    op.add_column('tab_purchase_order',
                  sa.Column('etd_date', sa.String(length=10), nullable=False, server_default=''))


def downgrade() -> None:
    op.drop_column('tab_purchase_order', 'etd_date')
    op.drop_index('ix_tab_po_import_cost_cost_status', table_name='tab_po_import_cost')
    op.drop_column('tab_po_import_cost', 'cost_status')
