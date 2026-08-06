"""them bang lich su mua hang (snapshot dong DMH hoan thanh)

Revision ID: bd465aae44d0
Revises: 347765325c1b
Create Date: 2026-08-06 09:07:44.743304

Chỉ tạo bảng tab_purchase_history. Các thay đổi NOT NULL trên tab_comment_*/tab_ticket_*
mà autogenerate phát hiện đã được LOẠI BỎ — đó là drift có sẵn của DB local, không thuộc
phạm vi thay đổi này.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'bd465aae44d0'
down_revision: Union[str, None] = '347765325c1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_purchase_history',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        # Khóa & truy vấn
        sa.Column('po_item_id', sa.BigInteger(), nullable=False),
        sa.Column('po_id', sa.BigInteger(), nullable=False),
        sa.Column('po_code', sa.String(length=50), nullable=False),
        sa.Column('product_code', sa.String(length=50), nullable=False),
        sa.Column('supplier_code', sa.String(length=50), nullable=False),
        sa.Column('order_date', sa.String(length=10), nullable=False),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        # Hiển thị trên bảng
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('supplier_name', sa.String(length=255), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('unit', sa.String(length=25), nullable=False),
        sa.Column('qty_order', sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column('price', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('vat', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('completed_at', sa.String(length=10), nullable=False),
        # Phần "Thông tin chung" còn lại (chuỗi JSON)
        sa.Column('extra', sa.Text(), nullable=False),
        # AuditMixin
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('po_item_id'),
    )
    # Composite index phủ luôn truy vấn chỉ theo product_code / supplier_code (leftmost prefix)
    op.create_index('ix_ph_product_date', 'tab_purchase_history', ['product_code', 'order_date'], unique=False)
    op.create_index('ix_ph_supplier_date', 'tab_purchase_history', ['supplier_code', 'order_date'], unique=False)
    op.create_index(op.f('ix_tab_purchase_history_po_id'), 'tab_purchase_history', ['po_id'], unique=False)
    op.create_index(op.f('ix_tab_purchase_history_order_date'), 'tab_purchase_history', ['order_date'], unique=False)
    op.create_index(op.f('ix_tab_purchase_history_company_id'), 'tab_purchase_history', ['company_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_purchase_history_company_id'), table_name='tab_purchase_history')
    op.drop_index(op.f('ix_tab_purchase_history_order_date'), table_name='tab_purchase_history')
    op.drop_index(op.f('ix_tab_purchase_history_po_id'), table_name='tab_purchase_history')
    op.drop_index('ix_ph_supplier_date', table_name='tab_purchase_history')
    op.drop_index('ix_ph_product_date', table_name='tab_purchase_history')
    op.drop_table('tab_purchase_history')
