"""Thêm cờ ĐÁNH SỐ MỤC TỰ ĐỘNG cho phiên bản văn bản.

Bật thì tiêu đề trong bài tự mang số nhiều cấp (I · 1 · a) mà không phải gõ tay
— gõ tay thì chèn thêm một mục ở giữa là phải đánh lại toàn bộ phía sau.

Cờ của TỪNG PHIÊN BẢN chứ không phải của cả văn bản: bản 2.0 đổi cách trình bày
không được kéo bản 1.0 đã ký đổi theo.

⚠️ Autogenerate còn dò ra một loạt `alter_column ... nullable=False` ở các bảng
bình luận / ticket — lệch có sẵn giữa model và CSDL, KHÔNG thuộc việc này nên đã
bỏ khỏi bản vá.

Revision ID: 9effe7ec20cb
Revises: 4d6cb36cf82f
Create Date: 2026-08-19 08:45:06.551755
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9effe7ec20cb'
down_revision: Union[str, None] = '4d6cb36cf82f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_document_version',
                  sa.Column('auto_heading_number', sa.Boolean(),
                            nullable=False, server_default=sa.text('0')))


def downgrade() -> None:
    op.drop_column('tab_document_version', 'auto_heading_number')
