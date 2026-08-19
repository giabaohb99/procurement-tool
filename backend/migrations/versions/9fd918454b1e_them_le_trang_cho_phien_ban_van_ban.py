"""Thêm LỀ TRANG (mm) cho phiên bản văn bản — Nghị định 30 điều 8.

Lề ngang gắn với PHIÊN BẢN chứ không với văn bản: sửa lề ở bản 2.0 không được
đổi hình dạng bản 1.0 đã ký. Dòng dữ liệu cũ nhận mặc định 30mm/20mm — đúng thể
thức hành chính; ai muốn khác thì kéo lại thước trên trình soạn thảo.

⚠️ Autogenerate còn dò ra một loạt `alter_column ... nullable=False` ở các bảng
bình luận / ticket — đó là lệch có sẵn giữa model và DB, KHÔNG thuộc việc này
nên đã bỏ khỏi bản vá để không đụng bảng của phân hệ khác.

⚠️ `Revises` trỏ vào `d5b2f9c31a08` (CR-087) chứ không phải `225c3966c99c` như lúc
mới sinh ra: bản vá này làm song song với nhánh CR-086/087, rebase xong thì hai
nhánh cùng treo vào một điểm và Alembic có HAI head. `alembic upgrade head` gặp
hai head là báo lỗi và dừng — mà `start.sh` chạy đúng lệnh đó lúc khởi động, nên
API sẽ không lên nổi. Nối thẳng vào cuối nhánh kia là hết chẻ.

Revision ID: 9fd918454b1e
Revises: d5b2f9c31a08
Create Date: 2026-08-19 03:43:48.925469
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9fd918454b1e'
down_revision: Union[str, None] = 'd5b2f9c31a08'
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
