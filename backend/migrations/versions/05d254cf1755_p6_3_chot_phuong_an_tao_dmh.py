"""p6_3_chot_phuong_an_tao_dmh

P6-3 (bao-CR-281): bộ phận yêu cầu CHỐT phương án từng dòng, thu mua tạo THẲNG
đơn mua hàng từ dòng đã chốt — bỏ bước sinh YCMH trung gian.
- `tab_survey_request_line` thêm cặp `po_id`/`po_code` (ĐMH gần nhất tạo thẳng
  từ dòng — đối xứng `pr_id`/`pr_code`). Bảng đang có dữ liệu nên có server_default.
- Bảng mới `tab_survey_request_po`: lịch sử mỗi lần lên đơn (1 dòng có thể lên
  đơn nhiều lần — mua lại), đối xứng `tab_survey_request_pr`.
Trạng thái dòng "confirmed" dùng lại cột `line_status` sẵn có — không đổi schema.

LƯU Ý: bản autogenerate kèm ~60 lệnh alter/drop lạc đề do trôi dạt schema cũ
(nullable, index đổi tên, DROP cột đang dùng thật) — đã CẮT HẾT, tệp này chỉ
giữ đúng phần của CR.

Revision ID: 05d254cf1755
Revises: 1c5d9c4ee981
Create Date: 2026-09-04 04:08:01.586852
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '05d254cf1755'
down_revision: Union[str, None] = '1c5d9c4ee981'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LINE_TABLE = 'tab_survey_request_line'
PO_TABLE = 'tab_survey_request_po'


def upgrade() -> None:
    op.add_column(LINE_TABLE, sa.Column('po_id', sa.BigInteger(),
                                        nullable=False, server_default=sa.text("'0'")))
    op.add_column(LINE_TABLE, sa.Column('po_code', sa.String(length=50),
                                        nullable=False, server_default=sa.text("''")))
    op.create_table(
        PO_TABLE,
        sa.Column('survey_request_id', sa.BigInteger(), nullable=False),
        sa.Column('survey_request_line_id', sa.BigInteger(), nullable=False),
        sa.Column('option_id', sa.BigInteger(), nullable=False),
        sa.Column('product_survey_line_id', sa.BigInteger(), nullable=False),
        sa.Column('po_id', sa.BigInteger(), nullable=False),
        sa.Column('po_code', sa.String(length=50), nullable=False),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_survey_request_po_option_id'), PO_TABLE, ['option_id'], unique=False)
    op.create_index(op.f('ix_tab_survey_request_po_po_id'), PO_TABLE, ['po_id'], unique=False)
    op.create_index(op.f('ix_tab_survey_request_po_survey_request_id'), PO_TABLE, ['survey_request_id'], unique=False)
    op.create_index(op.f('ix_tab_survey_request_po_survey_request_line_id'), PO_TABLE, ['survey_request_line_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_survey_request_po_survey_request_line_id'), table_name=PO_TABLE)
    op.drop_index(op.f('ix_tab_survey_request_po_survey_request_id'), table_name=PO_TABLE)
    op.drop_index(op.f('ix_tab_survey_request_po_po_id'), table_name=PO_TABLE)
    op.drop_index(op.f('ix_tab_survey_request_po_option_id'), table_name=PO_TABLE)
    op.drop_table(PO_TABLE)
    op.drop_column(LINE_TABLE, 'po_code')
    op.drop_column(LINE_TABLE, 'po_id')
