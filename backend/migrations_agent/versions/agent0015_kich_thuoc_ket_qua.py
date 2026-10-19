"""nhat ky cong MCP: so ky tu ket qua moi luot tools/call (ai-CR-228)

Revision ID: agent0015
Revises: agent0014

Cặp với `migrations/versions/mcplog02_kich_thuoc_ket_qua.py`. Chỉ thêm khi thiếu. Dòng cũ = 0 (không đo).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "agent0015"
down_revision: Union[str, None] = "agent0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_agent_mcp_call"


def upgrade() -> None:
    have = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}
    if "result_chars" not in have:
        op.add_column(TABLE, sa.Column("result_chars", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    have = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}
    if "result_chars" in have:
        op.drop_column(TABLE, "result_chars")
