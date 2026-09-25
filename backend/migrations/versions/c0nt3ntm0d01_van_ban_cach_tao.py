"""van_ban_cach_tao

Cột `tab_document.content_mode` — CÁCH TẠO văn bản (24/09/2026):
1 «Tạo và soạn thảo» · 2 «Tạo, không soạn thảo» (văn bản chỉ gồm tệp có sẵn).
Màn chi tiết bỏ tab «Tệp»; tab «Văn bản» là trình SOẠN THẢO hay trình XEM TỆP
tùy cột này. Trước đó giao diện ĐOÁN bằng "nội dung rỗng + có tệp", đoán nhầm
văn bản soạn thảo vừa tạo, chưa gõ chữ nào mà đã đính tệp.

Bước dữ liệu: văn bản CŨ điền theo đúng luật đoán đang chạy (bản đang dùng
rỗng nội dung VÀ có ít nhất một tệp gắn vào bản đó → 2), để không văn bản nào
đổi cách hiển thị so với hôm qua.

Revision ID: c0nt3ntm0d01
Revises: 32b55e9888f6
Create Date: 2026-09-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c0nt3ntm0d01"
down_revision: Union[str, None] = "32b55e9888f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tab_document",
        sa.Column("content_mode", sa.SmallInteger(), nullable=False, server_default="1"),
    )
    op.execute(
        """
        UPDATE tab_document d
        JOIN tab_document_version v ON v.id = d.current_version_id
        SET d.content_mode = 2
        WHERE TRIM(COALESCE(v.content_html, '')) = ''
          AND EXISTS (
            SELECT 1 FROM tab_file_link l
            WHERE l.entity = 'document_version' AND l.entity_id = v.id
          )
        """
    )


def downgrade() -> None:
    op.drop_column("tab_document", "content_mode")
