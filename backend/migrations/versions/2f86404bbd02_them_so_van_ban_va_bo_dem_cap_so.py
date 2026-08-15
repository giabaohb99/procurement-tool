"""them so van ban va bo dem cap so

Ba bang: tab_document_book (so), tab_document_book_member (nguoi quan ly / nguoi xem),
tab_number_sequence (bo dem cap so - moi so mot bo dem, reset theo nam).

Da bo phan alter_column ma autogenerate sinh them cho tab_comment_*, tab_ticket*:
do la drift NOT NULL co san cua cac bang khac, khong thuoc thay doi nay.

Revision ID: 2f86404bbd02
Revises: 5922e3767c9e
Create Date: 2026-08-14 07:10:37.349953
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '2f86404bbd02'
down_revision: Union[str, None] = '5922e3767c9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table('tab_document_book',
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('kind', sa.SmallInteger(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('company_id', sa.BigInteger(), nullable=False),
    sa.Column('department_id', sa.BigInteger(), nullable=False),
    sa.Column('number_prefix', sa.String(length=20), nullable=False),
    sa.Column('reset_yearly', sa.Boolean(), nullable=False),
    sa.Column('start_no', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('tab_document_book_member',
    sa.Column('book_id', sa.BigInteger(), nullable=False),
    sa.Column('employee_id', sa.BigInteger(), nullable=False),
    sa.Column('role', sa.SmallInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('book_id', 'employee_id', 'role', name='uq_book_member')
    )
    op.create_table('tab_number_sequence',
    sa.Column('scope_key', sa.String(length=150), nullable=False),
    sa.Column('year', sa.SmallInteger(), nullable=False),
    sa.Column('current_no', sa.Integer(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('scope_key')
    )

    # Truy vấn nóng: danh sách sổ lọc theo pháp nhân + loại sổ.
    op.create_index("ix_doc_book_company", "tab_document_book", ["company_id", "kind", "is_active"])
    # "Người này quản lý / xem được sổ nào" — chiều ngược của bảng thành viên.
    op.create_index("ix_doc_book_member_emp", "tab_document_book_member", ["employee_id", "role"])


def downgrade() -> None:
    op.drop_index("ix_doc_book_member_emp", table_name="tab_document_book_member")
    op.drop_index("ix_doc_book_company", table_name="tab_document_book")
    op.drop_table("tab_number_sequence")
    op.drop_table("tab_document_book_member")
    op.drop_table("tab_document_book")

