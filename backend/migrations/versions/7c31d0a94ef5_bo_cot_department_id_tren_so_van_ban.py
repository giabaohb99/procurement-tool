"""bo cot department_id tren so van ban

Quyen xem so cap cho NGUOI DICH DANH (tab_document_book_member), khong cap theo
phong ban: cap theo phong ban thi nguoi moi vao phong tu thay so, nguoi chuyen di
tu mat — hai hanh vi nguoc nhau ma nguoi mo so khong he chon.

Bang moi tao o migration truoc, chua co du lieu that nen bo cot luon thay vi de
lai mot cot chet khong ai doc.

Revision ID: 7c31d0a94ef5
Revises: 2f86404bbd02
Create Date: 2026-08-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "7c31d0a94ef5"
down_revision: Union[str, None] = "2f86404bbd02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Chỉ mục cũ có `department_id` ở giữa nên phải dựng lại, không sửa tại chỗ được.
    op.drop_index("ix_doc_book_company", table_name="tab_document_book")
    op.drop_column("tab_document_book", "department_id")
    op.create_index(
        "ix_doc_book_company", "tab_document_book", ["company_id", "kind", "is_active"]
    )


def downgrade() -> None:
    op.drop_index("ix_doc_book_company", table_name="tab_document_book")
    op.add_column(
        "tab_document_book",
        sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_doc_book_company", "tab_document_book", ["company_id", "kind", "is_active"]
    )
