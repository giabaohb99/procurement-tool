"""agent hub: nhat ky luot goi cong MCP + bang dem theo ngay (ai-CR-209)

Revision ID: agent0011
Revises: agent0010

Cặp với `migrations/versions/mcplog01_nhat_ky_cong_mcp.py` (DB ERP ở chế độ nhúng). `agent0001` dựng bảng theo model HIỆN
TẠI — DB dựng mới đã có hai bảng này, nên chỉ tạo khi thiếu.
"""
from typing import Sequence, Union

from alembic import op

import app.core.all_models  # noqa: F401
from app.core.base_model import Base

# revision identifiers, used by Alembic.
revision: str = "agent0011"
down_revision: Union[str, None] = "agent0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ("tab_agent_mcp_call", "tab_agent_mcp_call_daily")


def upgrade() -> None:
    Base.metadata.create_all(op.get_bind(), tables=[Base.metadata.tables[t] for t in TABLES], checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind(), tables=[Base.metadata.tables[t] for t in TABLES], checkfirst=True)
