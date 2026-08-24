"""Thêm HẠN XEM TỆP ĐÍNH KÈM cho văn bản (`tab_document.attachment_view_until`).

Quá ngày này thì mọi tệp đính kèm của văn bản không mở/tải được nữa — dùng cho
tài liệu chỉ cho xem trong một khoảng (bảng lương kỳ này, hồ sơ thầu tới ngày mở
thầu). Khác `expire_date` là hạn HIỆU LỰC của chính văn bản.

⚠️ Bản autogenerate ban đầu kèm theo **27 lệnh `alter_column` không liên quan**
(NOT NULL cho `tab_comment_*`, `tab_ticket*`…) — đó là ĐỘ LỆCH có sẵn giữa model
và CSDL thật, không phải việc của đợt này. Đã cắt bỏ hết: một migration chỉ được
làm đúng thứ tên nó nói, gộp thêm là lần sau muốn lùi một cái thì lùi luôn cả
đám. Muốn dọn phần lệch kia thì làm một migration riêng, có người soát.

Revision ID: 62398fdb8563
Revises: ebcfc25db193
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '62398fdb8563'
down_revision: Union[str, None] = 'ebcfc25db193'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_document',
                  sa.Column('attachment_view_until', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('tab_document', 'attachment_view_until')
