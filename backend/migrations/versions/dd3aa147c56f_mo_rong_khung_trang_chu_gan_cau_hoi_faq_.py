"""mo rong khung trang chu: gan cau hoi FAQ va the tu do

Khung "Không tìm thấy điều bạn cần?" gắn được câu hỏi thường gặp (faq_id) và khung "Mẹo tra cứu"
nhập được thẻ tự do (title/description/icon). Vì vậy article_id phải cho phép NULL — mỗi phần tử
chỉ dùng đúng một trong ba nhóm cột.

Đã BỎ các thay đổi của tab_ticket / tab_ticket_message mà autogenerate bắt kèm: đó là sai lệch
sẵn có giữa model và DB, không thuộc phạm vi thay đổi này.

Revision ID: dd3aa147c56f
Revises: c8d1f6b3a92e
Create Date: 2026-08-06 03:29:17.467237
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'dd3aa147c56f'
down_revision: Union[str, None] = 'c8d1f6b3a92e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK_FAQ = 'fk_help_home_item_faq'


def upgrade() -> None:
    op.add_column('tab_help_home_item', sa.Column('faq_id', sa.BigInteger(), nullable=True))
    op.add_column('tab_help_home_item', sa.Column('title', sa.String(length=150), nullable=True))
    op.add_column('tab_help_home_item', sa.Column('description', sa.String(length=500), nullable=True))
    op.add_column('tab_help_home_item', sa.Column('icon', sa.String(length=50), nullable=True))
    op.alter_column('tab_help_home_item', 'article_id',
                    existing_type=mysql.BIGINT(),
                    nullable=True)
    op.create_foreign_key(FK_FAQ, 'tab_help_home_item', 'tab_faq', ['faq_id'], ['id'],
                          ondelete='CASCADE')


def downgrade() -> None:
    # Phần tử của khung faq/tips không có article_id -> phải xóa trước khi trả cột về NOT NULL
    op.execute('DELETE FROM tab_help_home_item WHERE article_id IS NULL')
    op.drop_constraint(FK_FAQ, 'tab_help_home_item', type_='foreignkey')
    op.alter_column('tab_help_home_item', 'article_id',
                    existing_type=mysql.BIGINT(),
                    nullable=False)
    op.drop_column('tab_help_home_item', 'icon')
    op.drop_column('tab_help_home_item', 'description')
    op.drop_column('tab_help_home_item', 'title')
    op.drop_column('tab_help_home_item', 'faq_id')
