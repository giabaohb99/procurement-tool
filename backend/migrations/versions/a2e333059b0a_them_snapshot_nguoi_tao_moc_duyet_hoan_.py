"""them snapshot nguoi tao + moc duyet/hoan thanh cho dat xe va duyet dau

Revision ID: a2e333059b0a
Revises: seal2multi01
Create Date: 2026-09-07 09:28:13.140607

Chỉ thêm cột cho hai bảng (tab_vehicle_booking, tab_seal_request). Bản autogenerate
gốc dính rất nhiều thay đổi KHÔNG liên quan (drift của các model khác) nên đã lược bỏ,
chỉ giữ đúng phần cần. server_default để hàng cũ nhận giá trị hợp lệ, không vi phạm NOT NULL.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a2e333059b0a'
down_revision: Union[str, None] = 'seal2multi01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Đặt xe: chụp email/SĐT/chức danh người tạo + mốc duyệt ---
    op.add_column('tab_vehicle_booking',
                  sa.Column('requester_email', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('tab_vehicle_booking',
                  sa.Column('requester_phone', sa.String(length=30), nullable=False, server_default=''))
    op.add_column('tab_vehicle_booking',
                  sa.Column('requester_role', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('tab_vehicle_booking',
                  sa.Column('approved_at', sa.String(length=20), nullable=False, server_default=''))

    # --- Duyệt dấu: chụp email/SĐT/chức danh người tạo + mốc duyệt/hoàn thành ---
    op.add_column('tab_seal_request',
                  sa.Column('requester_email', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('tab_seal_request',
                  sa.Column('requester_phone', sa.String(length=30), nullable=False, server_default=''))
    op.add_column('tab_seal_request',
                  sa.Column('requester_role', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('tab_seal_request',
                  sa.Column('approved_at', sa.String(length=20), nullable=False, server_default=''))
    op.add_column('tab_seal_request',
                  sa.Column('completed_at', sa.String(length=20), nullable=False, server_default=''))
    op.add_column('tab_seal_request',
                  sa.Column('completed_by', sa.BigInteger(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('tab_seal_request', 'completed_by')
    op.drop_column('tab_seal_request', 'completed_at')
    op.drop_column('tab_seal_request', 'approved_at')
    op.drop_column('tab_seal_request', 'requester_role')
    op.drop_column('tab_seal_request', 'requester_phone')
    op.drop_column('tab_seal_request', 'requester_email')
    op.drop_column('tab_vehicle_booking', 'approved_at')
    op.drop_column('tab_vehicle_booking', 'requester_role')
    op.drop_column('tab_vehicle_booking', 'requester_phone')
    op.drop_column('tab_vehicle_booking', 'requester_email')
