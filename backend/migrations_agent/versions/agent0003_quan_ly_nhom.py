"""agent hub: quan ly nhom tren web — loai nhom, ngung ghi, ban tom tat, nhat ky xem (ai-CR-123)

Revision ID: agent0003
Revises: agent0002

`agent0001` dựng bảng theo model HIỆN TẠI — DB dựng mới đã có đủ, chỉ thêm phần còn thiếu.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import app.core.all_models  # noqa: F401
from app.core.base_model import Base

# revision identifiers, used by Alembic.
revision: str = "agent0003"
down_revision: Union[str, None] = "agent0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_TABLES = ("tab_agent_group_summary", "tab_agent_group_view")


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("tab_agent_group")}
    if "category" not in cols:
        op.add_column("tab_agent_group", sa.Column("category", sa.SmallInteger(), nullable=False, server_default="0"))
    if "paused" not in cols:
        op.add_column("tab_agent_group", sa.Column("paused", sa.Boolean(), nullable=False, server_default=sa.false()))
    Base.metadata.create_all(bind, tables=[Base.metadata.tables[t] for t in NEW_TABLES], checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind, tables=[Base.metadata.tables[t] for t in NEW_TABLES], checkfirst=True)
    cols = {c["name"] for c in sa.inspect(bind).get_columns("tab_agent_group")}
    for c in ("paused", "category"):
        if c in cols:
            op.drop_column("tab_agent_group", c)
