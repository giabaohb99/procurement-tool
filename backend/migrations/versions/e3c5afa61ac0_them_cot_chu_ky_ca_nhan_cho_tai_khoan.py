"""them cot chu ky ca nhan cho tai khoan

Revision ID: e3c5afa61ac0
Revises: da225a25912a
Create Date: 2026-08-07 02:25:43.409362

Chỉ thêm cột tab_user.signature (URL ảnh chữ ký cá nhân). Các lệnh alter_column
NOT NULL mà autogenerate sinh kèm cho tab_ticket / tab_comment_* đã bị BỎ: đó là
chênh lệch cũ của schema, không thuộc thay đổi này.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e3c5afa61ac0'
down_revision: Union[str, None] = 'da225a25912a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default="" để bản ghi cũ không vướng NOT NULL khi thêm cột
    op.add_column('tab_user', sa.Column('signature', sa.String(length=500),
                                        nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column('tab_user', 'signature')
