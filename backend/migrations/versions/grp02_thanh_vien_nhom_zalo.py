"""agent hub: thanh vien nhom Zalo (tai khoan cong ty) — them cot members (ai-CR-122)

Revision ID: grp02
Revises: meet03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp02"
down_revision: Union[str, None] = "meet03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_agent_group", sa.Column("members", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("tab_agent_group", "members")
