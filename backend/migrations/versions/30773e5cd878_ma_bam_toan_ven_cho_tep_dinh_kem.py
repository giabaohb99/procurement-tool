"""ma bam toan ven cho tep dinh kem

Mã băm nội dung tệp, tính lúc tải lên (`van-thu` C06). Dòng cũ để rỗng: tính lại
phải tải toàn bộ object từ storage về, tốn kém mà chưa ai cần đối chiếu tệp cũ.

`server_default` bắt buộc — `tab_file` đã có dữ liệu, thêm cột NOT NULL không
kèm mặc định thì MySQL ở chế độ nghiêm ngặt từ chối cả câu lệnh.

Bản autogenerate còn bắt kèm `alter_column` của `tab_comment_*` và `tab_ticket*`:
đó là chênh lệch có sẵn giữa model và DB, không phải do thay đổi này, đã gỡ.

Revision ID: 30773e5cd878
Revises: 85fd48d984db
Create Date: 2026-08-17 02:22:43.675187
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "30773e5cd878"
down_revision: Union[str, Sequence[str], None] = "85fd48d984db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tab_file",
        sa.Column("sha256", sa.String(length=64), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("tab_file", "sha256")
