"""gop 2 alembic head: CR-268 tien treo + forum F13a

KHÔNG đổi lược đồ — chỉ hợp nhất hai nhánh migration cùng mọc ra từ `7e93b1977593`:
  7e93b1977593 -> d5e8f2a71c04                  (CR-268 tiền treo)
  7e93b1977593 -> c3a91d47f2b8 -> e7b3c9d41f28  (forum F13a)
Để hai đầu thì `alembic upgrade head` báo "Multiple head revisions" và container `api`
chết ngay lúc khởi động. Cùng cách xử lý như commit 8b877458.

Tệp `..._forum_board_f13a.py` có ghi chú định rebase `down_revision` trước khi commit.
Nếu chọn hướng đó thì XÓA tệp gộp này đi, đừng giữ cả hai.

Revision ID: 79f6f09573b9
Revises: d5e8f2a71c04, e7b3c9d41f28
Create Date: 2026-09-03 04:07:21.242941
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79f6f09573b9'
down_revision: Union[str, None] = ('d5e8f2a71c04', 'e7b3c9d41f28')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
