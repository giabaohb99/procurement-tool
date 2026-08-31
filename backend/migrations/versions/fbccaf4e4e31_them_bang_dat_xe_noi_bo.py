"""them_truong_dat_xe_noi_bo (2 loai + giao hang + diem dung + thuc te/km/chi phi)

Bảng tab_vehicle_booking đã được tạo ở migration trước (bản scaffold). Migration này chỉ:
- thêm cột `request_type` (loại yêu cầu), `stops` (điểm dừng JSON), khối GIAO HÀNG,
  và các cột chạy chuyến thực tế (actual_*, distance_km, cost);
- đổi `status` và `driver_status` từ VARCHAR sang SMALLINT theo rule R2 (mã số + nhãn
  ở tầng hiển thị). Bảng đang rỗng nên đổi kiểu an toàn.

⚠️ Đã LƯỢC BỎ toàn bộ thay đổi KHÔNG liên quan mà autogenerate cuốn theo (drift model
toàn repo: tab_attachment, system_product_code, đổi nullable hàng loạt…). Chỉ giữ đúng
phần Đặt xe.

Revision ID: fbccaf4e4e31
Revises: 9e357b249200
Create Date: 2026-08-29 04:54:58.582344
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'fbccaf4e4e31'
down_revision: Union[str, None] = '9e357b249200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_vehicle_booking',
                  sa.Column('request_type', sa.SmallInteger(), nullable=False, server_default='1'))
    op.add_column('tab_vehicle_booking',
                  sa.Column('stops', sa.Text(), nullable=False))
    op.add_column('tab_vehicle_booking',
                  sa.Column('goods_name', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('tab_vehicle_booking',
                  sa.Column('goods_size', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('tab_vehicle_booking',
                  sa.Column('sender_name', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('tab_vehicle_booking',
                  sa.Column('sender_phone', sa.String(length=30), nullable=False, server_default=''))
    op.add_column('tab_vehicle_booking',
                  sa.Column('receiver_name', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('tab_vehicle_booking',
                  sa.Column('receiver_phone', sa.String(length=30), nullable=False, server_default=''))
    op.add_column('tab_vehicle_booking',
                  sa.Column('special_instructions', sa.Text(), nullable=False))
    op.add_column('tab_vehicle_booking',
                  sa.Column('actual_start_time', sa.String(length=20), nullable=False, server_default=''))
    op.add_column('tab_vehicle_booking',
                  sa.Column('actual_end_time', sa.String(length=20), nullable=False, server_default=''))
    op.add_column('tab_vehicle_booking',
                  sa.Column('distance_km', sa.Float(), nullable=False, server_default='0'))
    op.add_column('tab_vehicle_booking',
                  sa.Column('cost', sa.BigInteger(), nullable=False, server_default='0'))
    op.alter_column('tab_vehicle_booking', 'status',
                    existing_type=mysql.VARCHAR(length=30),
                    type_=sa.SmallInteger(),
                    existing_nullable=False,
                    server_default='1')
    op.alter_column('tab_vehicle_booking', 'driver_status',
                    existing_type=mysql.VARCHAR(length=30),
                    type_=sa.SmallInteger(),
                    existing_nullable=False,
                    server_default='0')
    op.create_index(op.f('ix_tab_vehicle_booking_status'), 'tab_vehicle_booking',
                    ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_vehicle_booking_status'), table_name='tab_vehicle_booking')
    op.alter_column('tab_vehicle_booking', 'driver_status',
                    existing_type=sa.SmallInteger(),
                    type_=mysql.VARCHAR(length=30),
                    existing_nullable=False,
                    server_default='')
    op.alter_column('tab_vehicle_booking', 'status',
                    existing_type=sa.SmallInteger(),
                    type_=mysql.VARCHAR(length=30),
                    existing_nullable=False,
                    server_default='draft')
    op.drop_column('tab_vehicle_booking', 'cost')
    op.drop_column('tab_vehicle_booking', 'distance_km')
    op.drop_column('tab_vehicle_booking', 'actual_end_time')
    op.drop_column('tab_vehicle_booking', 'actual_start_time')
    op.drop_column('tab_vehicle_booking', 'special_instructions')
    op.drop_column('tab_vehicle_booking', 'receiver_phone')
    op.drop_column('tab_vehicle_booking', 'receiver_name')
    op.drop_column('tab_vehicle_booking', 'sender_phone')
    op.drop_column('tab_vehicle_booking', 'sender_name')
    op.drop_column('tab_vehicle_booking', 'goods_size')
    op.drop_column('tab_vehicle_booking', 'goods_name')
    op.drop_column('tab_vehicle_booking', 'stops')
    op.drop_column('tab_vehicle_booking', 'request_type')
