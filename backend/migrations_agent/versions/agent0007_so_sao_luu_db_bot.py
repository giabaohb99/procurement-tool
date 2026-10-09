"""agent hub: so sao luu DB cua dich vu AI (ai-CR-139)

Revision ID: agent0007
Revises: agent0006

`agent0001` dựng bảng theo model HIỆN TẠI — DB dựng mới đã có đủ, chỉ thêm khi thiếu.
"""
from typing import Sequence, Union

from alembic import op

import app.core.all_models  # noqa: F401
from app.core.base_model import Base

# revision identifiers, used by Alembic.
revision: str = "agent0007"
down_revision: Union[str, None] = "agent0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_agent_db_backup"


def upgrade() -> None:
    Base.metadata.create_all(op.get_bind(), tables=[Base.metadata.tables[TABLE]], checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind(), tables=[Base.metadata.tables[TABLE]], checkfirst=True)
