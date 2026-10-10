"""agent hub: so y dinh them chi phi + toc do tung luot tra loi (ai-CR-160, phase 16.1)

Revision ID: grp09
Revises: grp08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp09"
down_revision: Union[str, None] = "grp08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_agent_intent"
COLUMNS = (
    ("model", sa.String(80), "''"),
    ("tokens_in", sa.Integer(), "0"),
    ("tokens_out", sa.Integer(), "0"),
    ("cache_read", sa.Integer(), "0"),
    ("cost_usd", sa.Float(), "0"),
    ("duration_ms", sa.Integer(), "0"),
    ("tools_offered", sa.SmallInteger(), "0"),
)


def upgrade() -> None:
    for name, kind, default in COLUMNS:
        op.add_column(TABLE, sa.Column(name, kind, nullable=False, server_default=sa.text(default)))


def downgrade() -> None:
    for name, _kind, _default in reversed(COLUMNS):
        op.drop_column(TABLE, name)
