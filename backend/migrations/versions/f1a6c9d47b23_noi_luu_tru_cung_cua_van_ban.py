"""Nơi lưu trữ cứng của văn bản

Bản giấy có chữ ký tươi nằm ở đâu — "Tủ A2 · Kệ 3 · Bìa 12". Ô chữ tự do chứ
không phải danh mục riêng: mỗi pháp nhân sắp kho một kiểu, ép vào một bảng danh
mục là đẻ thêm một màn khai báo mà không ai duy trì. Thứ giữ cho dữ liệu đỡ mỗi
người một kiểu là gợi ý lấy từ chính các giá trị đã nhập
(`GET /api/documents/storage-locations`).

Revision ID: f1a6c9d47b23
Revises: c66984bcd932
Create Date: 2026-08-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a6c9d47b23"
down_revision: Union[str, None] = "c66984bcd932"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tab_document",
        sa.Column("storage_location", sa.String(length=200), nullable=False,
                  server_default=""),
    )


def downgrade() -> None:
    op.drop_column("tab_document", "storage_location")
