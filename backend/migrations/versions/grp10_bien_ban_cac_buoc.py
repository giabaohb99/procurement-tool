"""agent hub: bien ban hop ghi cac buoc da xong (ai-CR-162)

Revision ID: grp10
Revises: grp09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp10"
down_revision: Union[str, None] = "grp09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_agent_meeting"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("steps", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column(TABLE, "steps")
