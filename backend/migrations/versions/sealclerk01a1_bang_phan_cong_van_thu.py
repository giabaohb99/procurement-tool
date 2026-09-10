"""seal_clerk: bang phan cong van thu theo cong ty (tab_seal_clerk)

Revision ID: sealclerk01a1
Revises: 32e30ac28788
Create Date: 2026-09-09

Bảng phân công VĂN THƯ (Duyệt dấu) theo công ty. Mỗi dòng = một văn thư phụ trách
một công ty; `is_head=1` là VĂN THƯ TỔNG (phụ trách phiếu đa công ty). Đọc trực
tiếp trong `core/scoping.py` (phạm vi văn thư) và `seal_request/notify.py`.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "sealclerk01a1"
down_revision: Union[str, None] = "32e30ac28788"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_seal_clerk",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("employee_id", sa.BigInteger(), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("is_head", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_seal_clerk_employee_id", "tab_seal_clerk", ["employee_id"])
    op.create_index("ix_tab_seal_clerk_company_id", "tab_seal_clerk", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_tab_seal_clerk_company_id", table_name="tab_seal_clerk")
    op.drop_index("ix_tab_seal_clerk_employee_id", table_name="tab_seal_clerk")
    op.drop_table("tab_seal_clerk")
