"""duoc-CR-660 (Đ-13c) — thêm cờ quyền `can_import` (Nhập file) vào tab_permission

Chỉ THÊM cột, mặc định 0: KHÔNG tự bật cho vai trò nào có sẵn trên DB (D-018 — seed không ghi đè
phân quyền người dùng đã chỉnh). Riêng vai trò `admin` được `ensure_admin_role` ép đủ quyền ở lần
khởi động kế tiếp. Vai trò khác muốn nhập CSV danh mục thì tick ô «Nhập» ở màn Phân quyền.

Revision ID: cr660imp01
Revises: aiplan01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "cr660imp01"
down_revision: Union[str, Sequence[str], None] = "aiplan01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_permission", sa.Column(
        "can_import", sa.Boolean(), nullable=False, server_default=sa.text("0")))


def downgrade() -> None:
    op.drop_column("tab_permission", "can_import")
