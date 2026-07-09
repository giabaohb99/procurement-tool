"""survey_request_option.system_product_code (gắn mã SP hệ thống cho option)

Revision ID: b2e5f9c3a7d4
Revises: a1d4f8b2c6e7
Create Date: 2026-07-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2e5f9c3a7d4'
down_revision: Union[str, None] = 'a1d4f8b2c6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_survey_request_option',
                  sa.Column('system_product_code', sa.String(length=50), nullable=False, server_default=''))


def downgrade() -> None:
    op.drop_column('tab_survey_request_option', 'system_product_code')
