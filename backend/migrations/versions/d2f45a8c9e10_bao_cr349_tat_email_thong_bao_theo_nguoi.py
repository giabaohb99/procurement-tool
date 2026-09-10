"""bao_cr349_tat_email_thong_bao_theo_nguoi

`tab_user.notify_email` — người dùng tự tắt email thông báo luồng duyệt cho riêng tài
khoản mình (ticket 37 prod). Mặc định `1` = vẫn nhận, nên mọi tài khoản đang chạy giữ
nguyên hành vi cũ; ai muốn tắt thì tự tick ở Trang cá nhân.

Chỉ chặn thư `workflow_*`. Thư đặt lại mật khẩu và thư cấp tài khoản KHÔNG đi qua cột
này — tắt chúng thì người dùng mất đường vào hệ thống.

Revision ID: d2f45a8c9e10
Revises: a1c6f80b2d47
Create Date: 2026-09-10 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2f45a8c9e10'
down_revision: Union[str, None] = 'a1c6f80b2d47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_user',
                  sa.Column('notify_email', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    op.drop_column('tab_user', 'notify_email')
