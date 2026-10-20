"""so y dinh: so luot goi cong cu + so luot bi tu choi moi cau (ai-CR-230)

Revision ID: agent0016
Revises: agent0015

Cặp với `migrations/versions/aiusage01_hoat_dong_ai_cr230.py` (phần `tab_agent_intent`). Chỉ thêm khi thiếu. Dòng cũ = 0.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "agent0016"
down_revision: Union[str, None] = "agent0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_agent_intent"
COLS = ("tool_calls_n", "denied_n")


def upgrade() -> None:
    have = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}
    for col in COLS:
        if col not in have:
            op.add_column(TABLE, sa.Column(col, sa.SmallInteger(), nullable=False, server_default="0"))


def downgrade() -> None:
    have = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}
    for col in reversed(COLS):
        if col in have:
            op.drop_column(TABLE, col)
