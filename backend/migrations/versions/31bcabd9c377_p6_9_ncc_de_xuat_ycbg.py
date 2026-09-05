"""p6_9_ncc_de_xuat_ycbg

P6-9 (bao-CR-287): cụm NCC do NGƯỜI YÊU CẦU đề xuất trên Yêu cầu báo giá — mirror
cụm `req` của YCMH (PurchaseRequest.suggested_supplier*). Dùng cho bản in luồng gộp:
dòng chưa chốt phương án in cụm này ở cột NCC (doc/erp/12 §P6-9a).

Bản autogenerate kèm ~60 lệnh drift (NOT NULL/index/collation, có cả drop cột thật
`tab_survey_product_line.system_product_code`) — đã CẮT SẠCH, chỉ giữ 3 cột mới.

Revision ID: 31bcabd9c377
Revises: 05d254cf1755
Create Date: 2026-09-04 06:39:58.524897
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '31bcabd9c377'
down_revision: Union[str, None] = '05d254cf1755'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_survey_request',
                  sa.Column('suggested_supplier', sa.String(length=255),
                            nullable=False, server_default=''))
    op.add_column('tab_survey_request',
                  sa.Column('suggested_supplier_tax_code', sa.String(length=50),
                            nullable=False, server_default=''))
    op.add_column('tab_survey_request',
                  sa.Column('suggested_supplier_contact', sa.String(length=255),
                            nullable=False, server_default=''))


def downgrade() -> None:
    op.drop_column('tab_survey_request', 'suggested_supplier_contact')
    op.drop_column('tab_survey_request', 'suggested_supplier_tax_code')
    op.drop_column('tab_survey_request', 'suggested_supplier')
