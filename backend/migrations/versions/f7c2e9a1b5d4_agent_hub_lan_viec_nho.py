"""agent hub: cot lane o tab_agent_task — duong tat viec nho (ai-CR-057)

Viec nho va ro (doi chu/nhan/mau tren giao dien) khong ra soat rieng, khong cho duyet.

Revision ID: f7c2e9a1b5d4
Revises: e6b1d4f8a2c7
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f7c2e9a1b5d4'
down_revision: Union[str, None] = 'e6b1d4f8a2c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_agent_task', sa.Column('lane', sa.SmallInteger(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('tab_agent_task', 'lane')
