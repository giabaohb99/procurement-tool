"""agent hub: dang ky ban tin bat / tat trong chat (ai-CR-140)

Revision ID: agent0008
Revises: agent0007

`agent0001` dựng bảng theo model HIỆN TẠI — DB dựng mới đã có đủ, chỉ thêm khi thiếu.
"""
from typing import Sequence, Union

from alembic import op

import app.core.all_models  # noqa: F401
from app.core.base_model import Base

# revision identifiers, used by Alembic.
revision: str = "agent0008"
down_revision: Union[str, None] = "agent0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_agent_brief_sub"


def upgrade() -> None:
    Base.metadata.create_all(op.get_bind(), tables=[Base.metadata.tables[TABLE]], checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind(), tables=[Base.metadata.tables[TABLE]], checkfirst=True)
