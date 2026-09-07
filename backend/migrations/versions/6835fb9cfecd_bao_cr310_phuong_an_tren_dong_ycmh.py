"""bao_cr310_phuong_an_tren_dong_ycmh

Bảng PHƯƠNG ÁN gắn vào từng dòng Yêu cầu mua hàng (NSTM đề xuất NCC + giá ngay
trên YCMH, không phải đi vòng qua Yêu cầu báo giá). Chỉ TẠO BẢNG MỚI — bản
autogenerate còn bắt thêm cả loạt `alter_column`/`drop_index` của những bảng
không liên quan (assistant, ticket, vehicle, survey_supplier_line...) do model
và DB đã lệch từ trước; đã bỏ hết, đụng vào là sửa nhầm phạm vi của CR khác.

Revision ID: 6835fb9cfecd
Revises: 7b479d6dd387
Create Date: 2026-09-07 09:07:33.273558
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6835fb9cfecd'
down_revision: Union[str, None] = '7b479d6dd387'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = 'tab_purchase_request_item_option'


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column('pr_item_id', sa.BigInteger(), nullable=False),
        sa.Column('source', sa.SmallInteger(), nullable=False),
        sa.Column('product_survey_line_id', sa.BigInteger(), nullable=False),
        sa.Column('public_id', sa.Integer(), nullable=False),
        sa.Column('display_label', sa.String(length=50), nullable=False),
        sa.Column('is_chosen', sa.Boolean(), nullable=False),
        sa.Column('chosen_by', sa.BigInteger(), nullable=False),
        sa.Column('snap_product_name', sa.String(length=255), nullable=False),
        sa.Column('snap_spec', sa.Text(), nullable=False),
        sa.Column('snap_origin', sa.String(length=100), nullable=False),
        sa.Column('snap_quote_unit', sa.String(length=25), nullable=False),
        sa.Column('snap_moq', sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column('snap_price_by_volume', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('snap_volume_range', sa.String(length=100), nullable=False),
        sa.Column('snap_vat', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('snap_delivery_time', sa.String(length=100), nullable=False),
        sa.Column('snap_delivery_place', sa.String(length=255), nullable=False),
        sa.Column('snap_shipping_cost', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('snap_sample_ready', sa.Boolean(), nullable=False),
        sa.Column('snap_lab_result', sa.String(length=20), nullable=False),
        sa.Column('snap_internal_code', sa.String(length=50), nullable=False),
        sa.Column('supplier_code', sa.String(length=50), nullable=False),
        sa.Column('supplier_name', sa.String(length=255), nullable=False),
        sa.Column('supplier_survey_id', sa.BigInteger(), nullable=False),
        sa.Column('nstm_note', sa.Text(), nullable=False),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f(f'ix_{TABLE}_is_chosen'), TABLE, ['is_chosen'], unique=False)
    op.create_index(op.f(f'ix_{TABLE}_pr_item_id'), TABLE, ['pr_item_id'], unique=False)
    op.create_index(op.f(f'ix_{TABLE}_product_survey_line_id'), TABLE, ['product_survey_line_id'], unique=False)
    op.create_index(op.f(f'ix_{TABLE}_supplier_code'), TABLE, ['supplier_code'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f(f'ix_{TABLE}_supplier_code'), table_name=TABLE)
    op.drop_index(op.f(f'ix_{TABLE}_product_survey_line_id'), table_name=TABLE)
    op.drop_index(op.f(f'ix_{TABLE}_pr_item_id'), table_name=TABLE)
    op.drop_index(op.f(f'ix_{TABLE}_is_chosen'), table_name=TABLE)
    op.drop_table(TABLE)
