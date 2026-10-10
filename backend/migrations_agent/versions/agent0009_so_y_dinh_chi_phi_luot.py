"""agent hub: so y dinh them chi phi + toc do tung luot tra loi (ai-CR-160, phase 16.1)

Revision ID: agent0009
Revises: agent0008

`agent0001` dựng bảng theo model HIỆN TẠI — DB dựng mới đã có cột, chỉ thêm khi thiếu.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "agent0009"
down_revision: Union[str, None] = "agent0008"
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


def _cols() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}


def upgrade() -> None:
    have = _cols()
    for name, kind, default in COLUMNS:
        if name not in have:
            op.add_column(TABLE, sa.Column(name, kind, nullable=False, server_default=sa.text(default)))


def downgrade() -> None:
    have = _cols()
    for name, _kind, _default in reversed(COLUMNS):
        if name in have:
            op.drop_column(TABLE, name)
