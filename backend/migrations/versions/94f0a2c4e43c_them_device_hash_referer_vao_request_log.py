"""bao-CR-346: them device_hash + referer vao tab_request_log

⚠️ Tệp này ĐƯỢC VIẾT TAY. Bản `--autogenerate` sinh ra hơn năm mươi thao tác
`alter_column` trên hai chục bảng không liên quan — đó là phần lệch có sẵn giữa
model và CSDL (NOT NULL, chỉ mục đổi tên) tích lại từ trước, KHÔNG phải việc của
lần sửa này. Để nguyên là một migration đụng vào cả hệ để thêm hai cột.

Revision ID: 94f0a2c4e43c
Revises: f4d37c7600d0
Create Date: 2026-09-10
"""
import sqlalchemy as sa
from alembic import op

revision: str = "94f0a2c4e43c"
down_revision: str | None = "f4d37c7600d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    #  Dấu thiết bị đã chuẩn hóa — 8 byte, có chỉ mục vì câu hỏi cần trả lời là
    #  "trong phiên này có dòng nào ra dấu khác không", tức lọc theo cột này.
    op.add_column("tab_request_log",
                  sa.Column("device_hash", sa.BINARY(8), nullable=True))
    op.create_index("ix_tab_request_log_device_hash", "tab_request_log", ["device_hash"])
    #  `server_default=""` chứ không chỉ `default=""`: bảng có thể đã có dòng, mà
    #  `default` của SQLAlchemy chỉ chạy ở tầng Python lúc INSERT — dòng cũ sẽ
    #  mang NULL và mọi phép so chuỗi trên cột này lặng lẽ trượt.
    op.add_column("tab_request_log",
                  sa.Column("referer", sa.String(300), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("tab_request_log", "referer")
    op.drop_index("ix_tab_request_log_device_hash", table_name="tab_request_log")
    op.drop_column("tab_request_log", "device_hash")
