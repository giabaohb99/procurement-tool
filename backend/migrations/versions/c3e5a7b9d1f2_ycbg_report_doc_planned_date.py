"""ycbg_report_doc_planned_date — thêm ngày DỰ ĐỊNH HOÀN TẤT vào hồ sơ của khối
Báo cáo thực hiện (YCBG), bao-CR-392.

Khác `expires_at` (hạn hiệu lực giấy tờ): đây là mốc kế hoạch ban đầu, để soi
hồ sơ có bị trễ so với dự định hay không.

⚠️ VIẾT TAY, không autogenerate (cùng lý do drift như a1c2e3d4f5b6).

Revision ID: c3e5a7b9d1f2
Revises: b2d4f6a8c0e1
Create Date: 2026-09-12 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3e5a7b9d1f2'
down_revision: Union[str, None] = 'b2d4f6a8c0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_survey_request_report_doc',
                  sa.Column('planned_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('tab_survey_request_report_doc', 'planned_date')
