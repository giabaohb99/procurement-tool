"""agent hub: so y dinh them con tro tin cau hoi de gan nhan tay (ai-CR-138, phase 13.6)

Revision ID: agent0006
Revises: agent0005

`agent0001` / `agent0005` dựng bảng theo model HIỆN TẠI — DB dựng mới đã có cột, chỉ thêm khi thiếu.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "agent0006"
down_revision: Union[str, None] = "agent0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_agent_intent"


def _cols() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}


def upgrade() -> None:
    if "message_id" not in _cols():
        op.add_column(TABLE, sa.Column("message_id", sa.BigInteger(), nullable=False, server_default="0"))


def downgrade() -> None:
    if "message_id" in _cols():
        op.drop_column(TABLE, "message_id")
