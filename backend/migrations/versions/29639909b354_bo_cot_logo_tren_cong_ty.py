"""bo_cot_logo_tren_cong_ty

Revision ID: 29639909b354
Revises: c4a9b2e60f83
Create Date: 2026-08-13 10:00:48.344980

Bỏ cột tab_company.logo. Tính năng tải logo pháp nhân bị gỡ theo yêu cầu:
chưa pháp nhân nào dùng (prod 14/14 trống, dev 14/14 trống) nên không mất dữ liệu.
Bản autogenerate còn kèm hàng loạt alter_column NOT NULL và đổi tên chỉ mục do
lệch sẵn giữa model và DB từ trước; đã bỏ hết, migration này chỉ làm đúng một việc.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '29639909b354'
down_revision: Union[str, None] = 'c4a9b2e60f83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('tab_company', 'logo')


def downgrade() -> None:
    op.add_column(
        'tab_company',
        sa.Column('logo', sa.String(length=500), nullable=False, server_default=''),
    )
