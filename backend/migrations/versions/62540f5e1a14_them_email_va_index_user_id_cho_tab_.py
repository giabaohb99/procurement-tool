"""them email va index user_id cho tab_driver

Chỉ thêm cột `email` (liên hệ / trùng email tài khoản) và index trên `user_id`
(liên kết tài khoản đăng nhập của tài xế nội bộ). Đã LƯỢC bỏ mọi thay đổi
KHÔNG liên quan mà autogenerate cuốn theo (drift NOT NULL toàn repo).

Revision ID: 62540f5e1a14
Revises: 550132b5e0e4
Create Date: 2026-09-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '62540f5e1a14'
down_revision: Union[str, None] = '550132b5e0e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tab_driver',
        sa.Column('email', sa.String(length=255), nullable=False, server_default=''),
    )
    op.create_index(op.f('ix_tab_driver_user_id'), 'tab_driver', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_driver_user_id'), table_name='tab_driver')
    op.drop_column('tab_driver', 'email')
