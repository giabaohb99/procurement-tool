"""thuoc bvtv danh dau tu them

duoc-CR-490 (29/09/2026): danh mục thuốc BVTV có thêm / sửa / xóa trên màn. Cột `is_manual`
đánh dấu thuốc người dùng tự thêm — nạp lại danh mục từ tệp GIỮ các dòng này, chỉ thay dòng
lấy từ nguồn. Dòng đang có đều là dòng nạp từ tệp nên mặc định `0`.

duoc-CR-495 (cùng ngày, chưa lên môi trường nào nên gộp vào đây): cột `summary` — câu mô tả của
trang nguồn (`tom_tat_su_dung` của bản cào). TEXT nên không có DEFAULT ở tầng MySQL.

Viết TAY (autogenerate repo này trôi ~650 dòng không liên quan).

Revision ID: b4d81f2c6e37
Revises: a7c3e91d5b20
Create Date: 2026-09-29 15:40:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b4d81f2c6e37'
down_revision: Union[str, None] = 'a7c3e91d5b20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_customs_pesticide',
                  sa.Column('is_manual', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('tab_customs_pesticide', sa.Column('summary', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('tab_customs_pesticide', 'summary')
    op.drop_column('tab_customs_pesticide', 'is_manual')
