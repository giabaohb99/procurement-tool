"""them approved_by (nguoi phe duyet that) cho dat xe va duyet dau

Revision ID: b3f4a1c2d5e6
Revises: a2e333059b0a
Create Date: 2026-09-07 10:20:00.000000

Chỉ thêm cột `approved_by` (id tài khoản người bấm Duyệt) cho hai bảng. server_default '0'
để hàng cũ hợp lệ; serialize lùi về `first_approver_id` khi cột này = 0 (phiếu duyệt trước đây).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b3f4a1c2d5e6'
down_revision: Union[str, None] = 'a2e333059b0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_vehicle_booking',
                  sa.Column('approved_by', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('tab_seal_request',
                  sa.Column('approved_by', sa.BigInteger(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('tab_seal_request', 'approved_by')
    op.drop_column('tab_vehicle_booking', 'approved_by')
