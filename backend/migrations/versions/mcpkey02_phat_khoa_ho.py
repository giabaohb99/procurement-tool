"""khoa MCP phat ho: issued_by, claimed_at, raw_sealed, batch_id (ai-CR-212, K4 doc/erp/21 §4.3 + §5.3)

Revision ID: mcpkey02
Revises: mcplog01

`tab_agent_mcp_key` là bảng của DỊCH VỤ AI: ở chế độ nhúng nằm chung DB ERP (migration này), ở chế độ tách nằm ở DB
`agent_hub` (cặp với `migrations_agent/versions/agent0012_phat_khoa_ho.py`). Chỉ thêm cột khi thiếu.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "mcpkey02"
down_revision: Union[str, None] = "mcplog01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_agent_mcp_key"
COLUMNS = (
    ("issued_by", lambda: sa.Column("issued_by", sa.BigInteger(), nullable=False, server_default="0")),
    ("claimed_at", lambda: sa.Column("claimed_at", sa.DateTime(), nullable=True)),
    ("raw_sealed", lambda: sa.Column("raw_sealed", sa.Text(), nullable=True)),
    ("batch_id", lambda: sa.Column("batch_id", sa.String(32), nullable=False, server_default="")),
)


def _cols() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}


def _indexes() -> set[str]:
    return {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(TABLE)}


def upgrade() -> None:
    have = _cols()
    for name, col in COLUMNS:
        if name not in have:
            op.add_column(TABLE, col())
    if "ix_tab_agent_mcp_key_batch_id" not in _indexes():
        op.create_index("ix_tab_agent_mcp_key_batch_id", TABLE, ["batch_id"])


def downgrade() -> None:
    if "ix_tab_agent_mcp_key_batch_id" in _indexes():
        op.drop_index("ix_tab_agent_mcp_key_batch_id", table_name=TABLE)
    have = _cols()
    for name, _col in reversed(COLUMNS):
        if name in have:
            op.drop_column(TABLE, name)
