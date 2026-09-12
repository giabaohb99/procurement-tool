"""ycbg_report_doc_dates_assignee — thêm ngày bắt đầu / hết hiệu lực / nhân sự
thực hiện vào hồ sơ của khối Báo cáo thực hiện (YCBG).

⚠️ VIẾT TAY, không autogenerate: dev DB lệch model nên autogenerate kéo theo
hàng trăm lệnh drift không liên quan (xem ghi chú ở migration 7816572fed52).
Chỉ thêm đúng 3 cột vào `tab_survey_request_report_doc`.

Revision ID: a1c2e3d4f5b6
Revises: 7816572fed52
Create Date: 2026-09-12 02:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1c2e3d4f5b6'
down_revision: Union[str, None] = '7816572fed52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_survey_request_report_doc',
                  sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('tab_survey_request_report_doc',
                  sa.Column('expires_at', sa.Date(), nullable=True))
    #  NOT NULL + server_default='0': hồ sơ cũ (chưa cử ai) nhận 0 ngay khi cột
    #  ra đời, khớp mặc định của model.
    op.add_column('tab_survey_request_report_doc',
                  sa.Column('assignee_id', sa.BigInteger(), nullable=False,
                            server_default='0'))


def downgrade() -> None:
    op.drop_column('tab_survey_request_report_doc', 'assignee_id')
    op.drop_column('tab_survey_request_report_doc', 'expires_at')
    op.drop_column('tab_survey_request_report_doc', 'start_date')
