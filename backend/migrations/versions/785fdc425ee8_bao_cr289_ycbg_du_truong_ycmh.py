"""bao_cr289_ycbg_du_truong_ycmh

bao-CR-289: YCBG (phiếu gộp) đủ trường YCMH — thêm cờ `is_urgent` lên đầu phiếu và
hai trường tiến độ `expected_date` / `progress_note` lên dòng (đặt tên y hệt
`tab_purchase_request_item`). Hai trường tiến độ CỐ Ý không đi qua SurveyRequestLineIn
mà qua endpoint lines/{id}/progress riêng — xem comment trong survey_request/model.py.
Bảng đang có dữ liệu nên mọi cột đều có server_default.

LƯU Ý: bản autogenerate kèm ~60 lệnh alter/drop lạc đề do trôi dạt schema cũ
(nullable, index đổi tên, DROP `tab_survey_product_line.system_product_code` đang dùng
thật) — đã CẮT HẾT như tiền lệ 1c5d9c4ee981, tệp này chỉ giữ đúng 3 cột của CR.

Revision ID: 785fdc425ee8
Revises: 31bcabd9c377
Create Date: 2026-09-04 07:38:17.711498
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '785fdc425ee8'
down_revision: Union[str, None] = '31bcabd9c377'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_survey_request', sa.Column('is_urgent', sa.Boolean(),
                                                  nullable=False, server_default=sa.text("'0'")))
    op.add_column('tab_survey_request_line', sa.Column('expected_date', sa.String(length=10),
                                                       nullable=False, server_default=sa.text("''")))
    op.add_column('tab_survey_request_line', sa.Column('progress_note', sa.Text(), nullable=False))


def downgrade() -> None:
    op.drop_column('tab_survey_request_line', 'progress_note')
    op.drop_column('tab_survey_request_line', 'expected_date')
    op.drop_column('tab_survey_request', 'is_urgent')
