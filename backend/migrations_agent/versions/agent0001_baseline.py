"""agent hub: nen dau tien cua database rieng (ai-CR-119)

Revision ID: agent0001
Revises:

Tạo đúng các bảng của dịch vụ AI (app/core/agent_tables.py) theo model HIỆN TẠI — ngang với head `meet03` của alembic ERP.
Dời từ DB ERP: chép dữ liệu bằng scripts/agent_split/copy_agent_tables.sh rồi `alembic -c alembic_agent.ini stamp head`
(bảng đã có thì KHÔNG chạy upgrade này).
"""
from typing import Sequence, Union

from alembic import op

import app.core.all_models  # noqa: F401
from app.core.agent_tables import agent_tables
from app.core.base_model import Base

# revision identifiers, used by Alembic.
revision: str = "agent0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind, tables=agent_tables(Base.metadata), checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind, tables=agent_tables(Base.metadata), checkfirst=True)
