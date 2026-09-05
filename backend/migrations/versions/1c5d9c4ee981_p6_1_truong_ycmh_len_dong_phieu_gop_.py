"""p6_1_truong_ycmh_len_dong_phieu_gop_cr277

P6-1 gộp phiếu (bao-CR-277): mang trường của YCMH lên dòng Yêu cầu báo giá —
`tab_survey_request_line` là chứng từ sống sót của vụ gộp (Q4, doc/erp/12).
Tên cột đặt Y HỆT `tab_purchase_request_item` để P6-4 (đồng bộ ngược từ ĐMH)
chép được logic. Bảng đang có dữ liệu nên mọi cột đều có server_default.

LƯU Ý: bản autogenerate kèm ~50 lệnh alter/drop lạc đề do trôi dạt schema cũ
(nullable, index đổi tên, thậm chí DROP `tab_survey_product_line.system_product_code`
đang dùng thật) — đã CẮT HẾT, tệp này chỉ giữ đúng 6 cột của CR.

Revision ID: 1c5d9c4ee981
Revises: a3b31686db49
Create Date: 2026-09-04 02:46:46.998789
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1c5d9c4ee981'
down_revision: Union[str, None] = 'a3b31686db49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = 'tab_survey_request_line'


def upgrade() -> None:
    op.add_column(TABLE, sa.Column('product_code', sa.String(length=50),
                                   nullable=False, server_default=sa.text("''")))
    op.add_column(TABLE, sa.Column('warehouse', sa.String(length=100),
                                   nullable=False, server_default=sa.text("''")))
    op.add_column(TABLE, sa.Column('required_date', sa.String(length=10),
                                   nullable=False, server_default=sa.text("''")))
    op.add_column(TABLE, sa.Column('vat_pct', sa.Numeric(precision=5, scale=2),
                                   nullable=False, server_default=sa.text("'0'")))
    op.add_column(TABLE, sa.Column('qty_ordered', sa.Numeric(precision=18, scale=3),
                                   nullable=False, server_default=sa.text("'0'")))
    op.add_column(TABLE, sa.Column('qty_received', sa.Numeric(precision=18, scale=3),
                                   nullable=False, server_default=sa.text("'0'")))


def downgrade() -> None:
    op.drop_column(TABLE, 'qty_received')
    op.drop_column(TABLE, 'qty_ordered')
    op.drop_column(TABLE, 'vat_pct')
    op.drop_column(TABLE, 'required_date')
    op.drop_column(TABLE, 'warehouse')
    op.drop_column(TABLE, 'product_code')
