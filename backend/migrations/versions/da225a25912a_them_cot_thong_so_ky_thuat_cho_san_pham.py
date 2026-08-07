"""them cot thong so ky thuat cho san pham

Revision ID: da225a25912a
Revises: d2e6f4b81a37
Create Date: 2026-08-07 02:15:39.809955

Chỉ thêm cột tab_product.specs (Thông số kỹ thuật). Các lệnh alter_column NOT NULL
mà autogenerate sinh ra cho tab_ticket / tab_comment_* đã bị BỎ: đó là chênh lệch cũ
của schema, không thuộc thay đổi này.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'da225a25912a'
down_revision: Union[str, None] = 'd2e6f4b81a37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default="" để bản ghi cũ không vướng NOT NULL khi thêm cột
    op.add_column('tab_product', sa.Column('specs', sa.String(length=255),
                                           nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column('tab_product', 'specs')
