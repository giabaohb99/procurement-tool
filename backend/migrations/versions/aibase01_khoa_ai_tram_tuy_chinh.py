"""agent hub: khoa AI tram tuy chinh kieu OpenAI — them cot base_url (ai-CR-108)

Revision ID: aibase01
Revises: grp01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "aibase01"
down_revision: Union[str, None] = "grp01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_ai_key", sa.Column("base_url", sa.String(length=200), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("tab_ai_key", "base_url")
