"""them_thu_tu_tien_quyet_cho_quy_tac_quan_he

Thêm `sort_order` cho `tab_doc_type_link_rule`: thứ tự tiên quyết trong cùng một
loại nguồn — *"trước C phải có A rồi B"*.

⚠️ Bản autogenerate còn bắt thêm một loạt `ALTER COLUMN ... NOT NULL` ở
`tab_comment_*` và `tab_ticket*` — đó là **độ lệch có sẵn** giữa model và cơ sở
dữ liệu, không phải việc của lần sửa này. Đã cắt bỏ: gộp vào đây thì một thay
đổi một dòng biến thành bản vá bảy bảng, mà lúc có sự cố không ai lần ra được
cột nào thuộc việc nào. Muốn dọn thì làm một migration riêng.

Revision ID: 225c3966c99c
Revises: 092b4e436d25
Create Date: 2026-08-18 02:15:35.424368
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '225c3966c99c'
down_revision: Union[str, None] = '092b4e436d25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #  `server_default='0'` là bắt buộc: cột NOT NULL thêm vào bảng đã có dữ liệu
    #  thì MySQL phải biết điền gì cho các dòng cũ. 0 = chưa xếp thứ tự, và
    #  `list_rules` sắp xếp sao cho các dòng cũ giữ nguyên trật tự như trước.
    op.add_column(
        'tab_doc_type_link_rule',
        sa.Column('sort_order', sa.SmallInteger(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_column('tab_doc_type_link_rule', 'sort_order')
