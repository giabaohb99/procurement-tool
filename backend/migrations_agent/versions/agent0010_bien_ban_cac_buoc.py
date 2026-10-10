"""agent hub: bien ban hop ghi cac buoc da xong (ai-CR-162)

Revision ID: agent0010
Revises: agent0009

`agent0001` dựng bảng theo model HIỆN TẠI — DB dựng mới đã có cột, chỉ thêm khi thiếu.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "agent0010"
down_revision: Union[str, None] = "agent0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_agent_meeting"


def _cols() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}


def upgrade() -> None:
    if "steps" not in _cols():
        op.add_column(TABLE, sa.Column("steps", sa.JSON(), nullable=True))


def downgrade() -> None:
    if "steps" in _cols():
        op.drop_column(TABLE, "steps")
