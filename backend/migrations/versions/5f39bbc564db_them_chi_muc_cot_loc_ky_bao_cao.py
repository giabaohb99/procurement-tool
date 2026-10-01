"""them chi muc cot loc ky bao cao

Bốn cột lọc KỲ của các endpoint /summary báo cáo (P05, review hiệu năng 28/09/2026) — trước
đây không có chỉ mục nên mỗi lượt xem báo cáo (`build_report` gọi `fetch()` 2 lần/lượt) là
quét hết bảng: `tab_purchase_request.request_date` (báo cáo Chi tiết YC mua hàng),
`tab_survey_request.request_date` (Tiến độ báo giá), `tab_survey_supplier_line.contact_date`
+ `tab_survey_product_line.contact_date` (Báo cáo khảo sát — cột lọc kỳ mới nhờ
`survey/service.report_rows_in_range`).

CẮT TAY khỏi bản autogenerate: repo có drift ~650 dòng không liên quan (đổi `NOT NULL`/tên
chỉ mục hàng loạt trên các bảng khác chưa đồng bộ với model — xem
`doc/tai-lieu-ky-thuat/nhat-ky-task.md`), giữ đúng migration này CHỈ 4 chỉ mục cố ý thêm.

Revision ID: 5f39bbc564db
Revises: e538c6a1f2d9 (bao-CR-531/537/538 chen truoc de len prod som)
Create Date: 2026-09-28 07:19:27.880973
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5f39bbc564db'
down_revision: Union[str, None] = 'e538c6a1f2d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f('ix_tab_purchase_request_request_date'), 'tab_purchase_request',
                     ['request_date'], unique=False)
    op.create_index(op.f('ix_tab_survey_request_request_date'), 'tab_survey_request',
                     ['request_date'], unique=False)
    op.create_index(op.f('ix_tab_survey_supplier_line_contact_date'), 'tab_survey_supplier_line',
                     ['contact_date'], unique=False)
    op.create_index(op.f('ix_tab_survey_product_line_contact_date'), 'tab_survey_product_line',
                     ['contact_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_survey_product_line_contact_date'), table_name='tab_survey_product_line')
    op.drop_index(op.f('ix_tab_survey_supplier_line_contact_date'), table_name='tab_survey_supplier_line')
    op.drop_index(op.f('ix_tab_survey_request_request_date'), table_name='tab_survey_request')
    op.drop_index(op.f('ix_tab_purchase_request_request_date'), table_name='tab_purchase_request')
