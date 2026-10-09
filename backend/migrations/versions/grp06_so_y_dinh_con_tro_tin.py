"""agent hub: so y dinh them con tro tin cau hoi de gan nhan tay (ai-CR-138, phase 13.6)

Revision ID: grp06
Revises: grp05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp06"
down_revision: Union[str, None] = "grp05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_agent_intent", sa.Column("message_id", sa.BigInteger(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("tab_agent_intent", "message_id")
