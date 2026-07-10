"""Liên kết Phiếu khảo sát -> Yêu cầu khảo sát (survey_request_id, sr_code)

Revision ID: e8b1c2d3f4a5
Revises: d7a1c4e8b3f2
Create Date: 2026-07-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e8b1c2d3f4a5'
down_revision: Union[str, None] = 'd7a1c4e8b3f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_survey', sa.Column('survey_request_id', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('tab_survey', sa.Column('sr_code', sa.String(length=50), nullable=False, server_default=''))
    op.create_index('ix_tab_survey_survey_request_id', 'tab_survey', ['survey_request_id'])


def downgrade() -> None:
    op.drop_index('ix_tab_survey_survey_request_id', table_name='tab_survey')
    op.drop_column('tab_survey', 'sr_code')
    op.drop_column('tab_survey', 'survey_request_id')
