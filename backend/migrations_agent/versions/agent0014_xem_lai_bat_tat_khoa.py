"""agent hub: khoa MCP xem lai khoa (raw_view) + bat / tat tam (disabled_at) (ai-CR-221)

Revision ID: agent0014
Revises: agent0013

Cặp với `migrations/versions/mcpkey03_xem_lai_bat_tat_khoa.py` (chế độ nhúng). Chỉ thêm khi thiếu.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "agent0014"
down_revision: Union[str, None] = "agent0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

KEY = "tab_agent_mcp_key"
COLUMNS = (
    ("raw_view", lambda: sa.Column("raw_view", sa.Text(), nullable=True)),
    ("disabled_at", lambda: sa.Column("disabled_at", sa.DateTime(), nullable=True)),
)


def upgrade() -> None:
    have = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(KEY)}
    for name, col in COLUMNS:
        if name not in have:
            op.add_column(KEY, col())


def downgrade() -> None:
    have = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(KEY)}
    for name, _col in reversed(COLUMNS):
        if name in have:
            op.drop_column(KEY, name)
