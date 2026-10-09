"""agent hub: nen hoi thoai — ban tom tat theo tung cuoc + dau cau tra loi rut tu cong cu (ai-CR-136)

Revision ID: agent0004
Revises: agent0003

`agent0001` dựng bảng theo model HIỆN TẠI — DB dựng mới đã có đủ, chỉ thêm phần còn thiếu.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import app.core.all_models  # noqa: F401
from app.core.base_model import Base

# revision identifiers, used by Alembic.
revision: str = "agent0004"
down_revision: Union[str, None] = "agent0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_agent_conv_summary"
FLAGS = ("tab_agent_message", "tab_assistant_message")


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for table in FLAGS:
        if "tool_used" not in {c["name"] for c in insp.get_columns(table)}:
            op.add_column(table, sa.Column("tool_used", sa.Boolean(), nullable=False, server_default=sa.false()))
    Base.metadata.create_all(bind, tables=[Base.metadata.tables[TABLE]], checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind, tables=[Base.metadata.tables[TABLE]], checkfirst=True)
    for table in FLAGS:
        if "tool_used" in {c["name"] for c in sa.inspect(bind).get_columns(table)}:
            op.drop_column(table, "tool_used")
