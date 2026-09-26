"""van ban: noi tab_doc_folder.path 255 -> 760 de cay thu muc sau toi 100 cap

Trần cây thư mục văn bản mở từ 7 lên 100 cấp (26/09/2026). `path` dạng `/1/5/9/`
dài theo số cấp; 255 ký tự chỉ đủ ~36 cấp. 760 là mức lớn nhất còn giữ được chỉ
mục `ix_doc_folder_path` với utf8mb4 (760 × 4 = 3040 byte < 3072).
MODIFY giữ nguyên chỉ mục; bảng nhỏ nên chạy tức thì.

Revision ID: f3b8d1a6c2e9
Revises: d2f7b4a9c6e1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f3b8d1a6c2e9'
down_revision: Union[str, None] = 'd2f7b4a9c6e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('tab_doc_folder', 'path',
                    existing_type=sa.String(255), type_=sa.String(760),
                    existing_nullable=False, existing_server_default='')


def downgrade() -> None:
    #  Hạ về 255 sẽ LỖI nếu đã có thư mục sâu hơn ~36 cấp — cố ý không cắt
    #  chuỗi, cắt `path` là hỏng cả cây.
    op.alter_column('tab_doc_folder', 'path',
                    existing_type=sa.String(760), type_=sa.String(255),
                    existing_nullable=False, existing_server_default='')
