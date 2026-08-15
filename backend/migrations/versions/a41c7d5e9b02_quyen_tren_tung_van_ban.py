"""quyen tren tung van ban (chia se / cam dich danh)

Revision ID: a41c7d5e9b02
Revises: 32f20b5057fc
Create Date: 2026-08-14 09:05:00.000000

Lớp quyền thứ ba, đứng cạnh vai trò và phạm vi chứ không thay thế lớp nào —
xem `app/modules/document/access_model.py` để biết vì sao cần và ba lớp khác
nhau chỗ nào.

Không đặt UNIQUE cho "một dòng đang sống mỗi (văn bản × đối tượng × chiều tác
động)": `revoked_at IS NULL` thì UNIQUE không chặn được (nhiều NULL vẫn hợp lệ).
Chống trùng làm ở `access_service.grant()`.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a41c7d5e9b02'
down_revision: Union[str, None] = '32f20b5057fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_document_access",
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        # 1 người (id NHÂN SỰ) · 2 phòng ban · 3 pháp nhân · 4 vai trò.
        sa.Column("subject_kind", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("subject_id", sa.BigInteger(), nullable=False),
        # 1 cho phép · 2 cấm. CẤM thắng CHO PHÉP và thắng cả phạm vi vai trò.
        sa.Column("effect", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("can_read", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("can_write", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("can_delete", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("valid_from", sa.Date(), nullable=True),
        # Trống = không hạn.
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("reason", sa.String(500), nullable=False, server_default=""),
        # Thu hồi = ĐÁNH DẤU, dòng ở lại bảng (G19, G20).
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("revoke_reason", sa.String(500), nullable=False, server_default=""),

        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Hai chiều tra: "văn bản này đang chia cho ai" và "người này được thấy
    # thêm những văn bản nào" — câu thứ hai chạy trên MỌI lần mở danh sách.
    op.create_index("ix_document_access_doc", "tab_document_access",
                    ["document_id", "effect"])
    op.create_index("ix_document_access_subject", "tab_document_access",
                    ["subject_kind", "subject_id"])


def downgrade() -> None:
    op.drop_table("tab_document_access")
