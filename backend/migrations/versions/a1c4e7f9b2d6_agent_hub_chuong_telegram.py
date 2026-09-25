"""agent hub: cot notify_mode o tab_agent_chat_link — chuong ERP sang Telegram ca nhan (ai-CR-059, P-01)

0 tat, 1 viec cua toi (mac dinh), 2 tat ca. Con tro bell_offset nam o tab_agent_cursor.

Revision ID: a1c4e7f9b2d6
Revises: f7c2e9a1b5d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1c4e7f9b2d6'
down_revision: Union[str, None] = 'f7c2e9a1b5d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_agent_chat_link', sa.Column('notify_mode', sa.SmallInteger(), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_column('tab_agent_chat_link', 'notify_mode')
