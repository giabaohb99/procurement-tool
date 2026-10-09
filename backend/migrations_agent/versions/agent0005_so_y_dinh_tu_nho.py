"""agent hub: so y dinh + diem tu rut ghi nho (ai-CR-137, phase 13.1-13.3)

Revision ID: agent0005
Revises: agent0004

`agent0001` dựng bảng theo model HIỆN TẠI — DB dựng mới đã có đủ, chỉ thêm phần còn thiếu.
"""
from typing import Sequence, Union

from alembic import op

import app.core.all_models  # noqa: F401
from app.core.base_model import Base

# revision identifiers, used by Alembic.
revision: str = "agent0005"
down_revision: Union[str, None] = "agent0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ("tab_agent_intent", "tab_agent_memory_candidate")


def upgrade() -> None:
    Base.metadata.create_all(op.get_bind(), tables=[Base.metadata.tables[t] for t in TABLES], checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind(), tables=[Base.metadata.tables[t] for t in TABLES], checkfirst=True)
