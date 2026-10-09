"""duoc-CR-614: mẫu khởi tạo của khối Báo cáo thực hiện

`tab_exec_report.template` (SMALLINT, R2) — mẫu người dùng chọn lúc «Khởi tạo báo cáo
mẫu»: 1 = mẫu chung hồ sơ nhập khẩu (5 giai đoạn), 2 = tiến độ kế hoạch công việc nhập
khẩu (1 giai đoạn, 21 việc). Khối có sẵn nhận 1 — đúng mẫu chúng đã được đổ.

Revision ID: rpttpl01
Revises: grp04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "rpttpl01"
down_revision: Union[str, None] = "grp04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_exec_report",
                  sa.Column("template", sa.SmallInteger(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("tab_exec_report", "template")
