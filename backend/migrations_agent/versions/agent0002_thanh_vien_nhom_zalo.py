"""agent hub: thanh vien nhom Zalo (tai khoan cong ty) — them cot members (ai-CR-122)

Revision ID: agent0002
Revises: agent0001

`agent0001` dựng bảng theo model HIỆN TẠI, nên DB dựng mới sau ngày này đã có cột — chỉ thêm khi còn thiếu.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "agent0002"
down_revision: Union[str, None] = "agent0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column() -> bool:
    cols = sa.inspect(op.get_bind()).get_columns("tab_agent_group")
    return any(c["name"] == "members" for c in cols)


def upgrade() -> None:
    if not _has_column():
        op.add_column("tab_agent_group", sa.Column("members", sa.JSON(), nullable=True))


def downgrade() -> None:
    if _has_column():
        op.drop_column("tab_agent_group", "members")
