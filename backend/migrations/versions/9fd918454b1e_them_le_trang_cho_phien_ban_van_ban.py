"""Thêm LỀ TRANG (mm) cho phiên bản văn bản — Nghị định 30 điều 8.

Lề ngang gắn với PHIÊN BẢN chứ không với văn bản: sửa lề ở bản 2.0 không được
đổi hình dạng bản 1.0 đã ký. Dòng dữ liệu cũ nhận mặc định 30mm/20mm — đúng thể
thức hành chính; ai muốn khác thì kéo lại thước trên trình soạn thảo.

⚠️ Autogenerate còn dò ra một loạt `alter_column ... nullable=False` ở các bảng
bình luận / ticket — đó là lệch có sẵn giữa model và DB, KHÔNG thuộc việc này
nên đã bỏ khỏi bản vá để không đụng bảng của phân hệ khác.

Revision ID: 9fd918454b1e
Revises: 225c3966c99c
Create Date: 2026-08-19 03:43:48.925469
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9fd918454b1e'
down_revision: Union[str, None] = '225c3966c99c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_document_version',
                  sa.Column('margin_left_mm', sa.SmallInteger(),
                            nullable=False, server_default='30'))
    op.add_column('tab_document_version',
                  sa.Column('margin_right_mm', sa.SmallInteger(),
                            nullable=False, server_default='20'))


def downgrade() -> None:
    op.drop_column('tab_document_version', 'margin_right_mm')
    op.drop_column('tab_document_version', 'margin_left_mm')
