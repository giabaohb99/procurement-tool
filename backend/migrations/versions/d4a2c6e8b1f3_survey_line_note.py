"""survey line note (gộp khảo sát - ghi chú mỗi dòng)

Revision ID: d4a2c6e8b1f3
Revises: c3e5a1b9f7d2
Create Date: 2026-07-04 04:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4a2c6e8b1f3'
down_revision: Union[str, None] = 'c3e5a1b9f7d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_survey_supplier_line', sa.Column('note', sa.Text(), nullable=True))
    op.add_column('tab_survey_product_line', sa.Column('note', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('tab_survey_product_line', 'note')
    op.drop_column('tab_survey_supplier_line', 'note')
