"""nhat ky cong MCP: ma chung tu + duong man cua luot ghi (bao-CR-696)

Revision ID: agent0017
Revises: agent0016

Cặp với `migrations/versions/mcplog03_ma_chung_tu_luot_ghi.py`. Chỉ thêm khi thiếu. Dòng cũ = rỗng.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "agent0017"
down_revision: Union[str, None] = "agent0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_agent_mcp_call"
COLUMNS = (("doc_code", 40), ("doc_url", 200))


def upgrade() -> None:
    have = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}
    for name, size in COLUMNS:
        if name not in have:
            op.add_column(TABLE, sa.Column(name, sa.String(size), nullable=False, server_default=""))


def downgrade() -> None:
    have = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}
    for name, _size in COLUMNS:
        if name in have:
            op.drop_column(TABLE, name)
