"""bao_cr_291_ghi_chu_thu_mua_dong_ycbg

Thêm ô ghi chú riêng của thu mua lên dòng YCBG (mirror `tab_pr_item.note`).

Autogenerate của lần chạy này bắt thêm hàng trăm lệnh drift không liên quan (NOT NULL,
index của các bảng khác) — đã bỏ hết, chỉ giữ đúng một cột mới.

Revision ID: 073812737ad1
Revises: 785fdc425ee8
Create Date: 2026-09-05 02:14:16.424093
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '073812737ad1'
down_revision: Union[str, None] = '785fdc425ee8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_survey_request_line',
                  sa.Column('purchaser_note', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('tab_survey_request_line', 'purchaser_note')
