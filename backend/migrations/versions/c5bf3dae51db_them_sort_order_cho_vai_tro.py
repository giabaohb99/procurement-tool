"""them sort_order cho vai tro

Thứ tự hiện của vai trò trên màn Phân quyền tài khoản — người quản trị tự kéo
thả (CR-172). Trước đó danh sách xếp cứng theo `id`.

⚠️ Tệp này đã được VIẾT LẠI BẰNG TAY. Bản `--autogenerate` sinh ra 44 thao tác:
ngoài cột này nó còn đòi sửa `tab_assistant_*` và `tab_ticket*` của phân hệ khác
(đổi NOT NULL, **xóa index**) — là độ lệch giữa model và DB đang có của người
khác, không phải việc của CR này. Để nguyên thì một migration mang tên "sắp xếp
vai trò" lặng lẽ đụng vào bảng của phân hệ khác.

Revision ID: c5bf3dae51db
Revises: c9a71e5b40d3
Create Date: 2026-08-25 09:00:33.994704
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c5bf3dae51db'
down_revision: Union[str, None] = 'c9a71e5b40d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #  `server_default='0'` chứ không chỉ `default=0`: bảng đang có sẵn vài chục
    #  dòng, cột NOT NULL mà không có mặc định phía CSDL là MySQL từ chối thêm.
    #  Mọi vai trò cũ cùng nhận 0 nên thứ tự ban đầu vẫn là theo `id` (khóa phụ
    #  trong `list_roles_query`) — nhìn y như trước cho tới lần kéo thả đầu tiên.
    op.add_column(
        'tab_role',
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
    )


def downgrade() -> None:
    op.drop_column('tab_role', 'sort_order')
