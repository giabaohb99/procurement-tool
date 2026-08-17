"""quan he cha con giua cac van ban

Nhóm E — quan hệ cha–con (E01–E06) và quan hệ "trích từ" (E11):

- `tab_doc_type_link_rule` — quy tắc theo LOẠI: loại X có quan hệ Y tới loại Z,
  bắt buộc hay không, được mấy cái. Khoảng 15–25 dòng, sửa bằng giao diện.
- `tab_document_link` — quan hệ thật giữa hai văn bản.
- `tab_document.needs_review` — cờ *cần rà lại*, bật khi văn bản cha đổi. Hệ
  thống chỉ đánh dấu, không tự sửa nội dung con.

Đã gỡ phần drift `tab_comment_*` / `tab_ticket*` mà autogenerate bắt kèm.

Revision ID: 435ae7efb034
Revises: 30773e5cd878
Create Date: 2026-08-17 02:45:54.736391
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "435ae7efb034"
down_revision: Union[str, Sequence[str], None] = "30773e5cd878"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
    ]


def upgrade() -> None:
    op.create_table(
        "tab_doc_type_link_rule",
        sa.Column("source_type_id", sa.BigInteger(), nullable=False),
        #  1 thay thế · 2 sửa đổi · 3 bổ sung · 4 hướng dẫn · 5 kèm theo
        #  · 6 thuộc về · 7 căn cứ theo · 8 tham chiếu · 9 bãi bỏ · 10 trích từ
        sa.Column("relation", sa.SmallInteger(), nullable=False),
        #  NULL = loại nào cũng được.
        sa.Column("target_type_id", sa.BigInteger(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("min_count", sa.SmallInteger(), nullable=False, server_default="0"),
        #  0 = không giới hạn.
        sa.Column("max_count", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("on_parent_obsolete", sa.SmallInteger(), nullable=False, server_default="2"),
        sa.Column("on_parent_new_version", sa.SmallInteger(), nullable=False,
                  server_default="3"),
        sa.Column("inherit_code", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("inherit_secrecy", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("id"),
        #  Hai dòng cùng (nguồn × quan hệ × đích) sẽ mâu thuẫn nhau về "bắt buộc"
        #  và không biết tin dòng nào.
        sa.UniqueConstraint("source_type_id", "relation", "target_type_id",
                            name="uq_doc_type_link_rule"),
    )
    op.create_index("ix_link_rule_source", "tab_doc_type_link_rule",
                    ["source_type_id", "relation"])

    op.create_table(
        "tab_document_link",
        sa.Column("source_document_id", sa.BigInteger(), nullable=False),
        sa.Column("target_document_id", sa.BigInteger(), nullable=False),
        sa.Column("relation", sa.SmallInteger(), nullable=False),
        sa.Column("rule_id", sa.BigInteger(), nullable=True),
        #  CHỈ dùng cho quan hệ trích từ: bản trích tách từ phiên bản nào của gốc.
        sa.Column("source_version_id", sa.BigInteger(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=False, server_default=""),
        #  Hệ thống tự tạo — không màn hình nào, không hàm nào xóa được.
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="0"),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_document_id", "target_document_id", "relation",
                            name="uq_document_link"),
    )
    op.create_index("ix_document_link_source", "tab_document_link",
                    ["source_document_id", "relation"])
    op.create_index("ix_document_link_target", "tab_document_link",
                    ["target_document_id", "relation"])

    op.add_column(
        "tab_document",
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "tab_document",
        sa.Column("needs_review_note", sa.String(length=300), nullable=False,
                  server_default=""),
    )


def downgrade() -> None:
    op.drop_column("tab_document", "needs_review_note")
    op.drop_column("tab_document", "needs_review")
    op.drop_index("ix_document_link_target", table_name="tab_document_link")
    op.drop_index("ix_document_link_source", table_name="tab_document_link")
    op.drop_table("tab_document_link")
    op.drop_index("ix_link_rule_source", table_name="tab_doc_type_link_rule")
    op.drop_table("tab_doc_type_link_rule")
