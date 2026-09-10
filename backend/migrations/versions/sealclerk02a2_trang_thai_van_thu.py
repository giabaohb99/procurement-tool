"""seal_clerk: them cot trang thai (status) cho phan cong van thu

Revision ID: sealclerk02a2
Revises: sealclerk01a1
Create Date: 2026-09-09

Thêm cột `status` (SMALLINT, mặc định 1 = Đang hoạt động) cho `tab_seal_clerk`.
Tạm dừng (2) thì `core/scoping.py` và `seal_request/notify.py` BỎ QUA văn thư đó —
giữ phân công nhưng ngừng nhận phiếu đóng dấu cho tới khi bật lại.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "sealclerk02a2"
down_revision: Union[str, None] = "sealclerk01a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tab_seal_clerk",
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("tab_seal_clerk", "status")
