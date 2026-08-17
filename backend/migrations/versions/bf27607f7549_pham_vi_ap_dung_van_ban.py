"""pham vi ap dung van ban

F01–F04 — phạm vi áp dụng của văn bản: pháp nhân · phòng ban · cá nhân, mỗi dòng
là bao gồm hoặc loại trừ.

Ràng buộc CHECK là phần quan trọng nhất của migration này, không phải mấy cột.

Đã gỡ phần drift `tab_comment_*` / `tab_ticket*` mà autogenerate bắt kèm.

Revision ID: bf27607f7549
Create Date: 2026-08-17 03:55:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'bf27607f7549'
down_revision: Union[str, None] = '435ae7efb034'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_document_scope",
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        # 1 pháp nhân · 2 phòng ban · 3 cá nhân
        sa.Column("dim", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("company_id", sa.BigInteger(), nullable=True),
        sa.Column("department_id", sa.BigInteger(), nullable=True),
        sa.Column("employee_id", sa.BigInteger(), nullable=True),
        #  Tính LÚC ĐỌC chứ không bung sẵn thành nhiều dòng: bung sẵn thì công ty
        #  con mở sau này không được áp.
        sa.Column("include_children", sa.Boolean(), nullable=False, server_default="0"),
        # 1 bao gồm · 2 loại trừ
        sa.Column("mode", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        #  F03 — chọn phòng ban thì BẮT BUỘC kèm pháp nhân. Một phòng ban có mặt
        #  ở 13 pháp nhân; khai trơ trọi "phòng Kế toán" là văn bản lan sang cả
        #  13 công ty. Lỗi rất dễ mắc, rất khó phát hiện sau khi đã ban hành —
        #  nên chặn ở tầng dữ liệu, nơi không có đường vòng nào.
        sa.CheckConstraint("dim <> 2 OR company_id IS NOT NULL",
                           name="ck_document_scope_department_needs_company"),
        sa.UniqueConstraint("document_id", "dim", "company_id", "department_id",
                            "employee_id", "mode", name="uq_document_scope"),
    )
    op.create_index("ix_tab_document_scope_document_id", "tab_document_scope",
                    ["document_id"])
    op.create_index("ix_document_scope_company", "tab_document_scope",
                    ["company_id", "mode"])
    op.create_index("ix_document_scope_department", "tab_document_scope",
                    ["department_id", "mode"])
    op.create_index("ix_document_scope_employee", "tab_document_scope",
                    ["employee_id", "mode"])


def downgrade() -> None:
    op.drop_index("ix_document_scope_employee", table_name="tab_document_scope")
    op.drop_index("ix_document_scope_department", table_name="tab_document_scope")
    op.drop_index("ix_document_scope_company", table_name="tab_document_scope")
    op.drop_index("ix_tab_document_scope_document_id", table_name="tab_document_scope")
    op.drop_table("tab_document_scope")
