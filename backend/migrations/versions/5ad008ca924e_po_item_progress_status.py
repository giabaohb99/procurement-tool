"""po_item progress_status (máy trạng thái tiến độ mua hàng — cột P/AU/AV/AW)

Revision ID: 5ad008ca924e
Revises: e8b1c2d3f4a5
Create Date: 2026-07-11

Ghi chú: cột progress_status mặc định "Chưa đặt hàng" cho mọi dòng cũ.
Không auto-nâng trạng thái theo qty_received hiện có ở migration này —
nghiệp vụ tự chuyển trạng thái theo luồng mới (giữ đơn giản cho v1).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5ad008ca924e'
down_revision: Union[str, None] = 'e8b1c2d3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_po_item', sa.Column('progress_status', sa.String(length=40), nullable=False, server_default='Chưa đặt hàng'))
    op.add_column('tab_po_item', sa.Column('pay_confirm_date', sa.String(length=10), nullable=False, server_default=''))
    op.add_column('tab_po_item', sa.Column('pause_reason', sa.String(length=500), nullable=False, server_default=''))
    op.add_column('tab_po_item', sa.Column('status_before_pause', sa.String(length=40), nullable=False, server_default=''))


def downgrade() -> None:
    op.drop_column('tab_po_item', 'status_before_pause')
    op.drop_column('tab_po_item', 'pause_reason')
    op.drop_column('tab_po_item', 'pay_confirm_date')
    op.drop_column('tab_po_item', 'progress_status')
