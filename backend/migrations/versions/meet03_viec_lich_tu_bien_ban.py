"""agent hub: viec + lich rut tu bien ban hop — them cot actions (ai-CR-114)

Revision ID: meet03
Revises: meet02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "meet03"
down_revision: Union[str, None] = "meet02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_agent_meeting", sa.Column("actions", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("tab_agent_meeting", "actions")
