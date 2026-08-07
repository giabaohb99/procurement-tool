"""lich su mua hang them nguon du lieu cu

Lịch sử mua hàng chứa thêm DỮ LIỆU CŨ nhập từ file Excel (giai đoạn trước khi có hệ thống):
  - `source`     : system = chốt tự động khi dòng ĐMH "Hoàn thành" | legacy = nhập từ file
  - `legacy_key` : khóa nguồn của dòng cũ (file + sheet + số dòng), unique để chống nhập trùng
  - `po_item_id` : cho phép NULL vì dòng cũ không có ĐMH trong hệ thống. MySQL cho phép nhiều
                   NULL trong unique index nên lớp chống ghi trùng của luồng chạy thật vẫn giữ nguyên.

(Bản autogenerate quét ra hàng loạt alter NOT NULL không liên quan ở các bảng khác — đã bỏ,
 file này chỉ đụng tab_purchase_history.)

Revision ID: 5b85be0c2b48
Revises: e7a3c9d5b210
Create Date: 2026-08-07 07:21:16.318878
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '5b85be0c2b48'
down_revision: Union[str, None] = 'e7a3c9d5b210'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_purchase_history',
                  sa.Column('source', sa.String(length=10), nullable=False, server_default='system'))
    op.add_column('tab_purchase_history', sa.Column('legacy_key', sa.String(length=190), nullable=True))
    op.alter_column('tab_purchase_history', 'po_item_id',
                    existing_type=mysql.BIGINT(), nullable=True)
    op.create_index(op.f('ix_tab_purchase_history_source'), 'tab_purchase_history', ['source'], unique=False)
    op.create_unique_constraint('uq_tab_purchase_history_legacy_key', 'tab_purchase_history', ['legacy_key'])


def downgrade() -> None:
    op.drop_constraint('uq_tab_purchase_history_legacy_key', 'tab_purchase_history', type_='unique')
    op.drop_index(op.f('ix_tab_purchase_history_source'), table_name='tab_purchase_history')
    op.alter_column('tab_purchase_history', 'po_item_id',
                    existing_type=mysql.BIGINT(), nullable=False)
    op.drop_column('tab_purchase_history', 'legacy_key')
    op.drop_column('tab_purchase_history', 'source')
