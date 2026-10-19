"""gop hai nhanh migration: OAuth / khoa MCP (mcpkey03) + HDLD (lbvar01)

Revision ID: mcpmerge01
Revises: lbvar01, mcpkey03

Hai nhánh cùng mọc từ `mcpkey02` (prod đang đứng ở đó, 19/10/2026): duoc-CR-629 / 630 (`lbrct02` → `lbvar01`) và ai-CR-218/221
(`mcpoauth01` → `mcpkey03`). Migration gộp rỗng — không đổi bảng nào, chỉ để `alembic upgrade head` còn một đầu.
"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "mcpmerge01"
down_revision: Union[str, Sequence[str], None] = ("lbvar01", "mcpkey03")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
