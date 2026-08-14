"""them danh muc loai van ban va don vi gui nhan

Hai bang danh muc nen cua phan he Van thu (van-thu/04 muc 4.1 va 4.5).
Deu la danh muc dung chung moi phap nhan nen KHONG co cot company_id.

Da bo phan alter_column ma autogenerate sinh them cho tab_comment_*, tab_ticket*:
do la drift NOT NULL co san cua cac bang khac, khong thuoc thay doi nay.

Revision ID: 5922e3767c9e
Revises: 29639909b354
Create Date: 2026-08-14 06:35:53.728728
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '5922e3767c9e'
down_revision: Union[str, None] = '29639909b354'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table('tab_doc_type',
    sa.Column('code', sa.String(length=10), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('group_code', sa.String(length=1), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('id_scheme', sa.SmallInteger(), nullable=False),
    sa.Column('number_when', sa.SmallInteger(), nullable=False),
    sa.Column('default_secrecy', sa.SmallInteger(), nullable=False),
    sa.Column('is_confidential_type', sa.Boolean(), nullable=False),
    sa.Column('needs_approval', sa.Boolean(), nullable=False),
    sa.Column('needs_signature', sa.Boolean(), nullable=False),
    sa.Column('needs_decision', sa.Boolean(), nullable=False),
    sa.Column('needs_request', sa.Boolean(), nullable=False),
    sa.Column('review_cycle_months', sa.SmallInteger(), nullable=False),
    sa.Column('retention_months', sa.SmallInteger(), nullable=False),
    sa.Column('default_flow_id', sa.BigInteger(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('tab_external_party',
    sa.Column('code', sa.String(length=30), nullable=False),
    sa.Column('name', sa.String(length=300), nullable=False),
    sa.Column('kind', sa.SmallInteger(), nullable=False),
    sa.Column('contact_person', sa.String(length=200), nullable=False),
    sa.Column('phone', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=150), nullable=False),
    sa.Column('address', sa.Text(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )

    # Chỉ mục phục vụ màn danh mục: lọc theo nhóm + trạng thái, sắp theo sort_order.
    op.create_index("ix_doc_type_group", "tab_doc_type", ["group_code", "is_active"])
    op.create_index("ix_external_party_kind", "tab_external_party", ["kind", "is_active"])


def downgrade() -> None:
    op.drop_index("ix_external_party_kind", table_name="tab_external_party")
    op.drop_index("ix_doc_type_group", table_name="tab_doc_type")
    op.drop_table("tab_external_party")
    op.drop_table("tab_doc_type")

