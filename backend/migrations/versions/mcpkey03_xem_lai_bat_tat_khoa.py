"""khoa MCP: xem lai khoa (raw_view) + bat / tat tam (disabled_at) (ai-CR-221)

Revision ID: mcpkey03
Revises: mcpoauth01

Bảng của DỊCH VỤ AI (tiền tố `tab_agent_`): ở chế độ nhúng nằm chung DB ERP (migration này), ở chế độ tách nằm ở DB
`agent_hub` (cặp với `migrations_agent/versions/agent0014_xem_lai_bat_tat_khoa.py`). Chỉ thêm khi thiếu. Khóa cũ không có
`raw_view` → màn hiện «tạo lại để xem».
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "mcpkey03"
down_revision: Union[str, None] = "mcpoauth01"
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
