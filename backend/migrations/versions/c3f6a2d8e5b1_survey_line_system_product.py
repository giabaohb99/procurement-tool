"""survey_product_line.system_product_code (ánh xạ mã SP hệ thống trên dòng khảo sát)

Revision ID: c3f6a2d8e5b1
Revises: b2e5f9c3a7d4
Create Date: 2026-07-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c3f6a2d8e5b1'
down_revision: Union[str, None] = 'b2e5f9c3a7d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_survey_product_line',
                  sa.Column('system_product_code', sa.String(length=50), nullable=False, server_default=''))


def downgrade() -> None:
    op.drop_column('tab_survey_product_line', 'system_product_code')
